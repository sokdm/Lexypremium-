import os
import base64
from io import BytesIO
from datetime import datetime
from flask import current_app

# Try to import qrcode, handle if not available
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

def save_image(file, filename_prefix=''):
    """Save uploaded image - basic version without Pillow optimization"""
    if not file or not file.filename:
        return None
    
    # Generate filename
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        ext = 'jpg'
    
    filename = f"{filename_prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure directory exists
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Save file directly without processing
    file.save(filepath)
    
    return filename

def generate_qr_code(data):
    """Generate QR code for payment"""
    if not QRCODE_AVAILABLE:
        # Return placeholder if qrcode not installed
        return ""
    
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"QR generation error: {e}")
        return ""

def format_currency(amount):
    """Format amount as Nigerian Naira"""
    try:
        return f"₦{float(amount):,.0f}"
    except:
        return f"₦{amount}"
