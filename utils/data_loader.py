"""Data loading utilities for the Stone Price Predictor app."""

import pandas as pd
import streamlit as st
from pathlib import Path
import os
import logging

# Import config with error handling
try:
    from config.settings import DATA_CONFIG
except ImportError:
    # Fallback config if settings file is not available
    DATA_CONFIG = {
        "csv_file": "latest_data.csv",
        "column_mapping": {
            'LOẠI ĐÁ': 'loai_da',
            'CÁCH GIA CÔNG': 'gia_cong',
            'Mô tả Sản Phẩm': 'mo_ta',
            'Đơn giá': 'don_gia',
            'USD/PC': 'usd_pc',
            'USD/M2': 'usd_m2',
            'USD/M3': 'usd_m3',
            'USD/TON': 'usd_ton',
            'Year': 'year',
            'H': 'H',
            'W': 'W',
            'L': 'L',
        },
        "numeric_columns": ['L', 'W', 'H', 'usd_pc', 'usd_m2', 'usd_m3', 'usd_ton']
    }

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data loading with auto-reload capability"""
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self._data = None
        self._last_modified = None
        self._data_path = None
        self._find_data_file()

    def _find_data_file(self):
        """Find the most appropriate data file"""
        # Priority order for finding data
        possible_paths = [
            self.base_dir / 'data' / 'latest_data.csv',
            self.base_dir / 'latest_data.csv',
            self.base_dir / 'data' / DATA_CONFIG.get("csv_file", "latest_data.csv"),
            self.base_dir / DATA_CONFIG.get("csv_file", "latest_data.csv")
        ]
        
        for path in possible_paths:
            if path.exists():
                self._data_path = path
                logger.info(f"Using data file: {self._data_path}")
                return
        
        logger.warning("No data file found in expected locations")

    def _should_reload(self):
        """Check if data should be reloaded"""
        if not self._data_path or not self._data_path.exists():
            return True  # Always try to load if no valid path
        
        try:
            current_modified = os.path.getmtime(self._data_path)
            return self._data is None or current_modified != self._last_modified
        except OSError:
            return True

    def load_data(self, force_reload=False):
        """Load and preprocess the stone price data with auto-reload"""
        try:
            # If no file found, return empty dataframe
            if self._data_path is None:
                logger.warning("No data file available")
                return pd.DataFrame()
            
            if force_reload or self._should_reload():
                # Load the data
                df = pd.read_csv(self._data_path)
                
                # Only rename columns that exist
                existing_columns = {k: v for k, v in DATA_CONFIG["column_mapping"].items() 
                                    if k in df.columns}
                if existing_columns:
                    df = df.rename(columns=existing_columns)
                
                # Convert numeric columns
                for col in DATA_CONFIG["numeric_columns"]:
                    if col in df.columns:
                        # Handle various numeric formats
                        df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('$', '')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Update cache
                self._data = df
                if self._data_path.exists():
                    self._last_modified = os.path.getmtime(self._data_path)
                
                # Log info
                logger.info(f"Loaded {len(df)} rows from {self._data_path}")
                if 'last_updated' in df.columns and len(df) > 0:
                    logger.info(f"Data last synced: {df['last_updated'].iloc[0]}")
            
            return self._data if self._data is not None else pd.DataFrame()
            
        except FileNotFoundError:
            error_msg = f"Data file not found: {self._data_path}"
            logger.error(error_msg)
            return pd.DataFrame()
        except Exception as e:
            error_msg = f"Error loading data: {str(e)}"
            logger.error(error_msg)
            if self._data is not None:
                logger.warning("Using cached data")
                return self._data
            return pd.DataFrame()

    def get_data_info(self):
        """Get information about the loaded data"""
        if self._data is None:
            return None
        
        info = {
            'file_path': str(self._data_path) if self._data_path else 'Unknown',
            'last_modified': self._last_modified,
            'row_count': len(self._data),
            'columns': list(self._data.columns),
            'last_synced': None
        }
        
        if 'last_updated' in self._data.columns and len(self._data) > 0:
            info['last_synced'] = self._data['last_updated'].iloc[0]
        
        return info

# Create a singleton instance
_data_manager = DataManager()

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes to allow for updates
def load_data():
    """Load and preprocess the stone price data.
    
    This function maintains backward compatibility with the existing codebase
    while adding auto-reload capability for updated data.
    """
    return _data_manager.load_data()

def get_data_info():
    """Get information about the currently loaded data"""
    return _data_manager.get_data_info()

def force_reload_data():
    """Force reload the data (useful after manual sync)"""
    st.cache_data.clear()
    return _data_manager.load_data(force_reload=True)

def get_unique_values(df, column):
    """Get sorted unique values from a dataframe column."""
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().unique())

def filter_data(df, stone_type, processing_type, height, width=None, length=None):
    """Filter dataframe based on given criteria."""
    if df.empty:
        return df
    
    # Start with all data
    mask = pd.Series([True] * len(df))
    
    # Apply filters only if columns exist
    if 'loai_da' in df.columns:
        mask &= (df['loai_da'] == stone_type)
    
    if 'gia_cong' in df.columns:
        mask &= (df['gia_cong'] == processing_type)
    
    if 'H' in df.columns:
        mask &= (df['H'] == height)

    if width is not None and 'W' in df.columns:
        mask &= (df['W'] == width)

    if length is not None and 'L' in df.columns:
        mask &= (df['L'] == length)

    return df[mask].copy()