import os
from datetime import timedelta

class Config:
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///wigstore.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Monnify API Configuration
    MONNIFY_API_KEY = os.environ.get('MONNIFY_API_KEY')
    MONNIFY_SECRET_KEY = os.environ.get('MONNIFY_SECRET_KEY')
    MONNIFY_BASE_URL = os.environ.get('MONNIFY_BASE_URL') or 'https://api.monnify.com'
    MONNIFY_CONTRACT_CODE = os.environ.get('MONNIFY_CONTRACT_CODE')
    
    # WhatsApp settings
    WHATSAPP_PHONE_NUMBER = os.environ.get('WHATSAPP_PHONE_NUMBER') or '+2348108332873'
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
