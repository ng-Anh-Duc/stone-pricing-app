import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import logging
from pathlib import Path
from datetime import datetime
import streamlit as st  # 👈 used for secrets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheetsSync:
    def __init__(self, credentials=None, file_id=None):
        """Initialize Google Drive/Sheets sync"""
        # Use Streamlit secrets if not passed explicitly
        self.credentials_info = credentials or dict(st.secrets["google_credentials"])
        self.file_id = file_id or st.secrets.get("GOOGLE_SPREADSHEET_ID")

        if not self.file_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID must be set in Streamlit secrets")

        self.drive_service, self.sheets_service = self._authenticate()

        # Local data directory
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _authenticate(self):
        """Authenticate with Google APIs using service account"""
        try:
            creds = service_account.Credentials.from_service_account_info(
                self.credentials_info,
                scopes=[
                    "https://www.googleapis.com/auth/drive.readonly",
                    "https://www.googleapis.com/auth/spreadsheets.readonly",
                ],
            )
            drive_service = build("drive", "v3", credentials=creds)
            sheets_service = build("sheets", "v4", credentials=creds)
            logger.info("✅ Successfully authenticated with Google APIs")
            return drive_service, sheets_service
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise

    def download_excel_from_drive(self):
        """Download Excel file from Google Drive by file_id"""
        try:
            file_metadata = self.drive_service.files().get(
                fileId=self.file_id, fields="name,mimeType"
            ).execute()

            logger.info(f"⬇️ Downloading file: {file_metadata['name']}")
            logger.info(f"📂 File type: {file_metadata['mimeType']}")

            request = self.drive_service.files().get_media(fileId=self.file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Progress: {int(status.progress() * 100)}%")

            file_content.seek(0)
            df = pd.read_excel(file_content, sheet_name=0)

            logger.info(f"✅ Loaded {len(df)} rows from Excel file")
            return df

        except Exception as e:
            logger.error(f"❌ Failed to download Excel file: {e}")
            raise

    def save_latest_data(self, df, filename="latest_data.csv"):
        """Save data as CSV (latest + timestamped snapshot)"""
        try:
            latest_file = self.data_dir / filename
            df.to_csv(latest_file, index=False)
            logger.info(f"💾 Saved latest data to: {latest_file}")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_with_ts = df.copy()
            df_with_ts["last_updated"] = timestamp

            snapshot_file = self.data_dir / f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df_with_ts.to_csv(snapshot_file, index=False)

            return latest_file
        except Exception as e:
            logger.error(f"❌ Failed to save latest data: {e}")
            raise

    def sync(self):
        """Download Excel file and save as CSV"""
        try:
            logger.info(f"🔄 Starting sync for file: {self.file_id}")
            df = self.download_excel_from_drive()

            if df is None or df.empty:
                logger.error("⚠️ No data downloaded")
                return False

            self.save_latest_data(df)
            logger.info("✅ Sync completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return False
