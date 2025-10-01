from flask import Flask, render_template, request, jsonify
from agents.scraper import GoogleTrendsScraper
from agents.categorizer import AICategorizer
from agents.content_generator import ContentGenerator
from utils.sheets_manager import GoogleSheetsManager
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize components
scraper = GoogleTrendsScraper()
categorizer = AICategorizer()
content_generator = ContentGenerator()
sheets_manager = GoogleSheetsManager()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run-agent', methods=['POST'])
def run_ai_agent():
    """Complete AI Agent Workflow"""
    try:
        # Phase 1: Data Extraction
        trends = scraper.get_job_trends()
        
        results = []
        for trend in trends[:5]:  # Process first 5 trends
            # Phase 2: Categorization
            category = categorizer.categorize(trend)
            
            if category != "Not Relevant":
                # Phase 3: Content Generation
                content = content_generator.generate_content(trend, category)
                
                # Phase 4: Update Sheets
                sheet_data = {
                    'trend': trend,
                    'category': category,
                    'instagram_post': content['instagram'],
                    'blog_draft': content['blog'],
                    'youtube_script': content['youtube'],
                    'thumbnail_idea': content['thumbnail'],
                    'status': 'Pending Review'
                }
                
                sheets_manager.add_row(sheet_data)
                results.append(sheet_data)
        
        return jsonify({
            'success': True,
            'message': f'AI Agent processed {len(results)} job trends',
            'results': results
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-trends')
def get_trends():
    """Get all processed trends"""
    try:
        trends = sheets_manager.get_all_data()
        return jsonify({'success': True, 'data': trends})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update-status', methods=['POST'])
def update_status():
    """Update approval status"""
    try:
        data = request.json
        trend = data['trend']
        new_status = data['status']
        
        success = sheets_manager.update_status(trend, new_status)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)