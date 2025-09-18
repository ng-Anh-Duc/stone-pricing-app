import streamlit as st
import json
import os
from pathlib import Path

def get_credentials():
    """Get credentials from Streamlit secrets or local file"""
    if 'google_credentials' in st.secrets:
        # Running on Streamlit Cloud - return dict directly
        return dict(st.secrets["google_credentials"])
    else:
        # Running locally - return file path
        return os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

def get_spreadsheet_id():
    """Get spreadsheet ID from Streamlit secrets or env"""
    if 'GOOGLE_SPREADSHEET_ID' in st.secrets:
        return st.secrets['GOOGLE_SPREADSHEET_ID']
    else:
        return os.getenv('GOOGLE_SPREADSHEET_ID')