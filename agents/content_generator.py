from openai import OpenAI
import os
from config import Config

class ContentGenerator:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_content(self, trend, category):
        """Generate social media content using AI (GPT-2 Agent)"""
        if not trend or category == "Not Relevant":
            return self.get_fallback_content(trend, category)
        
        try:
            prompt = self._build_content_prompt(trend, category)
            
            response = self.client.chat.completions.create(
                model=Config.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a social media content creator for JobYaari, specializing in Indian government job updates."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            
            content_text = response.choices[0].message.content
            parsed_content = self.parse_content(content_text)
            
            # Validate parsed content
            if not any(parsed_content.values()):
                print(f"⚠️ Empty content generated, using fallback for: {trend[:50]}...")
                return self.get_fallback_content(trend, category)
            
            return parsed_content
            
        except Exception as e:
            print(f"❌ Content generation error for '{trend[:50]}...': {e}")
            return self.get_fallback_content(trend, category)
    
    def _build_content_prompt(self, trend, category):
        """Build the content generation prompt"""
        return f"""Create engaging social media content for this Indian government job update.

TREND: {trend}
CATEGORY: {category}

Generate content in this EXACT format with clear labels:

INSTAGRAM_POST:
[Create a 2-3 line Instagram caption with emojis and 3-5 hashtags. Make it engaging for Indian job seekers aged 18-30. Include urgency if applicable.]

BLOG_DRAFT:
[Write a 120-150 word blog post with: Opening hook, key details (dates/eligibility/links), benefits, and call-to-action. Use short paragraphs.]

YOUTUBE_SCRIPT:
[Create a 30-second script with: Hook (5 sec), Main content (20 sec), Call-to-action (5 sec). Include visual cues in brackets.]

THUMBNAIL_IDEA:
[Describe a eye-catching YouTube thumbnail: Main text, background color, visual elements, text placement. Keep it bold and readable.]

Use simple Hindi-English mix where appropriate. Make content shareable and actionable."""
    
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
                if line_stripped.startswith(section_header):
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
                if line_stripped.startswith('---') or line_stripped.startswith('==='):
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
            "Admit Card": "#AdmitCard #HallTicket #ExamUpdate #JobYaari",
            "Job Notification": "#JobAlert #GovernmentJobs #Vacancy #Recruitment",
            "Result": "#Result #MeritList #ExamResult #JobYaari"
        }
        
        hashtags = hashtags_map.get(category, "#GovernmentJobs #JobUpdate #JobYaari")
        
        return {
            'instagram': f"🎯 {trend}\n\nImportant update for government job aspirants! 📝\nCheck official website for complete details.\n\n{hashtags} 🔥",
            
            'blog': f"""Latest Update: {trend}

This is an important development for job seekers across India. {category} notifications are crucial for candidates preparing for government sector careers.

Key Points:
• Important update for aspirants
• Check official notification for eligibility
• Visit official website for application process
• Don't miss important deadlines

Stay updated with JobYaari for more government job notifications and exam updates!""",
            
            'youtube': f"""[Opening Hook]
🔔 Big news for government job seekers!

[Main Content]
{trend}

[Details]
Check the official notification for:
- Eligibility criteria
- Application process
- Important dates

[Call-to-Action]
👍 Like, Share & Subscribe for daily job updates!
Visit JobYaari.com for more details.""",
            
            'thumbnail': f"""Bold yellow background with red accent border. 

Main text (White, bold): "{category.upper()}"
Subtitle (Black): First 4-5 words of trend

Visual elements: 
- Government building silhouette
- Red "NEW" badge in top-right corner
- Professional look suitable for Indian audience"""
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
        
        return len(issues) == 0, issues
