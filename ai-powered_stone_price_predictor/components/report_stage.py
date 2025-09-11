# components/report_stage.py
"""Report stage component for the Stone Price Predictor app."""

import streamlit as st
from datetime import datetime
from utils.ui_helpers import reset_session_state

def generate_report_text(current_time):
    """Generate report text for download."""
    report_text = f"Stone Price Analysis Report\nGenerated: {current_time}\n\n"
    report_text += f"Specifications:\n- Stone: {st.session_state.stone_type}\n"
    report_text += f"- Processing: {st.session_state.processing_type}\n"
    report_text += f"- Height: {st.session_state.height}cm\n\n"
    
    if st.session_state.prediction_results:
        report_text += f"Predicted Price: ${st.session_state.prediction_results['avg_price']:.2f}/m²"
    else:
        report_text += "No prediction available"
    
    return report_text

def render_report_stage():
    """Render the report stage of the application."""
    st.markdown("## Comprehensive Price Analysis Report")
    
    # Report header
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**Generated:** {current_time}")
    st.markdown("---")
    
    # Product specifications
    st.markdown('<div class="report-section">', unsafe_allow_html=True)
    st.markdown("### Product Specifications")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Stone Type:** {st.session_state.stone_type}")
        st.markdown(f"**Processing:** {st.session_state.processing_type}")
    with col2:
        st.markdown(f"**Height:** {st.session_state.height} cm")
        if hasattr(st.session_state, 'width'):
            st.markdown(f"**Width:** {st.session_state.width} cm")
            st.markdown(f"**Length:** {st.session_state.length} cm")
    with col3:
        if st.session_state.prediction_results:
            st.markdown(f"**Confidence:** {st.session_state.prediction_results['confidence']}%")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Price prediction summary
    if st.session_state.prediction_results:
        st.markdown('<div class="prediction-container">', unsafe_allow_html=True)
        st.markdown("### Price Prediction Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Price", f"${st.session_state.prediction_results['avg_price']:.2f}/m²")
        with col2:
            st.metric("Min Price", f"${st.session_state.prediction_results['min_price']:.2f}/m²")
        with col3:
            st.metric("Max Price", f"${st.session_state.prediction_results['max_price']:.2f}/m²")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show exact matches if found
    if hasattr(st.session_state, 'exact_matches') and len(st.session_state.exact_matches) > 0:
        st.markdown("### Exact Product Matches")
        st.success(f"Found {len(st.session_state.exact_matches)} exact matches!")
        st.dataframe(
            st.session_state.exact_matches[['loai_da', 'gia_cong', 'H', 'W', 'L', 'usd_pc', 'usd_m2', 'usd_m3', 'usd_ton']], 
            use_container_width=True
        )
    
    # Show filtered data table
    if st.session_state.filtered_data is not None:
        st.markdown("### Similar Products Database")
        st.dataframe(
            st.session_state.filtered_data[['loai_da', 'gia_cong', 'H', 'W', 'L', 'usd_m2']], 
            use_container_width=True
        )
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Analysis"):
            reset_session_state()
            st.rerun()
    
    with col2:
        if st.button("Export Report"):
            report_data = generate_report_text(current_time)
            st.download_button(
                label="Download Analysis Report",
                data=report_data,
                file_name=f"stone_analysis_{current_time.replace(':', '-').replace(' ', '_')}.txt",
                mime="text/plain"
            )