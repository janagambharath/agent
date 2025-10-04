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
import json

# ============================================
# 🔹 Load Environment Variables
# ============================================
load_dotenv()  # Loads .env locally (ignored on Render)

# 🔹 Ensure Google credentials work in Render or local
def setup_google_credentials():
    """
    Ensures Google Cloud credentials are available.
    - If GOOGLE_APPLICATION_CREDENTIALS exists, use that path (Render Secret File)
    - Otherwise, if GOOGLE_CREDENTIALS env var exists, write it to credentials.json
    - Else, check if local credentials.json exists
    """
    gac_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if gac_path and os.path.exists(gac_path):
        print(f"✅ Using Google credentials from: {gac_path}")
        return

    creds_env = os.getenv("GOOGLE_CREDENTIALS")
    if creds_env:
        with open("credentials.json", "w") as f:
            f.write(creds_env)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")
        print("✅ GOOGLE_CREDENTIALS env var found — credentials.json created")
    elif os.path.exists("credentials.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")
        print("✅ Local credentials.json found and loaded")
    else:
        print("⚠️ No Google credentials found — Sheets access may fail")

setup_google_credentials()

# ============================================
# 🔹 Initialize Flask app
# ============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# ============================================
# 🔹 Validate Configuration
# ============================================
config_errors, config_warnings = Config.validate()
if config_errors:
    print("❌ Configuration errors:")
    for error in config_errors:
        print(f"  - {error}")
    print("\n⚠️ Please fix errors in .env or Render Environment Variables before continuing")
    exit(1)

if config_warnings:
    print("⚠️ Configuration warnings:")
    for warning in config_warnings:
        print(f"  - {warning}")

# ============================================
# 🔹 Initialize AI Components
# ============================================
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
    print("   Make sure OPENROUTER_API_KEY is set in .env or Render")
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


# ============================================
# 🔹 Flask Routes
# ============================================

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
        trends = scraper.get_job_trends()
        print(f"✅ Found {len(trends)} trends")

        results = []
        processed_count = 0
        relevant_count = 0
        skipped_count = 0
        error_count = 0

        BATCH_SIZE = 3
        trends_to_process = trends[:BATCH_SIZE]

        print(f"\n⚙️ Processing {len(trends_to_process)} trends (batch size: {BATCH_SIZE})")

        for idx, trend in enumerate(trends_to_process, 1):
            try:
                print(f"\n{'='*60}")
                print(f"🔄 Item {idx}/{len(trends_to_process)}: {trend[:60]}...")
                print(f"{'='*60}")

                # Phase 2: Categorization
                category = categorizer.categorize(trend)
                print(f"✅ Category: {category}")

                if category != "Not Relevant":
                    relevant_count += 1
                    if idx < len(trends_to_process):
                        time.sleep(1)

                    # Phase 3: Content Generation
                    content = content_generator.generate_content(trend, category)

                    # Validate
                    is_valid, issues = content_generator.validate_content(content)
                    if not is_valid:
                        print(f"⚠️ Content validation issues: {', '.join(issues)}")

                    # Phase 4: Save
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
                        print("✅ Saved to storage")
                    else:
                        print("⚠️ Failed to save (duplicate?)")
                        error_count += 1
                else:
                    print("⏭️ Skipped: Not relevant")
                    skipped_count += 1

                processed_count += 1

            except Exception as e:
                print(f"❌ Error processing trend: {e}")
                traceback.print_exc()
                error_count += 1
                continue

        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETE!")
        print("="*60)
        print(f"📊 Processed: {processed_count}/{len(trends_to_process)}")
        print(f"✅ Relevant: {relevant_count}")
        print(f"⏭️ Skipped: {skipped_count}")
        print(f"⚠️ Errors: {error_count}")
        print(f"💾 Saved: {len(results)}")

        return jsonify({
            'success': True,
            'message': f'AI Agent processed {relevant_count} relevant job trends successfully!',
            'stats': {
                'processed': processed_count,
                'relevant': relevant_count,
                'skipped': skipped_count,
                'errors': error_count,
                'saved': len(results)
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
            return jsonify({'success': False, 'error': 'Sheets manager not initialized'}), 500
        trends = sheets_manager.get_all_data()
        return jsonify({'success': True, 'data': trends, 'count': len(trends)})
    except Exception as e:
        print(f"❌ Error fetching trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/update-status', methods=['POST'])
def update_status():
    """Update approval status"""
    try:
        if not sheets_manager:
            return jsonify({'success': False, 'error': 'Sheets manager not initialized'}), 500

        data = request.json
        if not data or 'trend' not in data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Missing trend/status'}), 400

        trend = data['trend']
        new_status = data['status']
        valid_statuses = ['Pending Review', 'Approved', 'Rejected']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': f'Invalid status. Must be one of {valid_statuses}'}), 400

        success = sheets_manager.update_status(trend, new_status)
        if success:
            print(f"✅ Status updated: {trend[:50]} → {new_status}")
            return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update status'}), 500

    except Exception as e:
        print(f"❌ Error updating status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
        for item in all_data:
            category = item.get('category', 'Unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all data (placeholder)"""
    try:
        return jsonify({'success': True, 'message': 'Clear data endpoint - to be implemented'})
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


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
