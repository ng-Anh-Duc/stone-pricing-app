def show_data_sync_sidebar():
    """Add data sync controls to Streamlit sidebar"""
    with st.sidebar:
        st.markdown("### 📊 Data Management")

        info = get_data_info()
        if info:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows", f"{info['row_count']:,}")
            with col2:
                if info.get("last_synced"):
                    try:
                        last_sync = datetime.strptime(info["last_synced"], "%Y-%m-%d %H:%M:%S")
                        hours_ago = (datetime.now() - last_sync).total_seconds() / 3600
                        if hours_ago < 1:
                            time_str = "< 1 hour ago"
                        elif hours_ago < 24:
                            time_str = f"{int(hours_ago)} hours ago"
                        else:
                            time_str = f"{int(hours_ago/24)} days ago"
                        st.metric("Last Sync", time_str)
                    except:
                        st.metric("Last Sync", "Unknown")
                else:
                    st.metric("Last Sync", "Never")

        # Check secrets availability
        if "google_credentials" in st.secrets and "GOOGLE_SPREADSHEET_ID" in st.secrets:
            if st.button("🔄 Sync from Google Sheets", use_container_width=True):
                try:
                    with st.spinner("Syncing data from Google Sheets..."):
                        sync = GoogleSheetsSync()  # 👈 now auto-uses st.secrets
                        success = sync.sync()
                    if success:
                        st.success("✅ Data synced successfully!")
                        force_reload_data()
                        st.rerun()
                    else:
                        st.error("❌ Sync failed. Check logs.")
                except Exception as e:
                    st.error(f"❌ Sync error: {str(e)}")
        else:
            st.warning("⚠️ Google Sheets sync not configured")
            with st.expander("Setup Instructions"):
                st.markdown("""
                To enable Google Sheets sync:
                1. Add `GOOGLE_SPREADSHEET_ID` to your Streamlit secrets
                2. Add `[google_credentials]` block with your service account
                """)
