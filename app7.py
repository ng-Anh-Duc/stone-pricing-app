import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import time
import re
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="AI Stone Price Predictor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for automation UI
st.markdown("""
<style>
    .chat-container {
        background: #1a1a1a;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #fabc14;
        font-family: 'Courier New', monospace;
        border: 1px solid #fabc14;
    }
    
    .ai-response {
        background: #fabc14;
        border-left: 3px solid #fabc14;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #fabc14;
        font-family: 'Courier New', monospace;
    }
    
    .prediction-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .report-section {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .metric-highlight {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .stButton > button {
        background: #fabc14;
        color: black;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        font-family: 'Courier New', monospace;
    }
    
    .streaming-text {
        color: #fabc14;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# Load data function
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("cPhuong_last_check_1.csv")
        df = df.rename(columns={
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
        })
        
        # Convert numeric columns
        numeric_columns = ['L', 'W', 'H', 'usd_pc', 'usd_m2', 'usd_m3', 'usd_ton']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error("Data file not found: cPhuong_last_check_1.csv")
        st.stop()

# Auto-generate product codes
def generate_product_code(row, index):
    """Generate unique product codes"""
    stone_code = ''.join([c for c in str(row['loai_da'])[:3].upper() if c.isalpha()])
    processing_code = ''.join([c for c in str(row['gia_cong'])[:2].upper() if c.isalpha()])
    size_code = f"{int(row['H'])}{int(row['W'])}{int(row['L'])}"
    return f"{stone_code}-{processing_code}-{size_code}-{index:03d}"

# Priority scoring function
def calculate_priority_score(df, stone_type, processing_type, height):
    """Calculate priority scores for filtered products"""
    def score_row(r):
        score = 0
        
        # Stone type matching (40 points max)
        if str(r['loai_da']).upper() == stone_type.upper():
            score += 40
        elif stone_type.upper() in str(r['loai_da']).upper():
            score += 30
        else:
            score += 10
            
        # Processing type matching (30 points max)
        if str(r['gia_cong']).upper() == processing_type.upper():
            score += 30
        elif processing_type.upper() in str(r['gia_cong']).upper():
            score += 20
        else:
            score += 5
            
        # Height matching (30 points max)
        height_diff = abs(float(r['H']) - height) if pd.notna(r['H']) else 100
        if height_diff < 0.1:
            score += 30
        elif height_diff <= 1.0:
            score += 25
        elif height_diff <= 2.0:
            score += 20
        elif height_diff <= 5.0:
            score += 15
        else:
            score += 5
            
        return score
    
    df['priority_score'] = df.apply(score_row, axis=1)
    df['product_code'] = [generate_product_code(row, i) for i, (_, row) in enumerate(df.iterrows())]
    return df.sort_values('priority_score', ascending=False)

# Streaming text function
def stream_text(text, container, delay=0.05):
    """Simulate streaming text output"""
    placeholder = container.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(f'<div class="streaming-text">{displayed_text}▋</div>', unsafe_allow_html=True)
        time.sleep(delay)
    placeholder.markdown(f'<div class="streaming-text">{displayed_text}</div>', unsafe_allow_html=True)

# Load data
df = load_data()

# Initialize session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'input'
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'prediction_results' not in st.session_state:
    st.session_state.prediction_results = None

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1a1a1a 0%, #333 100%); padding: 8px; border-radius: 10px; text-align: center; color: #fabc14; font-family: 'Courier New', monospace;">
    <h1>🤖 AI-Powered Stone Price Prediction System</h1>
    <h5>Advanced automation for intelligent price forecasting</p>
</div>
""", unsafe_allow_html=True)

# STAGE 1: Initial Input
if st.session_state.stage == 'input':
    # st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI Assistant: Ready for Price Analysis")
    st.markdown("Please provide the stone specifications for intelligent price prediction:")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unique_stones = sorted(df['loai_da'].dropna().unique())
        stone_type = st.selectbox("Stone Type", unique_stones)
    
    with col2:
        unique_processing = sorted(df['gia_cong'].dropna().unique())
        processing_type = st.selectbox("Processing Method", unique_processing)
    
    with col3:
        height = st.number_input("Height (cm)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
    
    if st.button("Start AI Analysis", use_container_width=True):
        st.session_state.stone_type = stone_type
        st.session_state.processing_type = processing_type
        st.session_state.height = height
        st.session_state.stage = 'processing'
        st.rerun()

# STAGE 2: Processing and Analysis
elif st.session_state.stage == 'processing':
    
    # AI Response Container
    response_container = st.container()
    
    with response_container:
        st.markdown('<div class="ai-response">', unsafe_allow_html=True)
        
        # Streaming response 1
        stream_container1 = st.empty()
        stream_text("🔍 Analyzing your requirements...", stream_container1)
        
        time.sleep(1)
        
        stream_container2 = st.empty()
        stream_text(f"📊 Filtering database for {st.session_state.stone_type} stones with {st.session_state.processing_type} processing...", stream_container2)
        
        time.sleep(1)
        
        # Filter data
        filtered_df = df[
            (df['loai_da'] == st.session_state.stone_type) &
            (df['gia_cong'] == st.session_state.processing_type) &
            (df['H'] == st.session_state.height)
        ].copy()
        
        stream_container3 = st.empty()
        stream_text(f"✅ Found {len(filtered_df)} matching products in database", stream_container3)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        time.sleep(1)
        
        if len(filtered_df) > 0:
            # Calculate priority scores
            filtered_df = calculate_priority_score(filtered_df, st.session_state.stone_type, st.session_state.processing_type, st.session_state.height)
            st.session_state.filtered_data = filtered_df
            
            # Show filtered table
            st.markdown("### 📋 Filtered Product Database")
            st.dataframe(filtered_df[['product_code', 'loai_da', 'gia_cong', 'H', 'W', 'L', 'usd_m2', 'priority_score']], use_container_width=True)
            
            # AI continues analysis
            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
            stream_container4 = st.empty()
            stream_text("🧠 Computing priority scores and preparing predictive analysis...", stream_container4)
            time.sleep(1)
            
            stream_container5 = st.empty()
            stream_text("📈 Generating linear regression model for price prediction...", stream_container5)
            time.sleep(1)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Create priority vs product scatter plot with prediction line
            fig = go.Figure()
            
            # Add scatter points
            fig.add_trace(go.Scatter(
                x=filtered_df['priority_score'],
                y=list(range(len(filtered_df))),
                mode='markers',
                marker=dict(size=10, color='blue', opacity=0.6),
                text=filtered_df['product_code'],
                hovertemplate='<b>%{text}</b><br>Priority Score: %{x}<br>Price: $%{customdata:.2f}/m²',
                customdata=filtered_df['usd_m2'],
                name='Products'
            ))
            
            # Add linear regression line if we have enough data
            if len(filtered_df) > 1 and not filtered_df['usd_m2'].isna().all():
                clean_data = filtered_df.dropna(subset=['priority_score', 'usd_m2'])
                if len(clean_data) > 1:
                    lr = LinearRegression()
                    X = clean_data[['priority_score']]
                    y = clean_data['usd_m2']
                    lr.fit(X, y)
                    
                    x_line = np.linspace(clean_data['priority_score'].min(), clean_data['priority_score'].max(), 100)
                    y_line = lr.predict(x_line.reshape(-1, 1))
                    
                    fig.add_trace(go.Scatter(
                        x=x_line,
                        y=np.interp(y_line, sorted(clean_data['usd_m2']), range(len(clean_data))),
                        mode='lines',
                        line=dict(color='red', dash='dash', width=2),
                        name='Prediction Line'
                    ))
            
            fig.update_layout(
                title="Priority Score vs Product Analysis",
                xaxis_title="Priority Score",
                yaxis_title="Product Index",
                height=500,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Price prediction
            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
            stream_container6 = st.empty()
            
            # Calculate predicted price range
            valid_prices = filtered_df['usd_m2'].dropna()
            if len(valid_prices) > 0:
                avg_price = valid_prices.mean()
                min_price = valid_prices.min()
                max_price = valid_prices.max()
                
                prediction_text = f"💰 Based on analysis of {len(valid_prices)} similar products:\n\n"
                prediction_text += f"   • Predicted Price Range: ${min_price:.2f} - ${max_price:.2f} USD/m²\n"
                prediction_text += f"   • Average Predicted Price: ${avg_price:.2f} USD/m²\n"
                prediction_text += f"   • Confidence Level: {min(95, len(valid_prices) * 10)}%"
                
                stream_text(prediction_text, stream_container6)
                
                st.session_state.prediction_results = {
                    'avg_price': avg_price,
                    'min_price': min_price,
                    'max_price': max_price,
                    'confidence': min(95, len(valid_prices) * 10)
                }
            else:
                stream_text("⚠️ Insufficient price data for accurate prediction", stream_container6)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            time.sleep(2)
            
            # Ask for exact product search
            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
            stream_container7 = st.empty()
            stream_text("🎯 Would you like me to search for products with specific length and width dimensions?", stream_container7)
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Find Exact Products", use_container_width=True):
                    st.session_state.stage = 'exact_search'
                    st.rerun()
            
            with col2:
                if st.button("📊 Show Final Report", use_container_width=True):
                    st.session_state.stage = 'report'
                    st.rerun()
        
        else:
            st.error("❌ No matching products found in database")
            if st.button("🔄 Try Different Parameters"):
                st.session_state.stage = 'input'
                st.rerun()

# STAGE 3: Exact Product Search
elif st.session_state.stage == 'exact_search':
    st.markdown('<div class="ai-response">', unsafe_allow_html=True)
    st.markdown("🎯 **Please specify exact dimensions for precise product matching:**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        width = st.number_input("Width (cm)", min_value=0.1, max_value=100.0, value=15.0, step=0.1)
    
    with col2:
        length = st.number_input("Length (cm)", min_value=0.1, max_value=100.0, value=15.0, step=0.1)
    
    with col3:
        st.write("")  # Spacing
        if st.button("🔍 Search Exact Match", use_container_width=True):
            st.session_state.width = width
            st.session_state.length = length
            
            # Find exact matches
            exact_matches = df[
                (df['loai_da'] == st.session_state.stone_type) &
                (df['gia_cong'] == st.session_state.processing_type) &
                (df['H'] == st.session_state.height) &
                (df['W'] == width) &
                (df['L'] == length)
            ].copy()
            
            st.session_state.exact_matches = exact_matches
            st.session_state.stage = 'report'
            st.rerun()

# STAGE 4: Final Report
elif st.session_state.stage == 'report':
    st.markdown("## 📊 Comprehensive Price Analysis Report")
    
    # Report header
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**Generated:** {current_time}")
    st.markdown("---")
    
    # Product specifications
    st.markdown('<div class="report-section">', unsafe_allow_html=True)
    st.markdown("### 🎯 Product Specifications")
    
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
        st.markdown("### 💰 Price Prediction Summary")
        
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
        st.markdown("### 🎯 Exact Product Matches")
        st.success(f"Found {len(st.session_state.exact_matches)} exact matches!")
        st.dataframe(st.session_state.exact_matches[['loai_da', 'gia_cong', 'H', 'W', 'L', 'usd_pc', 'usd_m2', 'usd_m3', 'usd_ton']], use_container_width=True)
    
    # Show filtered data table
    if st.session_state.filtered_data is not None:
        st.markdown("### 📋 Similar Products Database")
        st.dataframe(st.session_state.filtered_data[['product_code', 'loai_da', 'gia_cong', 'H', 'W', 'L', 'usd_m2', 'priority_score']], use_container_width=True)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Analysis"):
            # Reset session state
            for key in list(st.session_state.keys()):
                if key != 'stage':
                    del st.session_state[key]
            st.session_state.stage = 'input'
            st.rerun()
    
    with col2:
        if st.button("📥 Export Report"):
            st.download_button(
                label="Download Analysis Report",
                data=f"Stone Price Analysis Report\nGenerated: {current_time}\n\nSpecifications:\n- Stone: {st.session_state.stone_type}\n- Processing: {st.session_state.processing_type}\n- Height: {st.session_state.height}cm\n\nPredicted Price: ${st.session_state.prediction_results['avg_price']:.2f}/m²" if st.session_state.prediction_results else "No prediction available",
                file_name=f"stone_analysis_{current_time.replace(':', '-')}.txt",
                mime="text/plain"
            )