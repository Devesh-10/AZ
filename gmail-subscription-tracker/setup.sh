#!/bin/bash
# Setup script for Gmail Subscription Tracker

set -e

cd "$(dirname "$0")"

echo "=== Gmail Subscription Tracker Setup ==="
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "=== Setup complete! ==="
echo ""
echo "BEFORE RUNNING: You need a credentials.json file from Google Cloud."
echo ""
echo "Quick steps:"
echo "  1. Go to https://console.cloud.google.com/"
echo "  2. Create a new project (or select existing)"
echo "  3. Enable the Gmail API:"
echo "     - APIs & Services > Library > search 'Gmail API' > Enable"
echo "  4. Create OAuth credentials:"
echo "     - APIs & Services > Credentials > Create Credentials > OAuth Client ID"
echo "     - Application type: Desktop app"
echo "     - Download the JSON file"
echo "  5. Rename it to 'credentials.json' and place it in this folder"
echo ""
echo "Then run:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
