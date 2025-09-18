"""
Main Streamlit application for AI Stone Price Predictor.
"""

import streamlit as st
from datetime import datetime
import logging
import pandas as pd

# Import utilities
from utils.data_loader import DataManager
from utils.google_sheets_sync import GoogleSheetsSync

# Import configuration
from config.settings import PAGE_CONFIG
from config.styles import get_custom_css, get_header_style
from utils.ui_helpers import initialize_session_state
from components.input_stage import render_input_stage
from components.processing_stage import render_processing_stage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DataManager
data_manager = DataManager()


def get_data_info(df: pd.DataFrame):
    """Return dataset info for sidebar display"""
    if df.empty:
        return {"row_count": 0, "last_synced": None}

    info = {"row_count": df.shape[0]}
    if "last_updated" in df.columns and not df["last_updated"].isna().all():
        info["last_synced"] = df["last_updated"].iloc[0]
    return info


def show_data_sync_sidebar():
    """Sidebar for data sync and info"""
    with st.sidebar:
        st.markdown("### 📊 Data Management")

        df = data_manager.load_data()
        info = get_data_info(df)
        st.metric("Rows", f"{info['row_count']:,}")
        st.metric("Last Sync", info["last_synced"] or "Unknown")

        if "google_credentials" in st.secrets and "GOOGLE_SPREADSHEET_ID" in st.secrets:
            if st.button("🔄 Sync from Google Drive", use_container_width=True):
                try:
                    with st.spinner("Syncing data from Google Drive..."):
                        sync = GoogleSheetsSync()
                        success = sync.sync()
                    if success:
                        st.success("✅ Data synced successfully!")
                        data_manager.load_data(force_reload=True)
                        st.rerun()
                    else:
                        st.error("❌ Sync failed. Check logs.")
                except Exception as e:
                    st.error(f"❌ Sync error: {str(e)}")
        else:
            st.warning("⚠️ Google sync not configured")
            with st.expander("Setup Instructions"):
                st.markdown("""
                To enable Google Sheets/Drive sync:
                1. Add `GOOGLE_SPREADSHEET_ID` to your Streamlit secrets
                2. Add `[google_credentials]` block with your service account JSON
                """)


def check_data_freshness():
    """Warn if data is stale"""
    df = data_manager.load_data()
    info = get_data_info(df)
    if info.get("last_synced"):
        try:
            last_sync = datetime.strptime(info["last_synced"], "%Y-%m-%d %H:%M:%S")
            hours_old = (datetime.now() - last_sync).total_seconds() / 3600
            if hours_old > 48:
                st.warning(f"⚠️ Data is {int(hours_old/24)} days old. Consider syncing.")
        except Exception:
            pass


def main():
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    initialize_session_state()

    # Sidebar
    show_data_sync_sidebar()

    # Load dataset
    df = data_manager.load_data()

    # Header
    st.markdown(get_header_style(), unsafe_allow_html=True)

    # Freshness warning
    check_data_freshness()

    # Stage routing
    if st.session_state.stage == 'input':
        render_input_stage(df)
    elif st.session_state.stage == 'processing':
        render_processing_stage(df)
    else:
        st.error("Unknown stage. Resetting...")
        st.session_state.stage = 'input'
        st.rerun()


if __name__ == "__main__":
    main()
