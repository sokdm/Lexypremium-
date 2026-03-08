#!/bin/bash

echo "🎀 LuxeWigs NG - Premium Wig Store with Monnify Integration"
echo "==========================================================="
echo ""

# Update packages
echo "📦 Updating packages..."
pkg update -y && pkg upgrade -y

# Install required packages
echo "🔧 Installing Python and dependencies..."
pkg install python python-pip git -y

# Create virtual environment
echo "🌟 Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install Python packages
echo "⬇️ Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p static/uploads
mkdir -p instance

# Initialize database
echo "🗄️ Initializing database..."
python -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('✅ Database created successfully!')
"

echo ""
echo "✅ Installation Complete!"
echo ""
echo "🚀 IMPORTANT NEXT STEPS:"
echo ""
echo "1. Get your Monnify Contract Code:"
echo "   python monnify_setup.py"
echo ""
echo "2. Update config.py with your contract code:"
echo "   MONNIFY_CONTRACT_CODE = 'YOUR_CONTRACT_CODE_HERE'"
echo ""
echo "3. To start the application:"
echo "   ./start.sh"
echo ""
echo "🌐 The website will be available at:"
echo "   http://localhost:5000"
echo ""
echo "🔗 Webhook endpoint for Monnify:"
echo "   http://YOUR_DOMAIN/webhook/monnify"
echo "   (Configure this in your Monnify dashboard)"
echo ""
echo "👤 Admin Login:"
echo "   Email: sokwilliams41@gmail.com"
echo "   Password: Admin54321"
echo ""
