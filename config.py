import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'cp_secret_key_hackathon_demo_2026')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "instance", "campuspulse.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMIN_VERIFICATION_KEY = os.getenv('ADMIN_VERIFICATION_KEY', 'CP_ADMIN_2026_SECURE')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')
    
    QR_FOLDER = os.path.join(BASE_DIR, 'generated', 'qr')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    
    # Institution Info
    INSTITUTION_NAME = "Greenfield Institute of Technology"
