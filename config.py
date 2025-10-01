import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys with validation
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # AI Model Settings
    AI_MODEL = "gpt-3.5-turbo"
    MAX_TOKENS = 800
    TEMPERATURE = 0.7
    
    # Flask Settings
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Data Storage
    CSV_FILE = "job_trends_data.csv"
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        errors = []
        
        if not Config.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set in environment variables")
        
        if len(Config.SECRET_KEY) < 16:
            errors.append("SECRET_KEY should be at least 16 characters for production")
        
        return errors
    
    @staticmethod
    def is_production():
        """Check if running in production"""
        return os.getenv('FLASK_ENV', 'development') == 'production'
