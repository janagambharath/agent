import pandas as pd
import os
from datetime import datetime
from config import Config

# Google Sheets imports
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️ gspread not available - Google Sheets integration disabled")

class GoogleSheetsManager:
    """Manages data storage in CSV + Google Sheets (as per assignment)"""
    
    def __init__(self):
        self.csv_file = Config.CSV_FILE
        self.sheet_id = Config.GOOGLE_SHEET_ID
        self.credentials_file = Config.GOOGLE_CREDENTIALS_FILE
        
        # Setup CSV (fallback storage)
        self.setup_csv()
        
        # Setup Google Sheets (primary storage as per assignment)
        self.google_sheet = None
        self.setup_google_sheets()
    
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
                df = pd.read_csv(self.csv_file)
                print(f"✅ Loaded existing CSV: {len(df)} records")
        except Exception as e:
            print(f"❌ Error setting up CSV: {e}")
            raise
    
    def setup_google_sheets(self):
        """Initialize Google Sheets connection (REQUIRED by assignment)"""
        if not GSPREAD_AVAILABLE:
            print("⚠️ Google Sheets integration not available - install gspread")
            return
        
        if not self.sheet_id:
            print("⚠️ GOOGLE_SHEET_ID not configured - Google Sheets disabled")
            return
        
        if not os.path.exists(self.credentials_file):
            print(f"⚠️ Google credentials file not found: {self.credentials_file}")
            print("   Download credentials from Google Cloud Console")
            print("   https://console.cloud.google.com/apis/credentials")
            return
        
        try:
            # Define the required scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            client = gspread.authorize(creds)
            
            # Open the sheet
            self.google_sheet = client.open_by_key(self.sheet_id).sheet1
            
            # Setup headers if empty
            headers = self.google_sheet.row_values(1)
            if not headers:
                self.google_sheet.append_row([
                    'Timestamp', 'Trend', 'Category', 'Instagram Post',
                    'Blog Draft', 'YouTube Script', 'Thumbnail Idea', 'Status'
                ])
            
            print(f"✅ Connected to Google Sheet: {self.sheet_id}")
            
        except Exception as e:
            print(f"❌ Error connecting to Google Sheets: {e}")
            print("   Falling back to CSV-only mode")
            self.google_sheet = None
    
    def add_row(self, data):
        """Add a new row to CSV AND Google Sheets"""
        # Create row data
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
        
        # Add to CSV
        csv_success = self._add_to_csv(new_row)
        
        # Add to Google Sheets (if available)
        sheets_success = self._add_to_google_sheets(new_row)
        
        if csv_success or sheets_success:
            print(f"✅ Saved: {new_row['trend'][:50]}... [{new_row['category']}]")
            return True
        return False
    
    def _add_to_csv(self, new_row):
        """Add row to CSV file"""
        try:
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file, encoding='utf-8')
            else:
                df = pd.DataFrame()
            
            # Check for duplicates
            if not df.empty and 'trend' in df.columns:
                if new_row['trend'] in df['trend'].values:
                    print(f"⚠️ Duplicate in CSV: {new_row['trend'][:50]}...")
                    return False
            
            # Append and save
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"❌ Error adding to CSV: {e}")
            return False
    
    def _add_to_google_sheets(self, new_row):
        """Add row to Google Sheets"""
        if not self.google_sheet:
            return False
        
        try:
            # Check for duplicates
            all_trends = self.google_sheet.col_values(2)  # Column B (Trend)
            if new_row['trend'] in all_trends:
                print(f"⚠️ Duplicate in Google Sheets: {new_row['trend'][:50]}...")
                return False
            
            # Append row
            row_values = [
                new_row['timestamp'],
                new_row['trend'],
                new_row['category'],
                new_row['instagram_post'],
                new_row['blog_draft'],
                new_row['youtube_script'],
                new_row['thumbnail_idea'],
                new_row['status']
            ]
            
            self.google_sheet.append_row(row_values)
            print(f"✅ Added to Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Error adding to Google Sheets: {e}")
            return False
    
    def get_all_data(self):
        """Get all data from CSV (primary) or Google Sheets (fallback)"""
        try:
            # Try CSV first
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file, encoding='utf-8')
                data = df.to_dict('records')
                
                # Clean NaN values
                for item in data:
                    for key, value in item.items():
                        if pd.isna(value):
                            item[key] = ''
                
                return data
            
            # Fallback to Google Sheets
            elif self.google_sheet:
                records = self.google_sheet.get_all_records()
                return records
            
            return []
            
        except Exception as e:
            print(f"❌ Error reading data: {e}")
            return []
    
    def update_status(self, trend, new_status):
        """Update approval status in BOTH CSV and Google Sheets"""
        csv_success = self._update_status_csv(trend, new_status)
        sheets_success = self._update_status_sheets(trend, new_status)
        
        return csv_success or sheets_success
    
    def _update_status_csv(self, trend, new_status):
        """Update status in CSV"""
        try:
            if not os.path.exists(self.csv_file):
                return False
            
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            mask = df['trend'] == trend
            
            if not mask.any():
                return False
            
            df.loc[mask, 'status'] = new_status
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            
            print(f"✅ Updated CSV: {trend[:50]}... → {new_status}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating CSV status: {e}")
            return False
    
    def _update_status_sheets(self, trend, new_status):
        """Update status in Google Sheets"""
        if not self.google_sheet:
            return False
        
        try:
            # Find the row
            all_trends = self.google_sheet.col_values(2)  # Column B
            
            if trend not in all_trends:
                return False
            
            row_index = all_trends.index(trend) + 1  # +1 because sheets are 1-indexed
            
            # Update status column (Column H = 8)
            self.google_sheet.update_cell(row_index, 8, new_status)
            
            print(f"✅ Updated Google Sheet: {trend[:50]}... → {new_status}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating Google Sheets status: {e}")
            return False
    
    def get_by_status(self, status):
        """Get all trends with specific status"""
        all_data = self.get_all_data()
        return [item for item in all_data if item.get('status') == status]
    
    def get_pending_reviews(self):
        """Get all trends pending review"""
        return self.get_by_status('Pending Review')
    
    def get_approved_content(self):
        """Get all approved content (READY FOR PUBLISHING)"""
        return self.get_by_status('Approved')
    
    def get_rejected_content(self):
        """Get all rejected content"""
        return self.get_by_status('Rejected')
    
    def get_by_category(self, category):
        """Get all trends in a specific category"""
        all_data = self.get_all_data()
        return [item for item in all_data if item.get('category') == category]
    
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
                status = item.get('status', 'Unknown')
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                category = item.get('category', 'Unknown')
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
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
