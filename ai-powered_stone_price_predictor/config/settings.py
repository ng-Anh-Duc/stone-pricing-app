# config/settings.py
"""Configuration settings for the Stone Price Predictor app."""

import streamlit as st

# Page Configuration
PAGE_CONFIG = {
    "page_title": "AI Stone Price Predictor",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Data Configuration
DATA_CONFIG = {
    "csv_file": "cPhuong_last_check_1.csv",
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

# UI Configuration
UI_CONFIG = {
    "streaming_delay": 0.03,
    "sleep_time": 1,
    "theme_color": "#fabc14",
    "background_dark": "#1a1a1a",
    "background_darker": "#0a0a0a"
}

# Scoring Configuration
SCORING_CONFIG = {
    "stone_match_exact": 40,
    "stone_match_partial": 30,
    "stone_match_none": 10,
    "processing_match_exact": 30,
    "processing_match_partial": 20,
    "processing_match_none": 5,
    "height_match_perfect": 30,
    "height_match_1cm": 25,
    "height_match_2cm": 20,
    "height_match_5cm": 15,
    "height_match_default": 5
}

# Session State Keys
SESSION_KEYS = [
    'stage', 'filtered_data', 'prediction_results',
    'stone_type', 'processing_type', 'height',
    'width', 'length', 'exact_matches'
]