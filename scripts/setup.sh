#!/bin/bash
set -e

VENV_DIR="$HOME/.local/share/get-interest-rates-skill-venv"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# If the venv already exists and has a working Python, skip setup.
if [ -d "$VENV_DIR" ] && "$VENV_DIR/bin/python" -c "pass" 2>/dev/null; then
    exit 0
fi

echo "First run -- setting up environment..."
python -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
echo "Setup complete."
