#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "Setting up Node.js dependencies..."
npm install

echo "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "Setup complete! You can run python scripts using .venv/bin/python or source .venv/bin/activate"
