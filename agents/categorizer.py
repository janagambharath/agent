import openai
import os
from config import Config
import re
import time

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
        """Categorize trend using AI (GPT-1 Agent) with retry logic"""
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
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
                
                validated_category = self._validate_category(category)
                
                # Success!
                return validated_category
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2s, 4s, 8s
                        wait_time = base_delay * (2 ** attempt)
                        print(f"   ⏳ Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ Rate limit exceeded after {max_retries} attempts")
                        print(f"   💡 Try again in 30 seconds or use fallback categorization")
                        # Use fallback categorization based on keywords
                        return self._fallback_categorize(trend_text)
                else:
                    print(f"   ❌ Categorization error: {e}")
                    return self._fallback_categorize(trend_text)
        
        # If all retries failed
        return self._fallback_categorize(trend_text)
    
    def _fallback_categorize(self, trend_text):
        """Fallback categorization using keyword matching when API fails"""
        trend_lower = trend_text.lower()
        
        # Check for Admit Card keywords
        admit_keywords = ['admit card', 'hall ticket', 'exam date', 'download link']
        if any(keyword in trend_lower for keyword in admit_keywords):
            print(f"   🔄 Fallback: Categorized as 'Admit Card' (keyword match)")
            return "Admit Card"
        
        # Check for Job Notification keywords
        job_keywords = ['recruitment', 'notification', 'vacancy', 'hiring', 'posts announced', 'apply online']
        if any(keyword in trend_lower for keyword in job_keywords):
            print(f"   🔄 Fallback: Categorized as 'Job Notification' (keyword match)")
            return "Job Notification"
        
        # Check for Result keywords
        result_keywords = ['result', 'merit list', 'selection list', 'scorecard', 'declared']
        if any(keyword in trend_lower for keyword in result_keywords):
            print(f"   🔄 Fallback: Categorized as 'Result' (keyword match)")
            return "Result"
        
        # Check if it contains job-related organizations
        job_orgs = ['sbi', 'upsc', 'ssc', 'rrb', 'ibps', 'lic', 'aiims', 'isro', 'drdo', 
                    'army', 'navy', 'air force', 'police', 'railway', 'bank']
        
        has_job_org = any(org in trend_lower for org in job_orgs)
        
        if has_job_org:
            # If it has job org but no specific category, default to Job Notification
            print(f"   🔄 Fallback: Categorized as 'Job Notification' (organization match)")
            return "Job Notification"
        
        # Otherwise, not relevant
        print(f"   🔄 Fallback: Categorized as 'Not Relevant' (no job keywords)")
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
        """Categorize multiple trends at once with delays"""
        results = []
        for idx, trend in enumerate(trends_list):
            category = self.categorize(trend)
            results.append({
                'trend': trend,
                'category': category
            })
            
            # Add delay between batches to avoid rate limits
            if idx < len(trends_list) - 1:
                time.sleep(1.5)  # 1.5 second delay between items
        
        return results