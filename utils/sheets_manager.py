import pandas as pd
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

class GoogleSheetsManager:
    def __init__(self):
        self.csv_file = "job_trends_data.csv"
        self.setup_csv()
    
    def setup_csv(self):
        """Initialize CSV file with headers (fallback for Google Sheets)"""
        if not os.path.exists(self.csv_file):
            df = pd.DataFrame(columns=[
                'timestamp', 'trend', 'category', 'instagram_post', 
                'blog_draft', 'youtube_script', 'thumbnail_idea', 'status'
            ])
            df.to_csv(self.csv_file, index=False)
    
    def add_row(self, data):
        """Add a new row to the CSV (simulating Google Sheets)"""
        try:
            df = pd.read_csv(self.csv_file)
            
            new_row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'trend': data['trend'],
                'category': data['category'],
                'instagram_post': data['instagram_post'],
                'blog_draft': data['blog_draft'],
                'youtube_script': data['youtube_script'],
                'thumbnail_idea': data['thumbnail_idea'],
                'status': data.get('status', 'Pending Review')
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.csv_file, index=False)
            print(f"✅ Added trend to CSV: {data['trend']}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding row: {e}")
            return False
    
    def get_all_data(self):
        """Get all data from CSV"""
        try:
            df = pd.read_csv(self.csv_file)
            return df.to_dict('records')
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return []
    
    def update_status(self, trend, new_status):
        """Update approval status"""
        try:
            df = pd.read_csv(self.csv_file)
            mask = df['trend'] == trend
            if mask.any():
                df.loc[mask, 'status'] = new_status
                df.to_csv(self.csv_file, index=False)
                print(f"✅ Updated status for '{trend}' to '{new_status}'")
                return True
            else:
                print(f"❌ Trend not found: {trend}")
                return False
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return False
    
    def get_pending_reviews(self):
        """Get all trends pending review"""
        try:
            df = pd.read_csv(self.csv_file)
            pending = df[df['status'] == 'Pending Review']
            return pending.to_dict('records')
        except:
            return []
    
    def get_approved_content(self):
        """Get all approved content"""
        try:
            df = pd.read_csv(self.csv_file)
            approved = df[df['status'] == 'Approved']
            return approved.to_dict('records')
        except:
            return []
