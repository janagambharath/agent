import openai
import os
from config import Config
import re

class AICategorizer:
    """GPT-1 Agent: Categorizes job trends using DeepSeek R1"""
    
    def __init__(self):
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not configured in .env file")
        
        self.client = openai.OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.categories = ["Admit Card", "Job Notification", "Result", "Not Relevant"]
        print(f"✅ Categorizer initialized with model: {Config.AI_MODEL}")
    
    def categorize(self, trend_text):
        """Categorize trend using AI (GPT-1 Agent)"""
        try:
            prompt = self._build_categorization_prompt(trend_text)
            
            response = self.client.chat.completions.create(
                model=Config.AI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1,
                extra_headers={
                    "HTTP-Referer": Config.APP_URL,
                    "X-Title": Config.APP_NAME
                }
            )
            
            category = response.choices[0].message.content.strip()
            
            # Clean up DeepSeek's thinking process if present
            category = self._clean_deepseek_response(category)
            
            return self._validate_category(category)
            
        except Exception as e:
            print(f"❌ Categorization error: {e}")
            return "Not Relevant"
    
    def _build_categorization_prompt(self, trend_text):
        """Build the categorization prompt - Optimized for DeepSeek R1"""
        return f"""You are a job trend categorizer. Categorize this trend into EXACTLY ONE category.

Categories:
- Admit Card: Hall tickets, exam dates, admit card downloads
- Job Notification: Job vacancies, recruitment, hiring announcements  
- Result: Exam results, merit lists, selection lists
- Not Relevant: Anything else

Trend: "{trend_text}"

Return ONLY the category name, nothing else."""
    
    def _clean_deepseek_response(self, response):
        """Clean DeepSeek R1's thinking process from response"""
        # DeepSeek R1 sometimes includes <think>...</think> tags
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = response.strip()
        
        # Extract just the category if there's extra text
        for category in self.categories:
            if category.lower() in response.lower():
                return category
        
        return response
    
    def _validate_category(self, category):
        """Validate and clean the category"""
        category = category.strip()
        
        # Direct match
        if category in self.categories:
            return category
        
        # Fuzzy match
        category_lower = category.lower()
        if "admit" in category_lower or "hall ticket" in category_lower:
            return "Admit Card"
        elif "job" in category_lower or "notification" in category_lower or "vacancy" in category_lower or "recruitment" in category_lower:
            return "Job Notification"
        elif "result" in category_lower or "merit" in category_lower:
            return "Result"
        else:
            return "Not Relevant"
    
    def batch_categorize(self, trends_list):
        """Categorize multiple trends at once"""
        results = []
        for trend in trends_list:
            category = self.categorize(trend)
            results.append({
                'trend': trend,
                'category': category
            })
        return results
