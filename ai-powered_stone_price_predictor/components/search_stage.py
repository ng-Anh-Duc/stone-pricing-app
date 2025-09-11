# components/search_stage.py
"""Exact search stage component for the Stone Price Predictor app."""

import streamlit as st
from utils.data_loader import filter_data

def render_search_stage(df):
    """Render the exact search stage of the application."""
    st.markdown('<div class="ai-response">', unsafe_allow_html=True)
    st.markdown("**Please specify exact dimensions for precise product matching:**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        width = st.number_input("Width (cm)", min_value=0.1, max_value=100.0, value=15.0, step=0.1)
    
    with col2:
        length = st.number_input("Length (cm)", min_value=0.1, max_value=100.0, value=15.0, step=0.1)
    
    with col3:
        st.write("")  # Spacing
        if st.button("Search Exact Match", use_container_width=True):
            st.session_state.width = width
            st.session_state.length = length
            
            # Find exact matches
            exact_matches = filter_data(
                df,
                st.session_state.stone_type,
                st.session_state.processing_type,
                st.session_state.height,
                width,
                length
            )
            
            st.session_state.exact_matches = exact_matches
            st.session_state.stage = 'report'
            st.rerun()