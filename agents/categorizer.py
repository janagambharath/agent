import openai
import os
from config import Config

class AICategorizer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.categories = ["Admit Card", "Job Notification", "Result", "Not Relevant"]
    
    def categorize(self, trend_text):
        """Categorize trend using AI (GPT-1 Agent)"""
        try:
            prompt = self._build_categorization_prompt(trend_text)
            
            response = self.client.chat.completions.create(
                model=Config.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            category = response.choices[0].message.content.strip()
            return self._validate_category(category)
            
        except Exception as e:
            print(f"Categorization error: {e}")
            return "Not Relevant"
    
    def _build_categorization_prompt(self, trend_text):
        """Build the categorization prompt"""
        return f"""
        You are an AI content categorizer for job-related trends. 
        Categorize this trend into exactly one of: [Admit Card, Job Notification, Result, Not Relevant]
        
        DEFINITIONS:
        - Admit Card: Hall tickets, admit cards, exam dates, download links, hall ticket release
        - Job Notification: New job vacancies, recruitment notifications, application forms, vacancy announcements
        - Result: Exam results, merit lists, scorecards, final results, selection lists
        - Not Relevant: Anything not related to government jobs, exams, or recruitment
        
        TREND TO CATEGORIZE: "{trend_text}"
        
        IMPORTANT: Return ONLY the category name. No explanations, no additional text.
        """
    
    def _validate_category(self, category):
        """Validate and clean the category"""
        category = category.strip()
        # Handle cases where AI might add explanations
        if "Admit Card" in category:
            return "Admit Card"
        elif "Job Notification" in category:
            return "Job Notification"
        elif "Result" in category:
            return "Result"
        else:
            return "Not Relevant"
