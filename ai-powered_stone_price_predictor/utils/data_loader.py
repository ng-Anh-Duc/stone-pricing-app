# utils/data_loader.py
"""Data loading utilities for the Stone Price Predictor app."""

import pandas as pd
import streamlit as st
from config.settings import DATA_CONFIG

@st.cache_data
def load_data():
    """Load and preprocess the stone price data."""
    try:
        df = pd.read_csv(DATA_CONFIG["csv_file"])
        df = df.rename(columns=DATA_CONFIG["column_mapping"])
        
        # Convert numeric columns
        for col in DATA_CONFIG["numeric_columns"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error(f"Data file not found: {DATA_CONFIG['csv_file']}")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

def get_unique_values(df, column):
    """Get sorted unique values from a dataframe column."""
    return sorted(df[column].dropna().unique())

def filter_data(df, stone_type, processing_type, height, width=None, length=None):
    """Filter dataframe based on given criteria."""
    mask = (
        (df['loai_da'] == stone_type) &
        (df['gia_cong'] == processing_type) &
        (df['H'] == height)
    )
    
    if width is not None:
        mask &= (df['W'] == width)
    
    if length is not None:
        mask &= (df['L'] == length)
    
    return df[mask].copy()