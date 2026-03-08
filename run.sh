#!/bin/bash

echo "🎀 Starting LuxeWigs NG..."

# Use the python from venv directly
VENV_PYTHON="/data/data/com.termux/files/home/wig-store/venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at $VENV_PYTHON"
    echo "Please run: ./install.sh"
    exit 1
fi

echo "✅ Using Python from virtual environment"
echo "🚀 Launching server on http://localhost:5000"
echo ""

# Run with venv python
$VENV_PYTHON app.py
