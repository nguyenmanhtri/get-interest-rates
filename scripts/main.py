"""Scrape home loan interest rates from topi.vn."""

import json
import re
import sys
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

URL = "https://topi.vn/lai-suat-vay-mua-nha.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
}

_PI5_DIR = Path("/home/frank/.openclaw/workspace/interest_rates")
OUTPUT_DIR = _PI5_DIR if _PI5_DIR.exists() else Path(__file__).parent / "outputs"


class Bank(StrEnum):
    # State-owned banks
    AGRIBANK = "agribank"
    BIDV = "bidv"
    VIETCOMBANK = "vietcombank"
    VIETINBANK = "vietinbank"
    # Domestic banks
    ABBANK = "abbank"
    ACB = "acb"
    BVBANK = "bvbank"
    VCBNEO = "vcbneo"
    VIKKI_BANK = "vikki bank (đông á)"
    EXIMBANK = "eximbank"
    GPBANK = "gpbank"
    HDBANK = "hdbank"
    KIEN_LONG = "kiên long"
    LPBANK = "lpbank"
    MB_BANK = "mb bank"
    MSB = "msb"
    NAM_A_BANK = "nam á bank"
    NCB = "ncb"
    OCB = "ocb"
    MBV_OCEANBANK = "mbv (oceanbank)"
    PGBANK = "pgbank"
    PUBLIC_BANK = "publicbank"
    PVCOMBANK = "pvcombank"
    SACOMBANK = "sacombank"
    SAIGONBANK = "saigonbank"
    SCB = "scb"
    SEABANK = "seabank"
    SHB = "shb"
    TECHCOMBANK = "techcombank"
    TPBANK = "tpbank"
    VIB = "vib"
    VIETABANK = "vietabank"
    VIETBANK = "vietbank"
    VPBANK = "vpbank"
    # Foreign banks
    HONG_LEONG = "hong leong"
    HSBC = "hsbc"
    INDOVINA = "indovina"
    VRB = "vrb"
    SHINHAN_BANK = "shinhan bank"
    WOORI_BANK = "woori bank"


def fetch_html() -> str:
    """Fetch page HTML using streaming to avoid read timeouts on large pages."""
    last_exc: Exception | None = None
    for attempt in range(1, 6):
        try:
            chunks: list[bytes] = []
            with httpx.Client(
                follow_redirects=True,
                timeout=httpx.Timeout(60.0, connect=30.0),
                headers=HEADERS,
            ) as client:
                with client.stream("GET", URL) as response:
                    response.raise_for_status()
                    for chunk in response.iter_bytes():
                        chunks.append(chunk)
            return b"".join(chunks).decode("utf-8", errors="replace")
        except httpx.TimeoutException as exc:
            last_exc = exc
            print(f"Attempt {attempt}/5 timed out, retrying...", file=sys.stderr)
    raise last_exc  # type: ignore[misc]  # always set after 5 attempts


def parse_rate_table(table) -> list[dict]:
    """Parse a bank interest rate comparison table into a list of dicts."""
    rows = table.find_all("tr")
    if not rows:
        return []

    headers = [th.get_text(" ", strip=True) for th in rows[0].find_all(["th", "td"])]
    results = []
    for row in rows[1:]:
        cells = [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) == len(headers):
            results.append(dict(zip(headers, cells)))
    return results


def parse_state_bank_section(soup) -> list[dict]:
    """Parse the state-owned bank section.

    Each bank in this section has an h3 heading followed by a 2-column key-value
    table. Extract the bank name from the heading and pivot the table into a dict.
    """
    # Find the h2 that introduces the state bank section
    state_h2 = None
    for h2 in soup.find_all("h2"):
        if "ngân hàng nhà nước" in h2.get_text().lower():
            state_h2 = h2
            break
    if state_h2 is None:
        return []

    # Walk siblings until the next h2, collecting h3+table pairs
    results = []
    current_bank_name: str | None = None
    for sibling in state_h2.find_next_siblings():
        if sibling.name == "h2":
            break
        if sibling.name == "h3":
            heading = sibling.get_text(" ", strip=True)
            # Extract short bank name: the word(s) right after "tại [ngân hàng ]"
            m = re.search(r"tại (?:ngân hàng )?(\S+)", heading.lower())
            current_bank_name = m.group(1) if m else heading
        elif current_bank_name:
            # Tables may be direct siblings or wrapped in a div
            table = sibling if sibling.name == "table" else sibling.find("table")
            if table:
                row_dict: dict[str, str] = {"ngân hàng": current_bank_name}
                for tr in table.find_all("tr"):
                    cells = tr.find_all(["td", "th"])
                    if len(cells) == 2:
                        key = cells[0].get_text(" ", strip=True)
                        val = cells[1].get_text(" ", strip=True)
                        row_dict[key] = val
                results.append(row_dict)
                current_bank_name = None  # reset; each bank has one table
    return results


def scrape() -> dict:
    fetched_at = datetime.now(timezone.utc).isoformat()
    html = fetch_html()
    soup = BeautifulSoup(html, "html.parser")

    # Comparison tables: first cell of first row is "Ngân hàng"
    def is_comparison_table(table) -> bool:
        first_row = table.find("tr")
        if not first_row:
            return False
        first_cell = first_row.find(["th", "td"])
        return first_cell is not None and first_cell.get_text(strip=True).lower() == "ngân hàng"

    rate_tables = [t for t in soup.find_all("table") if is_comparison_table(t)]

    state_banks = parse_state_bank_section(soup)
    domestic_banks = parse_rate_table(rate_tables[0]) if len(rate_tables) > 0 else []
    foreign_banks = parse_rate_table(rate_tables[1]) if len(rate_tables) > 1 else []

    return {
        "source": URL,
        "fetched_at": fetched_at,
        "state_banks": state_banks,
        "domestic_banks": domestic_banks,
        "foreign_banks": foreign_banks,
    }


def save_output(data: dict) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    date_str = data["fetched_at"][:10]
    filename = OUTPUT_DIR / f"interest-rates-{date_str}.json"
    filename.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return filename


if __name__ == "__main__":
    print("Fetching interest rates from topi.vn...", file=sys.stderr)
    data = scrape()

    out_path = save_output(data)
    print(f"Saved to {out_path}", file=sys.stderr)
