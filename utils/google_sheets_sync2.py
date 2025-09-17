import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from datetime import datetime
import logging
from pathlib import Path
import shutil
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsSync:
    def __init__(self, credentials_path=None, spreadsheet_id=None):
        """Initialize Google Sheets sync with credentials and spreadsheet ID"""
        # Get from environment variables if not provided
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SPREADSHEET_ID')
        
        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID must be set")
        
        self.service = self._authenticate()
        
        # Set up data directories
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data'
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            service = build('sheets', 'v4', credentials=creds)
            logger.info("Successfully authenticated with Google Sheets API")
            return service
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def verify_spreadsheet(self):
        """Verify that the spreadsheet ID points to a valid Google Sheets document"""
        try:
            # Try to get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            logger.info(f"Spreadsheet title: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
            
            # List all sheets
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            logger.info(f"Available sheets: {sheet_names}")
            
            return True, sheet_names
        except Exception as e:
            logger.error(f"Failed to verify spreadsheet: {e}")
            return False, str(e)

    def download_sheet(self, sheet_name='cPhuong_last_check'):
        """Download specific sheet from Google Sheets"""
        try:
            sheet = self.service.spreadsheets()
            
            # Get the data
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning(f"No data found in sheet: {sheet_name}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # Save raw data with timestamp

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            raw_file = self.data_dir / f"{sheet_name}_raw_{timestamp}.csv"
            df.to_csv(raw_file, index=False)
            logger.info(f"Downloaded raw data to: {raw_file}")
            
            return df
        except Exception as e:
            logger.error(f"Failed to download sheet: {e}")
            raise
    
    def save_latest_data(self, df, filename='cPhuong_last_check_1.csv'):
        """Save raw data as the latest version for the app to use"""
        try:
            # Save as latest_data.csv in data directory
            latest_file = self.data_dir / 'latest_data.csv'
            df.to_csv(latest_file, index=False)
            logger.info(f"Saved latest data to: {latest_file}")
            
            # Also save with the original filename for backward compatibility
            root_file = self.base_dir / filename
            shutil.copy2(latest_file, root_file)
            logger.info(f"Updated root data file: {root_file}")
            
            return latest_file
        except Exception as e:
            logger.error(f"Failed to save latest data: {e}")
            raise
    
    def sync(self, sheet_name='cPhuong_last_check'):
        """Complete sync process: download and save raw data"""
        try:
            logger.info(f"Starting sync for sheet: {sheet_name}")
            
            # Verify spreadsheet first
            is_valid, result = self.verify_spreadsheet()
            if not is_valid:
                logger.error(f"Invalid spreadsheet: {result}")
                return False
            
            # Check if sheet exists
            if sheet_name not in result:
                logger.error(f"Sheet '{sheet_name}' not found. Available sheets: {result}")
                return False
        
            # Download raw data
            df = self.download_sheet(sheet_name)
            if df is None:
                return False
            
            # Save as latest data (no processing here)
            self.save_latest_data(df)
            
            logger.info("Sync completed successfully")
            return True
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False
    
    def cleanup_old_files(self, days_to_keep=7):
        """Remove old raw files to save space"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for file_path in self.raw_dir.glob('*.csv'):
                if file_path.stat().st_mtime < cutoff_date:
                    file_path.unlink()
                    logger.info(f"Removed old file: {file_path}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")