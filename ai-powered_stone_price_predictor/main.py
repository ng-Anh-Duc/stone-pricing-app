# main.py
"""
Main Streamlit application for AI Stone Price Predictor.
Entry point that orchestrates all components and manages application flow.
"""

import streamlit as st

# Import configuration
from config.settings import PAGE_CONFIG
from config.styles import get_custom_css, get_header_style

# Import utilities
from utils.data_loader import load_data
from utils.ui_helpers import initialize_session_state

# Import components
from components.input_stage import render_input_stage
from components.processing_stage import render_processing_stage
from components.search_stage import render_search_stage
from components.report_stage import render_report_stage

def main():
    """Main application function."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    # Initialize session state
    initialize_session_state()
    
    # Render header
    st.markdown(get_header_style(), unsafe_allow_html=True)
    
    # Route to appropriate stage based on session state
    if st.session_state.stage == 'input':
        render_input_stage(df)
    
    elif st.session_state.stage == 'processing':
        render_processing_stage(df)
    
    elif st.session_state.stage == 'exact_search':
        render_search_stage(df)
    
    elif st.session_state.stage == 'report':
        render_report_stage()
    
    else:
        # Fallback to input stage if unknown stage
        st.error("Unknown application stage. Resetting to input.")
        st.session_state.stage = 'input'
        st.rerun()

if __name__ == "__main__":
    main()