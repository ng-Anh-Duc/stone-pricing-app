# main.py
"""
Main Streamlit application for AI Stone Price Predictor.
Entry point that orchestrates all components and manages application flow.
"""

import streamlit as st
import os
from datetime import datetime

# Import configuration
from config.settings import PAGE_CONFIG
from config.styles import get_custom_css, get_header_style

# Import utilities
from utils.data_loader import load_data, get_data_info, force_reload_data
from utils.ui_helpers import initialize_session_state
from utils.google_sheets_sync import GoogleSheetsSync

# Import components
from components.input_stage import render_input_stage
from components.processing_stage import render_processing_stage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def show_data_sync_sidebar():
    """Add data sync controls to Streamlit sidebar"""
    with st.sidebar:
        st.markdown("### 📊 Data Management")
        
        # Show data info
        info = get_data_info()
        if info:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows", f"{info['row_count']:,}")
            with col2:
                if info.get('last_synced'):
                    # Parse and format the date
                    try:
                        last_sync = datetime.strptime(info['last_synced'], '%Y-%m-%d %H:%M:%S')
                        time_diff = datetime.now() - last_sync
                        hours_ago = time_diff.total_seconds() / 3600
                        
                        if hours_ago < 1:
                            time_str = "< 1 hour ago"
                        elif hours_ago < 24:
                            time_str = f"{int(hours_ago)} hours ago"
                        else:
                            days_ago = int(hours_ago / 24)
                            time_str = f"{days_ago} days ago"
                        
                        st.metric("Last Sync", time_str)
                    except:
                        st.metric("Last Sync", "Unknown")
                else:
                    st.metric("Last Sync", "Never")
        
        # Check if credentials exist before showing sync button
        credentials_exist = os.path.exists(os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json'))
        spreadsheet_id_set = bool(os.getenv('GOOGLE_SPREADSHEET_ID'))
        
        if credentials_exist and spreadsheet_id_set:
            # Sync button
            if st.button("🔄 Sync from Google Sheets", 
                        help="Download latest data from Google Sheets",
                        use_container_width=True):
                try:
                    with st.spinner("Syncing data from Google Sheets..."):
                        sync = GoogleSheetsSync()
                        success = sync.sync()
                        
                    if success:
                        st.success("✅ Data synced successfully!")
                        # Force reload the data
                        force_reload_data()
                        # Rerun to update the UI
                        st.rerun()
                    else:
                        st.error("❌ Sync failed. Check logs for details.")
                except Exception as e:
                    st.error(f"❌ Sync error: {str(e)}")
        else:
            # Show setup instructions
            st.warning("⚠️ Google Sheets sync not configured")
            with st.expander("Setup Instructions"):
                st.markdown("""
                To enable Google Sheets sync:
                1. Set up Google Sheets API credentials
                2. Add `GOOGLE_SPREADSHEET_ID` to your .env file
                3. Add `credentials.json` to your project root
                """)
        
        # Add info about automatic sync
        with st.expander("ℹ️ About Data Updates"):
            st.markdown("""
            - Data is automatically synced daily at 2 AM
            - Manual sync updates the data immediately
            - Raw data is downloaded and processed on-the-fly
            """)

def check_data_freshness():
    """Check if data is fresh and show warning if stale"""
    info = get_data_info()
    if info and info.get('last_synced'):
        try:
            last_sync = datetime.strptime(info['last_synced'], '%Y-%m-%d %H:%M:%S')
            hours_old = (datetime.now() - last_sync).total_seconds() / 3600
            
            # Only show warning if data is significantly old
            if hours_old > 48:
                st.warning(f"⚠️ Data is {int(hours_old/24)} days old. Consider syncing for latest updates.")
        except:
            pass

def main():
    """Main application function."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Show data sync controls in sidebar
    show_data_sync_sidebar()
    
    # Load data
    df = load_data()
    
    # Render header
    st.markdown(get_header_style(), unsafe_allow_html=True)
    
    # Check data freshness (optional - only shows warning if data is old)
    check_data_freshness()
    
    # Route to appropriate stage based on session state
    if st.session_state.stage == 'input':
        render_input_stage(df)
    
    elif st.session_state.stage == 'processing':
        render_processing_stage(df)
    
    # elif st.session_state.stage == 'exact_search':
    #     render_search_stage(df)
    
    # elif st.session_state.stage == 'report':
    #     render_report_stage()
    
    else:
        # Fallback to input stage if unknown stage
        st.error("Unknown application stage. Resetting to input.")
        st.session_state.stage = 'input'
        st.rerun()

if __name__ == "__main__":
    main()