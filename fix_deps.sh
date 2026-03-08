#!/bin/bash

echo "🔧 Fixing dependencies..."

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

echo "✅ Dependencies fixed!"
echo "Now run: ./start.sh"
