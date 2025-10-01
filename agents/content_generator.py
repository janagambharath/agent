import openai
import os
from config import Config

class ContentGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_content(self, trend, category):
        """Generate social media content using AI (GPT-2 Agent)"""
        try:
            prompt = self._build_content_prompt(trend, category)
            
            response = self.client.chat.completions.create(
                model=Config.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            
            content_text = response.choices[0].message.content
            return self.parse_content(content_text)
            
        except Exception as e:
            print(f"Content generation error: {e}")
            return self.get_fallback_content(trend, category)
    
    def _build_content_prompt(self, trend, category):
        """Build the content generation prompt"""
        return f"""
        You are a social media manager for JobYaari, a platform for government job seekers in India.
        
        TASK: Create engaging social media content for this job update:
        
        TREND: {trend}
        CATEGORY: {category}
        
        Generate content in this EXACT format. Follow the structure precisely:
        
        INSTAGRAM_POST: [Create an engaging Instagram post caption with 3-5 relevant hashtags. Make it viral-style with emojis. Target Indian youth preparing for government jobs. 2-3 lines maximum.]
        
        BLOG_DRAFT: [Write a 150-word blog draft with application links, important dates, and eligibility criteria. Include call-to-action to visit official website. Format with short paragraphs.]
        
        YOUTUBE_SCRIPT: [Create a 30-second YouTube reel script with hook, content, and call-to-action. Include visual cues. 4-5 lines total.]
        
        THUMBNAIL_IDEA: [Describe an eye-catching thumbnail design for YouTube with text placement, colors, and visual elements.]
        
        Make the content specific to Indian government job aspirants. Use relevant emojis and engaging language.
        """
    
    def parse_content(self, content_text):
        """Parse the structured AI response"""
        lines = content_text.split('\n')
        content = {
            'instagram': '',
            'blog': '', 
            'youtube': '',
            'thumbnail': ''
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('INSTAGRAM_POST:'):
                current_section = 'instagram'
                content['instagram'] = line.replace('INSTAGRAM_POST:', '').strip()
            elif line.startswith('BLOG_DRAFT:'):
                current_section = 'blog'
                content['blog'] = line.replace('BLOG_DRAFT:', '').strip()
            elif line.startswith('YOUTUBE_SCRIPT:'):
                current_section = 'youtube'
                content['youtube'] = line.replace('YOUTUBE_SCRIPT:', '').strip()
            elif line.startswith('THUMBNAIL_IDEA:'):
                current_section = 'thumbnail'
                content['thumbnail'] = line.replace('THUMBNAIL_IDEA:', '').strip()
            elif current_section and line and not line.startswith('---') and not line.startswith('['):
                # Append to current section if it's content (not a new section)
                if line:  # Only add non-empty lines
                    content[current_section] += ' ' + line
        
        # Clean up each section
        for key in content:
            content[key] = content[key].strip()
        
        return content
    
    def get_fallback_content(self, trend, category):
        """Fallback content if AI fails"""
        hashtags = {
            "Admit Card": "#AdmitCard #HallTicket #ExamUpdate",
            "Job Notification": "#JobAlert #GovernmentJobs #Vacancy",
            "Result": "#Result #MeritList #ExamResult"
        }
        
        return {
            'instagram': f"🎯 {trend} | Important update for government job aspirants! 📝\n\nCheck official website for details & application links.\n\n{hashtags.get(category, '#GovernmentJobs #JobUpdate')} 🔥",
            'blog': f"Latest Update: {trend}\n\nThis is a significant development for job seekers across India. The notification brings new opportunities for candidates looking to build their career in government sector.\n\nKey Highlights:\n- Important update for aspirants\n- Check eligibility criteria carefully\n- Visit official website for application details\n- Don't miss the deadline\n\nStay updated with JobYaari for more government job notifications!",
            'youtube': f"Hook: Big news for government job seekers!\nContent: {trend}\nDetails: Check official notification for eligibility and application process\nCall-to-action: Like, share, and subscribe for more job updates!",
            'thumbnail': f"Thumbnail Design: Bold text '{trend}' on bright yellow background with government building silhouette. Red 'NEW' badge in corner. Professional but eye-catching design suitable for Indian audience."
        }
