import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from datetime import datetime
import logging
from pathlib import Path
import shutil
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import io
from utils.secrets_handler import get_credentials, get_spreadsheet_id

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsSync:
    def __init__(self, credentials_path=None, file_id=None):
        """Initialize Google Drive sync for Excel files"""
        # Get from environment variables if not provided
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        # or get_credentials()
        self.file_id = file_id or os.getenv('GOOGLE_SPREADSHEET_ID')  # Actually a Drive file ID
        # or get_spreadsheet_id()
        
        if not self.file_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID must be set")
        
        self.drive_service, self.sheets_service = self._authenticate()
        
        # Set up data directories
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data'
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _authenticate(self):
        """Authenticate with Google Drive and Sheets APIs"""
        try:
            # Handle both file path and dict credentials
            if isinstance(self.credentials_path, dict):
                # Direct credentials dict (from Streamlit secrets)
                creds = service_account.Credentials.from_service_account_info(
                    dict(self.credentials_path),
                    scopes=[
                        'https://www.googleapis.com/auth/drive.readonly',
                        'https://www.googleapis.com/auth/spreadsheets.readonly'
                    ]
                )
            elif isinstance(self.credentials_path, str) and os.path.exists(self.credentials_path):
                # File path (local development)
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=[
                        'https://www.googleapis.com/auth/drive.readonly',
                        'https://www.googleapis.com/auth/spreadsheets.readonly'
                    ]
                )
            else:
                raise ValueError(f"Invalid credentials: {type(self.credentials_path)}")
                
            drive_service = build('drive', 'v3', credentials=creds)
            sheets_service = build('sheets', 'v4', credentials=creds)
            logger.info("Successfully authenticated with Google APIs")
            return drive_service, sheets_service
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def download_excel_from_drive(self):
        """Download Excel file from Google Drive"""
        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(
                fileId=self.file_id,
                fields='name,mimeType'
            ).execute()
            
            logger.info(f"Downloading file: {file_metadata['name']}")
            logger.info(f"File type: {file_metadata['mimeType']}")
            
            # Download the file
            request = self.drive_service.files().get_media(fileId=self.file_id)
            file_content = io.BytesIO()
            
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")
            
            # Reset the buffer position
            file_content.seek(0)
            
            # Read Excel file with pandas
            df = pd.read_excel(file_content, sheet_name=0)  # Read first sheet
            
            logger.info(f"Successfully loaded {len(df)} rows from Excel file")
            return df
            
        except Exception as e:
            logger.error(f"Failed to download Excel file: {e}")
            raise
    
    def save_latest_data(self, df, filename='latest_data.csv'):
        """Save data as CSV for the app to use"""
        try:
            # Save as latest_data.csv in data directory
            latest_file = self.data_dir / 'latest_data.csv'
            df.to_csv(latest_file, index=False)
            logger.info(f"Saved latest data to: {latest_file}")
            
            # Add timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df['last_updated'] = timestamp
            
            # Also save with timestamp for history
            timestamp_file = self.data_dir / f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(timestamp_file, index=False)
            
            return latest_file
        except Exception as e:
            logger.error(f"Failed to save latest data: {e}")
            raise
    
    def sync(self):
        """Download Excel file from Google Drive and save as CSV"""
        try:
            logger.info(f"Starting sync for Excel file: {self.file_id}")
            
            # Download Excel file from Drive
            df = self.download_excel_from_drive()
            
            if df is None or df.empty:
                logger.error("No data downloaded")
                return False
            
            # Save as CSV
            self.save_latest_data(df)
            
            logger.info("Sync completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False