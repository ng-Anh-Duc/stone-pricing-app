"""Input stage component for the Stone Price Predictor app."""

import streamlit as st
from utils.data_loader import get_unique_values

def render_input_stage(df):
    """Render the input stage of the application."""
    st.markdown("### AI Assistant: Ready for Price Analysis")
    st.markdown("Please provide the stone specifications for intelligent price prediction:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unique_stones = get_unique_values(df, 'loai_da')
        stone_options = [
            "BAZAN ĐEN", 
            "BAZAN XÁM",
            "BAZAN TỔ ONG",
            "BLUESTONE",
            "GRANITE",
            "GRANITE TRẮNG",
            "GRANITE HỒNG", 
            "GRANITE VÀNG",
            "GRANITE XÁM",
            "GRANITE ĐỎ"
        ]
        # Use either unique_stones OR stone_options, not both
        stone_type = st.selectbox("Stone Type", stone_options)
    
    with col2:
        unique_processing = get_unique_values(df, 'gia_cong')
        processing_type = st.selectbox("Processing Method", unique_processing)
    
    with col3:
        height = st.number_input("Height (cm)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
        width = st.number_input("Width (cm)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)
        length = st.number_input("Length (cm)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)
    
    # Add the button and state management
    if st.button("Start AI Analysis", use_container_width=True):
        st.session_state.stone_type = stone_type
        st.session_state.processing_type = processing_type
        st.session_state.height = height
        st.session_state.width = width
        st.session_state.length = length
        st.session_state.stage = 'processing'
        st.rerun()