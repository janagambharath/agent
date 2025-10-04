from openai import OpenAI
import os
from config import Config
import re
import time

class ContentGenerator:
    """GPT-2 Agent: Generates social media content using DeepSeek R1"""
    
    def __init__(self):
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not configured")
        
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        print(f"✅ Content Generator initialized with model: {Config.AI_MODEL}")
    
    def generate_content(self, trend, category):
        """Generate social media content using AI (GPT-2 Agent) with retry logic"""
        if not trend or category == "Not Relevant":
            return self.get_fallback_content(trend, category)
        
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_content_prompt(trend, category)
                
                response = self.client.chat.completions.create(
                    model=Config.AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a social media content creator for JobYaari, specializing in Indian government job updates. Create engaging, actionable content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=Config.MAX_TOKENS,
                    temperature=Config.TEMPERATURE,
                    extra_headers={
                        "HTTP-Referer": Config.APP_URL,
                        "X-Title": Config.APP_NAME
                    }
                )
                
                content_text = response.choices[0].message.content
                
                # Clean DeepSeek's thinking process
                content_text = self._clean_deepseek_response(content_text)
                
                parsed_content = self.parse_content(content_text)
                
                # Validate parsed content
                if not any(parsed_content.values()):
                    print(f"   ⚠️ Empty content generated, using fallback")
                    return self.get_fallback_content(trend, category)
                
                return parsed_content
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"   ⏳ Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ Rate limit exceeded, using fallback content")
                        return self.get_fallback_content(trend, category)
                else:
                    print(f"   ❌ Content generation error: {e}")
                    return self.get_fallback_content(trend, category)
        
        return self.get_fallback_content(trend, category)
    
    def _clean_deepseek_response(self, response):
        """Remove DeepSeek R1's thinking tags"""
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return response.strip()
    
    def _build_content_prompt(self, trend, category):
        """Build the content generation prompt - Optimized for DeepSeek R1"""
        # Add links based on category
        link_placeholder = self._get_link_placeholder(category)
        
        return f"""Create social media content for this Indian government job update.

TREND: {trend}
CATEGORY: {category}

Generate content with these sections (use EXACT labels):

INSTAGRAM_POST:
Write 2-3 lines with emojis and 3-5 hashtags. Make it urgent and engaging for 18-30 year olds.

BLOG_DRAFT:
Write 120-150 words with:
- Opening hook
- Key details (dates, eligibility, {link_placeholder})
- Benefits
- Call-to-action
Use short paragraphs.

YOUTUBE_SCRIPT:
30-second script:
- Hook (5 sec)
- Main content (20 sec)  
- Call-to-action (5 sec)
Include visual cues in [brackets]

THUMBNAIL_IDEA:
Describe eye-catching thumbnail:
- Main text (what to write)
- Background color
- Visual elements
- Text placement

Use Hindi-English mix where appropriate. Keep all content shareable and actionable."""
    
    def _get_link_placeholder(self, category):
        """Get appropriate link placeholder based on category"""
        if category == "Admit Card":
            return "admit card download link"
        elif category == "Job Notification":
            return "application link"
        elif category == "Result":
            return "result link"
        return "official link"
    
    def parse_content(self, content_text):
        """Parse the structured AI response"""
        content = {
            'instagram': '',
            'blog': '', 
            'youtube': '',
            'thumbnail': ''
        }
        
        sections = {
            'INSTAGRAM_POST:': 'instagram',
            'BLOG_DRAFT:': 'blog',
            'YOUTUBE_SCRIPT:': 'youtube',
            'THUMBNAIL_IDEA:': 'thumbnail'
        }
        
        current_section = None
        lines = content_text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line starts a new section
            section_found = False
            for section_header, section_key in sections.items():
                if line_stripped.upper().startswith(section_header.upper()):
                    current_section = section_key
                    # Get content after the header
                    content_after_header = line_stripped[len(section_header):].strip()
                    if content_after_header:
                        content[current_section] = content_after_header
                    section_found = True
                    break
            
            # If not a section header and we're in a section, add to current section
            if not section_found and current_section and line_stripped:
                # Skip separator lines
                if line_stripped.startswith('---') or line_stripped.startswith('===') or line_stripped.startswith('***'):
                    continue
                # Append to current section
                if content[current_section]:
                    content[current_section] += ' ' + line_stripped
                else:
                    content[current_section] = line_stripped
        
        # Clean up each section
        for key in content:
            content[key] = content[key].strip()
            # Remove any remaining section markers
            for header in sections.keys():
                content[key] = content[key].replace(header, '').strip()
        
        return content
    
    def get_fallback_content(self, trend, category):
        """Fallback content if AI fails"""
        hashtags_map = {
            "Admit Card": "#AdmitCard #HallTicket #ExamUpdate #JobYaari #SarkariExam",
            "Job Notification": "#JobAlert #GovernmentJobs #Vacancy #Recruitment #JobYaari",
            "Result": "#Result #MeritList #ExamResult #JobYaari #SarkariResult"
        }
        
        link_map = {
            "Admit Card": "Download Admit Card: [Official Link]",
            "Job Notification": "Apply Online: [Official Link]",
            "Result": "Check Result: [Official Link]"
        }
        
        hashtags = hashtags_map.get(category, "#GovernmentJobs #JobUpdate #JobYaari")
        link_text = link_map.get(category, "Visit: [Official Link]")
        
        return {
            'instagram': f"🎯 {trend}\n\nImportant update for government job aspirants! 📝\n{link_text}\n\n{hashtags} 🔥",
            
            'blog': f"""📢 Latest Update: {trend}

This is an important development for job seekers across India. {category} notifications are crucial for candidates preparing for government sector careers.

🔑 Key Points:
• Important update for aspirants
• Check official notification for eligibility criteria
• {link_text}
• Don't miss important deadlines

Stay updated with JobYaari for more government job notifications and exam updates! 🚀

{link_text}""",
            
            'youtube': f"""[OPENING - 0:00-0:05]
🔔 Big breaking news for government job seekers!

[MAIN CONTENT - 0:05-0:25]
{trend}

📋 Important Details:
- Check eligibility criteria
- {link_text}
- Note all important dates

[CALL TO ACTION - 0:25-0:30]
👍 Like, Share & Subscribe for daily job updates!
Visit JobYaari.com for complete details!""",
            
            'thumbnail': f"""🎨 THUMBNAIL DESIGN:

Background: Bold YELLOW with RED accent border

Main Text (White, Bold, 72pt): "{category.upper()}"
Subtitle (Black, 48pt): {trend[:30]}...

Visual Elements:
- Government building silhouette (bottom)
- Red "NEW" badge (top-right corner)
- Urgency indicator: Clock icon
- Professional, clean design for Indian audience

Layout: Center-aligned with strong contrast"""
        }
    
    def validate_content(self, content):
        """Validate generated content quality"""
        issues = []
        
        if not content['instagram'] or len(content['instagram']) < 20:
            issues.append("Instagram post too short")
        
        if not content['blog'] or len(content['blog']) < 50:
            issues.append("Blog draft too short")
        
        if not content['youtube'] or len(content['youtube']) < 30:
            issues.append("YouTube script too short")
        
        if not content['thumbnail']:
            issues.append("Thumbnail idea missing")
        
        return len(issues) == 0, issues