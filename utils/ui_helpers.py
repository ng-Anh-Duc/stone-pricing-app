# utils/ui_helpers.py
"""UI helper functions for the Stone Price Predictor app."""

import time
import streamlit as st
from config.settings import UI_CONFIG

def stream_text(text, container, delay=None):
    """Simulate streaming text output."""
    if delay is None:
        delay = UI_CONFIG["streaming_delay"]
    
    placeholder = container.empty()
    displayed_text = ""
    
    for char in text:
        displayed_text += char
        placeholder.markdown(
            f'<div class="streaming-text">{displayed_text}▋</div>', 
            unsafe_allow_html=True
        )
        time.sleep(delay)
    
    placeholder.markdown(
        f'<div class="streaming-text">{displayed_text}</div>', 
        unsafe_allow_html=True
    )

def initialize_session_state():
    """Initialize all session state variables."""
    if 'stage' not in st.session_state:
        st.session_state.stage = 'input'
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = None
    if 'prediction_results' not in st.session_state:
        st.session_state.prediction_results = None

def reset_session_state():
    """Reset session state for new analysis."""
    for key in list(st.session_state.keys()):
        if key != 'stage':
            del st.session_state[key]
    st.session_state.stage = 'input'

def calculate_prediction_results(filtered_df):
    """Calculate prediction results from filtered data."""
    valid_prices = filtered_df['usd_m3'].dropna()
    
    if len(valid_prices) == 0:
        return None
    
    return {
        'avg_price': valid_prices.mean(),
        'min_price': valid_prices.min(),
        'max_price': valid_prices.max(),
        'confidence': min(95, len(valid_prices) * 10)
    }

def format_prediction_text(prediction_results, num_products):
    """Format prediction text for display."""
    method = prediction_results.get('method', 'unknown')
    
    if method == 'multiple_linear_regression':
        r2_score = prediction_results.get('r2_score', 0)
        text = f"💰 Multiple Linear Regression Analysis ({num_products} products):\n\n"
        text += f"   • Model R² Score: {r2_score:.3f} (explains {r2_score*100:.1f}% of price variance)\n"
        text += f"   • Predicted Price Range: ${prediction_results['min_price']:.2f} - ${prediction_results['max_price']:.2f} USD/m³\n"
        text += f"   • Average Predicted Price: ${prediction_results['avg_price']:.2f} USD/m³\n"
        text += f"   • Model Confidence: {prediction_results['confidence']:.0f}%\n\n"
        
        # Add coefficient information
        coef = prediction_results.get('coefficients', {})
        text += f"   • Length Impact: ${coef.get('length', 0):.2f}/cm\n"
        text += f"   • Width Impact: ${coef.get('width', 0):.2f}/cm\n"
        text += f"   • Height Impact: ${coef.get('height', 0):.2f}/cm"
    
    elif method == 'statistical':
        text = f"💰 Statistical Analysis ({num_products} products):\n\n"
        text += f"   • Price Range: ${prediction_results['min_price']:.2f} - ${prediction_results['max_price']:.2f} USD/m³\n"
        text += f"   • Average Price: ${prediction_results['avg_price']:.2f} USD/m³\n"
        text += f"   • Confidence: {prediction_results['confidence']:.0f}%\n"
        text += f"   • Note: Insufficient data for regression modeling"
    
    else:
        text = f"💰 Fallback Analysis ({num_products} products):\n\n"
        text += f"   • Price Range: ${prediction_results['min_price']:.2f} - ${prediction_results['max_price']:.2f} USD/m³\n"
        text += f"   • Average Price: ${prediction_results['avg_price']:.2f} USD/m³\n"
        text += f"   • Confidence: {prediction_results['confidence']:.0f}%"
    
    return text