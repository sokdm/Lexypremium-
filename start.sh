#!/bin/bash

echo "🎀 Starting LuxeWigs NG..."

# Check venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: ./reinstall.sh"
    exit 1
fi

# Activate and run
source venv/bin/activate

echo "✅ Virtual environment ready"
echo "🌐 Server: http://localhost:5000"
echo ""

python app.py
