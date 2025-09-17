import streamlit as st
import json
import os
from pathlib import Path

def get_credentials():
    """Get credentials from Streamlit secrets or local file"""
    if 'google_credentials' in st.secrets:
        # Running on Streamlit Cloud
        creds_dict = dict(st.secrets["google_credentials"])
        
        # Write to temporary file for google-auth
        creds_path = Path("/tmp/credentials.json")
        with open(creds_path, 'w') as f:
            json.dump(creds_dict, f)
        
        return str(creds_path)
    else:
        # Running locally
        return os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

def get_spreadsheet_id():
    """Get spreadsheet ID from Streamlit secrets or env"""
    if 'GOOGLE_SPREADSHEET_ID' in st.secrets:
        return st.secrets['GOOGLE_SPREADSHEET_ID']
    else:
        return os.getenv('GOOGLE_SPREADSHEET_ID')