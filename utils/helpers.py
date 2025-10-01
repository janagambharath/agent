import re
import json
from datetime import datetime

def validate_trend_text(text):
    """Validate and clean trend text"""
    if not text or len(text.strip()) < 5:
        return False
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Check if it contains at least some meaningful content
    if len(text) < 10:
        return False
    
    return text

def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def extract_hashtags(text):
    """Extract hashtags from text"""
    return re.findall(r'#\w+', text)

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def save_to_json(data, filename):
    """Save data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

def load_from_json(filename):
    """Load data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None
