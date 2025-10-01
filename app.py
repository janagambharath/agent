from flask import Flask, render_template, request, jsonify
from agents.scraper import GoogleTrendsScraper
from agents.categorizer import AICategorizer
from agents.content_generator import ContentGenerator
from utils.sheets_manager import GoogleSheetsManager
from config import Config
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Validate configuration
config_errors = Config.validate()
if config_errors:
    print("⚠️ Configuration warnings:")
    for error in config_errors:
        print(f"  - {error}")

# Initialize components with error handling
try:
    scraper = GoogleTrendsScraper()
    print("✅ Scraper initialized")
except Exception as e:
    print(f"❌ Scraper initialization failed: {e}")
    scraper = None

try:
    categorizer = AICategorizer()
    print("✅ AI Categorizer initialized")
except Exception as e:
    print(f"❌ AI Categorizer initialization failed: {e}")
    print("   Make sure OPENAI_API_KEY is set in .env file")
    categorizer = None

try:
    content_generator = ContentGenerator()
    print("✅ Content Generator initialized")
except Exception as e:
    print(f"❌ Content Generator initialization failed: {e}")
    content_generator = None

try:
    sheets_manager = GoogleSheetsManager()
    print("✅ Sheets Manager initialized")
except Exception as e:
    print(f"❌ Sheets Manager initialization failed: {e}")
    sheets_manager = None

@app.route('/')
def home():
    """Render main dashboard"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'components': {
            'scraper': scraper is not None,
            'categorizer': categorizer is not None,
            'content_generator': content_generator is not None,
            'sheets_manager': sheets_manager is not None
        }
    })

@app.route('/run-agent', methods=['POST'])
def run_ai_agent():
    """Complete AI Agent Workflow"""
    try:
        # Validate components
        if not all([scraper, categorizer, content_generator, sheets_manager]):
            return jsonify({
                'success': False,
                'error': 'One or more AI components failed to initialize. Check server logs.'
            }), 500
        
        print("\n🤖 Starting AI Agent Workflow...")
        
        # Phase 1: Data Extraction
        print("📊 Phase 1: Scraping trends...")
        trends = scraper.get_job_trends()
        print(f"   Found {len(trends)} trends")
        
        results = []
        processed_count = 0
        relevant_count = 0
        
        # Process first 5 trends (to avoid rate limits)
        for idx, trend in enumerate(trends[:5], 1):
            try:
                print(f"\n🔄 Processing {idx}/5: {trend[:50]}...")
                
                # Phase 2: Categorization
                print("   🏷️ Categorizing...")
                category = categorizer.categorize(trend)
                print(f"   Category: {category}")
                
                if category != "Not Relevant":
                    relevant_count += 1
                    
                    # Phase 3: Content Generation
                    print("   ✍️ Generating content...")
                    content = content_generator.generate_content(trend, category)
                    
                    # Phase 4: Update Storage
                    sheet_data = {
                        'trend': trend,
                        'category': category,
                        'instagram_post': content.get('instagram', ''),
                        'blog_draft': content.get('blog', ''),
                        'youtube_script': content.get('youtube', ''),
                        'thumbnail_idea': content.get('thumbnail', ''),
                        'status': 'Pending Review'
                    }
                    
                    if sheets_manager.add_row(sheet_data):
                        results.append(sheet_data)
                        print(f"   ✅ Saved successfully")
                    else:
                        print(f"   ⚠️ Failed to save")
                else:
                    print(f"   ⏭️ Skipped (not relevant)")
                
                processed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing trend: {e}")
                traceback.print_exc()
                continue
        
        print(f"\n✅ Workflow complete!")
        print(f"   Processed: {processed_count}/5")
        print(f"   Relevant: {relevant_count}")
        print(f"   Saved: {len(results)}")
        
        return jsonify({
            'success': True,
            'message': f'AI Agent processed {relevant_count} relevant job trends',
            'stats': {
                'processed': processed_count,
                'relevant': relevant_count,
                'saved': len(results)
            },
            'results': results
        })
    
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Workflow failed: {str(e)}'
        }), 500

@app.route('/get-trends')
def get_trends():
    """Get all processed trends"""
    try:
        if not sheets_manager:
            return jsonify({
                'success': False,
                'error': 'Sheets manager not initialized'
            }), 500
        
        trends = sheets_manager.get_all_data()
        return jsonify({
            'success': True,
            'data': trends,
            'count': len(trends)
        })
    except Exception as e:
        print(f"❌ Error fetching trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/update-status', methods=['POST'])
def update_status():
    """Update approval status"""
    try:
        if not sheets_manager:
            return jsonify({
                'success': False,
                'error': 'Sheets manager not initialized'
            }), 500
        
        data = request.json
        
        if not data or 'trend' not in data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: trend and status'
            }), 400
        
        trend = data['trend']
        new_status = data['status']
        
        # Validate status
        valid_statuses = ['Pending Review', 'Approved', 'Rejected']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {valid_statuses}'
            }), 400
        
        success = sheets_manager.update_status(trend, new_status)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Status updated to {new_status}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update status'
            }), 500
            
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/stats')
def get_stats():
    """Get statistics"""
    try:
        if not sheets_manager:
            return jsonify({'success': False, 'error': 'Sheets manager not initialized'}), 500
        
        all_data = sheets_manager.get_all_data()
        
        stats = {
            'total': len(all_data),
            'pending': len([t for t in all_data if t.get('status') == 'Pending Review']),
            'approved': len([t for t in all_data if t.get('status') == 'Approved']),
            'rejected': len([t for t in all_data if t.get('status') == 'Rejected']),
            'by_category': {}
        }
        
        # Count by category
        for item in all_data:
            category = item.get('category', 'Unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 JobYaari AI Agent Starting...")
    print("="*50)
    print(f"Environment: {'Production' if Config.is_production() else 'Development'}")
    print(f"Port: {Config.PORT}")
    print(f"Debug: {Config.DEBUG}")
    print("="*50 + "\n")
    
    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',
        port=Config.PORT
    )
