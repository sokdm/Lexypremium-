import os
import base64
from io import BytesIO
from werkzeug.utils import secure_filename

def save_image(file, upload_folder='static/uploads'):
    """Save uploaded image and return filename"""
    if not file or file.filename == '':
        return None
    
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    import time
    filename = f"{name}_{int(time.time())}{ext}"
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filename

def format_currency(amount):
    """Format amount as Nigerian Naira"""
    if amount is None:
        return "₦0.00"
    return f"₦{amount:,.2f}"

def generate_qr_code(data):
    """Generate QR code - DISABLED"""
    return ""
