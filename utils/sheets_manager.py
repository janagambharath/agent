import pandas as pd
import os
from datetime import datetime
from config import Config

class GoogleSheetsManager:
    """Manages data storage in CSV format (can be extended for Google Sheets)"""
    
    def __init__(self):
        self.csv_file = Config.CSV_FILE
        self.setup_csv()
    
    def setup_csv(self):
        """Initialize CSV file with headers"""
        try:
            if not os.path.exists(self.csv_file):
                df = pd.DataFrame(columns=[
                    'timestamp', 'trend', 'category', 'instagram_post', 
                    'blog_draft', 'youtube_script', 'thumbnail_idea', 'status'
                ])
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                print(f"✅ Created new CSV file: {self.csv_file}")
            else:
                # Validate existing CSV
                df = pd.read_csv(self.csv_file)
                print(f"✅ Loaded existing CSV: {len(df)} records")
        except Exception as e:
            print(f"❌ Error setting up CSV: {e}")
            raise
    
    def add_row(self, data):
        """Add a new row to the CSV"""
        try:
            # Read existing data
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file, encoding='utf-8')
            else:
                df = pd.DataFrame()
            
            # Create new row
            new_row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'trend': str(data.get('trend', '')),
                'category': str(data.get('category', '')),
                'instagram_post': str(data.get('instagram_post', '')),
                'blog_draft': str(data.get('blog_draft', '')),
                'youtube_script': str(data.get('youtube_script', '')),
                'thumbnail_idea': str(data.get('thumbnail_idea', '')),
                'status': str(data.get('status', 'Pending Review'))
            }
            
            # Check for duplicates
            if not df.empty and 'trend' in df.columns:
                if new_row['trend'] in df['trend'].values:
                    print(f"⚠️ Duplicate trend detected: {new_row['trend'][:50]}...")
                    return False
            
            # Append new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to CSV
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            
            print(f"✅ Saved: {new_row['trend'][:50]}... [{new_row['category']}]")
            return True
            
        except Exception as e:
            print(f"❌ Error adding row: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_all_data(self):
        """Get all data from CSV"""
        try:
            if not os.path.exists(self.csv_file):
                return []
            
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            
            # Clean up NaN values
            for item in data:
                for key, value in item.items():
                    if pd.isna(value):
                        item[key] = ''
            
            return data
            
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return []
    
    def update_status(self, trend, new_status):
        """Update approval status for a trend"""
        try:
            if not os.path.exists(self.csv_file):
                print(f"❌ CSV file not found: {self.csv_file}")
                return False
            
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            
            # Find matching trend
            mask = df['trend'] == trend
            
            if not mask.any():
                print(f"❌ Trend not found: {trend[:50]}...")
                return False
            
            # Update status
            df.loc[mask, 'status'] = new_status
            
            # Save changes
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            
            print(f"✅ Updated status: {trend[:50]}... → {new_status}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_by_status(self, status):
        """Get all trends with specific status"""
        try:
            all_data = self.get_all_data()
            return [item for item in all_data if item.get('status') == status]
        except:
            return []
    
    def get_pending_reviews(self):
        """Get all trends pending review"""
        return self.get_by_status('Pending Review')
    
    def get_approved_content(self):
        """Get all approved content"""
        return self.get_by_status('Approved')
    
    def get_rejected_content(self):
        """Get all rejected content"""
        return self.get_by_status('Rejected')
    
    def get_by_category(self, category):
        """Get all trends in a specific category"""
        try:
            all_data = self.get_all_data()
            return [item for item in all_data if item.get('category') == category]
        except:
            return []
    
    def delete_trend(self, trend):
        """Delete a specific trend"""
        try:
            if not os.path.exists(self.csv_file):
                return False
            
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            initial_len = len(df)
            
            # Remove matching trend
            df = df[df['trend'] != trend]
            
            if len(df) < initial_len:
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                print(f"✅ Deleted trend: {trend[:50]}...")
                return True
            else:
                print(f"❌ Trend not found for deletion")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting trend: {e}")
            return False
    
    def clear_all_data(self):
        """Clear all data (use with caution)"""
        try:
            df = pd.DataFrame(columns=[
                'timestamp', 'trend', 'category', 'instagram_post', 
                'blog_draft', 'youtube_script', 'thumbnail_idea', 'status'
            ])
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            print("✅ All data cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            return False
    
    def export_to_json(self, filename='export.json'):
        """Export data to JSON format"""
        try:
            import json
            data = self.get_all_data()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(data)} records to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting to JSON: {e}")
            return False
    
    def get_stats(self):
        """Get statistics about stored data"""
        try:
            all_data = self.get_all_data()
            
            stats = {
                'total_records': len(all_data),
                'by_status': {},
                'by_category': {},
                'recent_updates': []
            }
            
            for item in all_data:
                # Count by status
                status = item.get('status', 'Unknown')
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Count by category
                category = item.get('category', 'Unknown')
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Get recent 5 updates
            if all_data:
                stats['recent_updates'] = sorted(
                    all_data, 
                    key=lambda x: x.get('timestamp', ''), 
                    reverse=True
                )[:5]
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return None
