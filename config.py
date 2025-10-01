import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # AI Model Settings
    AI_MODEL = "gpt-3.5-turbo"
    MAX_TOKENS = 800
    TEMPERATURE = 0.7
