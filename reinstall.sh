#!/bin/bash

echo "🧹 Cleaning up..."
rm -rf venv
rm -rf __pycache__
rm -rf static/uploads/*
rm -f instance/*.db

echo "🐍 Creating fresh virtual environment..."
python -m venv venv

echo "⬇️ Installing dependencies (without Pillow)..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install packages one by one to catch errors
echo "Installing Flask..."
pip install Flask==3.0.0

echo "Installing Flask-SQLAlchemy..."
pip install Flask-SQLAlchemy==3.1.1

echo "Installing Flask-Login..."
pip install Flask-Login==0.6.3

echo "Installing Flask-WTF..."
pip install Flask-WTF==1.2.1

echo "Installing Flask-Mail..."
pip install Flask-Mail==0.9.1

echo "Installing Flask-Migrate..."
pip install Flask-Migrate==4.0.5

echo "Installing Werkzeug..."
pip install Werkzeug==3.0.1

echo "Installing WTForms..."
pip install WTForms==3.1.1

echo "Installing python-dotenv..."
pip install python-dotenv==1.0.0

echo "Installing requests..."
pip install requests==2.31.0

echo "Installing qrcode..."
pip install qrcode==7.4.2

echo "🗄️ Initializing database..."
python -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('✅ Database created!')
"

echo ""
echo "✅ Installation complete!"
echo "🚀 Run: ./start.sh"
