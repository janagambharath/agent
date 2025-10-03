import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys - FIXED FOR OPENROUTER
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENAI_API_KEY = OPENROUTER_API_KEY  # Alias for compatibility
    
    # Google Sheets Configuration
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # OpenRouter + DeepSeek R1 Settings
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    AI_MODEL = "deepseek/deepseek-r1:free"  # DeepSeek R1 Free Model
    
    # Model Parameters
    MAX_TOKENS = 1000  # Increased for DeepSeek R1
    TEMPERATURE = 0.7
    
    # Flask Settings
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Data Storage
    CSV_FILE = "job_trends_data.csv"
    
    # App Metadata for OpenRouter
    APP_NAME = "JobYaari AI Agent"
    APP_URL = "https://jobyaari.com"
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        errors = []
        warnings = []
        
        if not Config.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is not set in environment variables")
        
        if not Config.GOOGLE_SHEET_ID:
            warnings.append("GOOGLE_SHEET_ID is not set - using CSV fallback only")
        
        if not os.path.exists(Config.GOOGLE_CREDENTIALS_FILE):
            warnings.append(f"Google credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
        
        if len(Config.SECRET_KEY) < 16:
            warnings.append("SECRET_KEY should be at least 16 characters for production")
        
        return errors, warnings
    
    @staticmethod
    def is_production():
        """Check if running in production"""
        return os.getenv('FLASK_ENV', 'development') == 'production'
