from flask import Flask, render_template, request, jsonify
from agents.scraper import GoogleTrendsScraper
from agents.categorizer import AICategorizer
from agents.content_generator import ContentGenerator
from utils.sheets_manager import GoogleSheetsManager
from config import Config
import os
import traceback
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Validate configuration
config_errors, config_warnings = Config.validate()
if config_errors:
    print("❌ Configuration errors:")
    for error in config_errors:
        print(f"  - {error}")
    print("\n⚠️ Please fix errors in .env file before continuing")
    exit(1)

if config_warnings:
    print("⚠️ Configuration warnings:")
    for warning in config_warnings:
        print(f"  - {warning}")

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
    print("   Make sure OPENROUTER_API_KEY is set in .env file")
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
        },
        'model': Config.AI_MODEL
    })

@app.route('/run-agent', methods=['POST'])
def run_ai_agent():
    """Complete AI Agent Workflow with Rate Limit Handling"""
    try:
        # Validate components
        if not all([scraper, categorizer, content_generator, sheets_manager]):
            missing = []
            if not scraper: missing.append('Scraper')
            if not categorizer: missing.append('Categorizer')
            if not content_generator: missing.append('Content Generator')
            if not sheets_manager: missing.append('Sheets Manager')
            
            return jsonify({
                'success': False,
                'error': f'Components not initialized: {", ".join(missing)}. Check server logs.'
            }), 500
        
        print("\n" + "="*60)
        print("🤖 Starting AI Agent Workflow...")
        print("="*60)
        
        # Phase 1: Data Extraction
        print("\n📊 Phase 1: Data Extraction")
        print("-" * 40)
        trends = scraper.get_job_trends()
        print(f"✅ Found {len(trends)} trends")
        
        results = []
        processed_count = 0
        relevant_count = 0
        skipped_count = 0
        error_count = 0
        
        # Process only 3 trends at a time to avoid rate limits (optimized for free tier)
        BATCH_SIZE = 3
        trends_to_process = trends[:BATCH_SIZE]
        
        print(f"\n⚙️ Processing {len(trends_to_process)} trends (batch size: {BATCH_SIZE})")
        print("-" * 40)
        
        for idx, trend in enumerate(trends_to_process, 1):
            try:
                print(f"\n{'='*60}")
                print(f"🔄 Item {idx}/{len(trends_to_process)}: {trend[:60]}...")
                print(f"{'='*60}")
                
                # Phase 2: Categorization (GPT-1 Agent)
                print("\n🏷️ Phase 2: AI Categorization (GPT-1 Agent)")
                print("-" * 40)
                
                category = categorizer.categorize(trend)
                
                print(f"✅ Category: {category}")
                
                if category != "Not Relevant":
                    relevant_count += 1
                    
                    # Small delay to avoid rate limits (important for free tier)
                    if idx < len(trends_to_process):
                        time.sleep(1)  # 1 second delay between items
                    
                    # Phase 3: Content Generation (GPT-2 Agent)
                    print("\n✍️ Phase 3: Content Generation (GPT-2 Agent)")
                    print("-" * 40)
                    
                    content = content_generator.generate_content(trend, category)
                    
                    # Validate content
                    is_valid, issues = content_generator.validate_content(content)
                    if not is_valid:
                        print(f"⚠️ Content validation issues: {', '.join(issues)}")
                    else:
                        print("✅ Content generated and validated")
                    
                    # Phase 4: Update Storage
                    print("\n💾 Phase 4: Saving to Storage")
                    print("-" * 40)
                    
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
                        print(f"✅ Saved to storage successfully")
                    else:
                        print(f"⚠️ Failed to save (might be duplicate)")
                        error_count += 1
                else:
                    print(f"⏭️ Skipped: Not relevant to job trends")
                    skipped_count += 1
                
                processed_count += 1
                
            except Exception as e:
                print(f"\n❌ Error processing trend: {e}")
                traceback.print_exc()
                error_count += 1
                continue
        
        # Summary
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETE!")
        print("="*60)
        print(f"📊 Summary:")
        print(f"   • Total Processed: {processed_count}/{len(trends_to_process)}")
        print(f"   • Relevant Items: {relevant_count}")
        print(f"   • Skipped (Not Relevant): {skipped_count}")
        print(f"   • Errors: {error_count}")
        print(f"   • Successfully Saved: {len(results)}")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'message': f'AI Agent processed {relevant_count} relevant job trends successfully!',
            'stats': {
                'processed': processed_count,
                'relevant': relevant_count,
                'skipped': skipped_count,
                'errors': error_count,
                'saved': len(results),
                'batch_size': BATCH_SIZE
            },
            'results': results
        })
    
    except Exception as e:
        print(f"\n❌ Workflow error: {e}")
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
            print(f"✅ Status updated: {trend[:50]}... → {new_status}")
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
            return jsonify({
                'success': False, 
                'error': 'Sheets manager not initialized'
            }), 500
        
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
        
        return jsonify({
            'success': True, 
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all data (use with caution)"""
    try:
        if not sheets_manager:
            return jsonify({
                'success': False,
                'error': 'Sheets manager not initialized'
            }), 500
        
        # This would need to be implemented in sheets_manager
        # For now, just return info
        return jsonify({
            'success': True,
            'message': 'Clear data endpoint - to be implemented'
        })
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False, 
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'success': False, 
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" " * 20 + "🚀 JobYaari AI Agent")
    print("="*70)
    print(f"📌 Environment: {'Production' if Config.is_production() else 'Development'}")
    print(f"🤖 AI Model: {Config.AI_MODEL}")
    print(f"🌐 Port: {Config.PORT}")
    print(f"🔧 Debug Mode: {Config.DEBUG}")
    print(f"📊 Max Tokens: {Config.MAX_TOKENS}")
    print(f"🌡️ Temperature: {Config.TEMPERATURE}")
    print("="*70)
    print("\n💡 Tips for Free Tier:")
    print("   • Processing 3 items per batch (optimized for rate limits)")
    print("   • Automatic retry on rate limit errors")
    print("   • 1-second delay between API calls")
    print("\n🔗 Access the dashboard at: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',
        port=Config.PORT
    )