"""Priority scoring utilities for the Stone Price Predictor app."""

import pandas as pd
import re
from config.settings import SCORING_CONFIG

def generate_product_code(row, index):
    """Generate unique product codes."""
    stone_code = ''.join([c for c in str(row['loai_da'])[:3].upper() if c.isalpha()])
    processing_code = ''.join([c for c in str(row['gia_cong'])[:2].upper() if c.isalpha()])
    size_code = f"{int(row['H'])}{int(row['W'])}{int(row['L'])}"
    return f"{stone_code}-{processing_code}-{size_code}-{index:03d}"

def normalize_stone_name(stone_name):
    """Normalize stone names for comparison"""
    if pd.isna(stone_name):
        return ""
    normalized = str(stone_name).strip().upper()
    normalized = re.sub(r'\s+', ' ', normalized)  # Replace multiple spaces with single space
    return normalized

def get_stone_base_type(stone_name):
    """Extract the base stone type (BAZAN, BLUESTONE, GRANITE, etc.)"""
    normalized = normalize_stone_name(stone_name)
    base_types = ['BAZAN', 'BLUESTONE', 'GRANITE']
    
    for base_type in base_types:
        if normalized.startswith(base_type):
            return base_type
    
    return normalized.split()[0] if normalized.split() else normalized

def calculate_priority_score(df, stone_type, processing_type, height, width=None, length=None):
    """
    Enhanced priority scoring with robust string matching
    """
    # Normalize input stone name
    input_stone = normalize_stone_name(stone_type)
    input_base_type = get_stone_base_type(input_stone)
    
    # Normalize input processing
    input_processing = normalize_stone_name(processing_type)
    
    # Stone type matching logic
    da_map = {
        'Ư1': lambda x: normalize_stone_name(x) == input_stone,  # Exact match after normalization
        'Ư2': lambda x: (
            get_stone_base_type(x) == input_base_type and  # Same base stone type
            normalize_stone_name(x) != input_stone  # But not exactly the same
        ),
        'Ư3': lambda x: True  # Any stone (fallback)
    }
    
    # Processing method matching
    gc_map = {
        'Ư1': lambda x: normalize_stone_name(x) == input_processing,  # Exact match after normalization
        'Ư2': lambda x: True  # Any processing method
    }
    
    # Height matching
    cao_map = {
        'Ư1': lambda v: abs(float(v) - height) < 0.01,
        'Ư2': lambda v: abs(float(v) - height) <= 1.0,
        'Ư3': lambda v: abs(float(v) - height) <= 2.0
    }
    
    # Width matching (if provided)
    rong_map = {
        'Ư1': lambda v: abs(float(v) - width) < 0.01,
        'Ư2': lambda v: abs(float(v) - width) <= 5.0,
        'Ư3': lambda v: abs(float(v) - width) <= 10.0
    } if width is not None else {}
    
    # Length matching (if provided)
    dai_map = {
        'Ư1': lambda v: abs(float(v) - length) < 0.01,
        'Ư2': lambda v: abs(float(v) - length) <= 10.0,
        'Ư3': lambda v: abs(float(v) - length) <= 20.0
    } if length is not None else {}

    def score_row(r):
        s = 0
        stone_score = 0
        processing_score = 0
        
        # Stone type scoring with proper base type checking
        for lvl, fn in da_map.items():
            try:
                if fn(r['loai_da']):
                    stone_score = {'Ư1': 30, 'Ư2': 25, 'Ư3': 20}[lvl]
                    s += stone_score
                    break
            except:
                continue
                
        # Processing method scoring
        for lvl, fn in gc_map.items():
            try:
                if fn(r['gia_cong']):
                    processing_score = {'Ư1': 20, 'Ư2': 15}[lvl]
                    s += processing_score
                    break
            except:
                continue
                
        # Height scoring (with error handling)
        for lvl, fn in cao_map.items():
            try:
                if pd.notna(r['H']) and fn(r['H']):
                    s += {'Ư1': 15, 'Ư2': 12, 'Ư3': 9}[lvl]
                    break
            except:
                continue
        
        # Width scoring (if width provided)
        if width is not None:
            for lvl, fn in rong_map.items():
                try:
                    if pd.notna(r['W']) and fn(r['W']):
                        s += {'Ư1': 9, 'Ư2': 6, 'Ư3': 3}[lvl]
                        break
                except:
                    continue
        
        # Length scoring (if length provided)
        if length is not None:
            for lvl, fn in dai_map.items():
                try:
                    if pd.notna(r['L']) and fn(r['L']):
                        s += {'Ư1': 3, 'Ư2': 2, 'Ư3': 1}[lvl]
                        break
                except:
                    continue
                
        return s

    df['priority_score'] = df.apply(score_row, axis=1)
    
    # Add product codes
    df['product_code'] = [generate_product_code(row, i) 
                         for i, (_, row) in enumerate(df.iterrows())]
    
    # Add detailed scoring breakdown for debugging
    def get_match_type(row):
        row_stone = normalize_stone_name(row['loai_da'])
        if input_stone == row_stone:
            return 'Exact Match'
        elif get_stone_base_type(row['loai_da']) == input_base_type:
            return f'Same Base Type ({input_base_type})'
        else:
            return f'Different Stone Type ({get_stone_base_type(row["loai_da"])})'
    
    df['stone_match_type'] = df.apply(get_match_type, axis=1)
    
    return df.sort_values('priority_score', ascending=False)