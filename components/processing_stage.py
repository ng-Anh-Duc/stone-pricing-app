# components/processing_stage.py
"""Processing stage component for the Stone Price Predictor app."""

import time
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression
import pandas as pd

from utils.data_loader import filter_data
from utils.scoring import calculate_priority_score
from utils.ui_helpers import stream_text, calculate_prediction_results, format_prediction_text
from config.settings import UI_CONFIG

def apply_price_transformation(raw_price):
    """Apply the price transformation formula: (output + 8) * 10 / 0.8"""
    return raw_price + (7 * 10) / 0.8

def create_scatter_plot(filtered_df):
    """Create scatter plot with prediction line."""
    fig = go.Figure()
    
    # Add scatter points
    fig.add_trace(go.Scatter(
        x=filtered_df['priority_score'],
        y=filtered_df['usd_m3'],
        mode='markers',
        marker=dict(size=10, color='blue', opacity=0.6),
        text=filtered_df['product_code'],
        hovertemplate='<b>%{text}</b><br>Priority Score: %{x}<br>Price: $%{customdata:.2f}/m²',
        customdata=filtered_df['usd_m2'],
        name='Products'
    ))
    
    # Add linear regression line if we have enough data
    if len(filtered_df) > 1 and not filtered_df['usd_m3'].isna().all():
        clean_data = filtered_df.dropna(subset=['priority_score', 'W', 'L', 'usd_m3'])
        if len(clean_data) > 3:
            lr = LinearRegression()
            X = clean_data[['priority_score', 'W', 'L']]
            y = clean_data['usd_m3']
            lr.fit(X, y)

            # Store the model in session state for later use
            st.session_state.price_model = lr
            st.session_state.model_features = ['priority_score', 'W', 'L']

            # For visualization, we'll show the prediction line at average W and L values
            avg_width = clean_data['W'].mean()
            avg_length = clean_data['L'].mean()
            
            x_line = np.linspace(clean_data['priority_score'].min(), 
                               clean_data['priority_score'].max(), 100)
            # Create feature matrix for prediction with average W and L
            X_pred = np.column_stack([
                x_line,
                np.full_like(x_line, avg_width),
                np.full_like(x_line, avg_length)
            ])
            y_line = lr.predict(X_pred)
            
            fig.add_trace(go.Scatter(
                x=x_line,
                # y=np.interp(y_line, sorted(clean_data['usd_m2']), range(len(clean_data))),
                y = y_line,
                mode='lines',
                line=dict(color='red', dash='dash', width=2),
                name=f'Prediction Line (W={avg_width:.1f}, L={avg_length:.1f})',
                hovertemplate='Priority Score: %{x}<br>Predicted Price: $%{y:.2f}/m²'
            ))

            # Add R² score as annotation
            r2_score = lr.score(X, y)
            fig.add_annotation(
                x=0.05, y=0.95,
                xref="paper", yref="paper",
                text=f"R² = {r2_score:.3f}<br>Model: Price ~ Priority + Width + Length",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1
            )
    
    fig.update_layout(
        title="Priority Score vs Product Analysis",
        xaxis_title="Priority Score",
        yaxis_title="Price (USD/m³)",
        height=500,
        template="plotly_white"
    )
    
    return fig

def render_processing_stage(df):
    """Render the processing stage of the application."""
    with st.container():
        st.markdown('<div class="ai-response">', unsafe_allow_html=True)
        
        # Streaming response 1
        stream_container1 = st.empty()
        stream_text("Analyzing your requirements...", stream_container1)
        time.sleep(UI_CONFIG["sleep_time"])
        
        # Streaming response 2
        stream_container2 = st.empty()
        stream_text(f"Filtering database for {st.session_state.stone_type} stones with {st.session_state.processing_type} processing...", stream_container2)
        time.sleep(UI_CONFIG["sleep_time"])
        
        # Filter data
        filtered_df = filter_data(
            df, 
            st.session_state.stone_type,
            st.session_state.processing_type,
            st.session_state.height
        )
        
        stream_container3 = st.empty()
        stream_text(f"Found {len(filtered_df)} matching products in database", stream_container3)
        st.markdown('</div>', unsafe_allow_html=True)
        
        time.sleep(UI_CONFIG["sleep_time"])
        
        if len(filtered_df) > 0:
            # Calculate priority scores
            filtered_df = calculate_priority_score(
                filtered_df, 
                st.session_state.stone_type, 
                st.session_state.processing_type, 
                st.session_state.height,
                st.session_state.width,
                st.session_state.length
            )
            st.session_state.filtered_data = filtered_df
            
            # Show filtered table
            st.markdown("### Filtered Product Database")
            st.dataframe(
                filtered_df[['product_code', 'loai_da', 'gia_cong', 'H', 'W', 'L', 'usd_m3', 'priority_score']], 
                use_container_width=True
            )
            
            # AI continues analysis
            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
            stream_container4 = st.empty()
            stream_text("Computing priority scores and preparing predictive analysis...", stream_container4)
            time.sleep(UI_CONFIG["sleep_time"])
            
            stream_container5 = st.empty()
            stream_text("Generating linear regression model for price prediction...", stream_container5)
            time.sleep(UI_CONFIG["sleep_time"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Create and display scatter plot
            fig = create_scatter_plot(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Price prediction
            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
            stream_container6 = st.empty()
            
            # prediction_results = calculate_prediction_results(filtered_df)
            # if prediction_results:
            #     prediction_text = format_prediction_text(prediction_results, len(filtered_df))
            #     stream_text(prediction_text, stream_container6)
            #     st.session_state.prediction_results = prediction_results
            # else:
            #     stream_text("Insufficient price data for accurate prediction", stream_container6)
            
            # st.markdown('</div>', unsafe_allow_html=True)
            # time.sleep(2)

            # Calculate prediction using the stored model if available
            if hasattr(st.session_state, 'price_model') and st.session_state.width and st.session_state.length:
                # Calculate priority score for the input dimensions
                input_priority = filtered_df['priority_score'].max()  # Use max priority as reference
                
                # Predict price for the specific input dimensions
                X_input = pd.DataFrame({
                    'priority_score': [input_priority],
                    'W': [st.session_state.width],
                    'L': [st.session_state.length]
                })
                predicted_price = st.session_state.price_model.predict(X_input)[0]
                # Apply the transformation formula
                final_predicted_price = apply_price_transformation(predicted_price)

                prediction_text = f"""🤖 Based on multi-linear regression analysis:
                
For your specific stone ({st.session_state.stone_type}, {st.session_state.processing_type}):
- Height: {st.session_state.height}cm
- Width: {st.session_state.width}cm  
- Length: {st.session_state.length}cm
- Priority Score: {input_priority:.1f}

**Predicted Price: ${final_predicted_price:.2f}/m³**

The model considers priority score, width, and length to provide a more accurate prediction."""
                
                stream_text(prediction_text, stream_container6)
                st.session_state.predicted_price = predicted_price
            else:
                prediction_results = calculate_prediction_results(filtered_df)
                if prediction_results:
                    prediction_text = format_prediction_text(prediction_results, len(filtered_df))
                    stream_text(prediction_text, stream_container6)
                    st.session_state.prediction_results = prediction_results
                else:
                    stream_text("Insufficient price data for accurate prediction", stream_container6)
            
            st.markdown('</div>', unsafe_allow_html=True)
            time.sleep(2)