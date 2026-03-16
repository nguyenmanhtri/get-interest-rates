---
name: get-interest-rates
description: >
  Get Vietnamese home loan interest rates by running a Python script. Use this skill whenever the user
  asks about home loan or mortgage interest rates in Vietnam. Trigger on keywords like: interest rate(s),
  lãi suất, lãi suất vay mua nhà, lãi suất ngân hàng, vay mua nhà.
---

# get-interest-rates

## Setup

Run the setup script to ensure dependencies are installed. This only
installs on the first run; subsequent runs are instant.

Note: `<skill-path>` is the absolute path to this skill's directory as resolved by the OpenClaw skill runner at invocation time.

```bash
chmod +x <skill-path>/scripts/setup.sh
bash <skill-path>/scripts/setup.sh
```

## Running

Activate the virtual environment and run the script:

```bash
source ~/.local/share/get-interest-rates-skill-venv/bin/activate
python <skill-path>/scripts/main.py
deactivate
```

## What it does

The script fetches Vietnamese home loan interest rates from topi.vn and outputs a JSON file
with rates categorized by bank type (state-owned banks, domestic banks, foreign banks).
