#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.google_sheets_sync import GoogleSheetsSync
import logging
from datetime import datetime
import os

# Set up logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'sync_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the daily update process"""
    try:
        logger.info("Starting daily data sync")
        
        # Initialize sync
        sync = GoogleSheetsSync()
        
        # Run sync
        success = sync.sync()
        
        if success:
            # Clean up old files (keep last 7 days)
            try:
                sync.cleanup_old_files(days_to_keep=7)
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
            logger.info("Daily sync completed successfully")
            return 0
        else:
            logger.error("Daily sync failed")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
