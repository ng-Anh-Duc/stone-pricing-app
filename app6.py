import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
import numpy as np
import re

# ------------------------------
# Page Configuration
# ------------------------------
st.set_page_config(
    page_title="Tra cứu giá sản phẩm đá",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .search-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    .result-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .price-table {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #dee2e6;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .sidebar .stSelectbox > div > div {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Load & normalize data
# ------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("cPhuong_last_check_1.csv")
        df = df.rename(columns={
            'LOẠI ĐÁ':        'loai_da',
            'CÁCH GIA CÔNG':  'gia_cong',
            'Mô tả Sản Phẩm': 'mo_ta',
            'Đơn giá':        'don_gia',
            'USD/PC':         'usd_pc',
            'USD/M2':         'usd_m2',
            'USD/M3':         'usd_m3',
            'USD/TON':        'usd_ton',
            'Year':           'year',
            'H':               'H',
            'W':               'W',
            'L':               'L',
        })
        
        # Convert numeric columns with proper error handling
        numeric_columns = ['L', 'W', 'H', 'usd_pc', 'usd_m2', 'usd_m3', 'usd_ton']
        for col in numeric_columns:
            if col in df.columns:
                # Clean the data by removing any non-numeric characters except decimal points
                df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error("❌ Không tìm thấy file dữ liệu: cPhuong_last_check_1.csv")
        st.stop()

df = load_data()

# Initialize session state
if 'matches' not in st.session_state:
    st.session_state.matches = None

# ------------------------------
# Header
# ------------------------------
st.markdown("""
<div class="main-header">
    <h1>Hệ thống tra cứu & dự đoán giá sản phẩm đá</h1>
    <p>Tìm kiếm sản phẩm phù hợp và dự đoán giá dựa trên dữ liệu lịch sử</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------
# Sidebar - Advanced Filters
# ------------------------------
with st.sidebar:
    st.header("Bộ lọc nâng cao")
    
    # Get unique values for dropdowns
    unique_stones = sorted(df['loai_da'].dropna().unique())
    unique_processing = sorted(df['gia_cong'].dropna().unique())
    
    if st.checkbox("Hiển thị chi tiết loại đá"):
        st.write("**Chi tiết các loại đá:**")
        stone_counts = df['loai_da'].value_counts()
        for stone, count in stone_counts.head(20).items():
            # Show the exact string representation
            st.write(f"• {stone} - {count} sản phẩm")

    
    # Filters
    filter_by_year = st.checkbox("Lọc theo năm")
    if filter_by_year:
        year_range = st.slider(
            "Chọn khoảng năm",
            min_value=int(df['year'].min()) if 'year' in df.columns else 2020,
            max_value=int(df['year'].max()) if 'year' in df.columns else 2025,
            value=(2020, 2025)
        )
    
    filter_by_price = st.checkbox("Lọc theo giá")
    if filter_by_price:
        price_type = st.selectbox(
            "Chọn loại giá USD",
            options=['usd_pc', 'usd_m2', 'usd_m3', 'usd_ton']
        )
        min_val = float(df[price_type].min())
        max_val = float(df[price_type].max())
        price_range = st.slider(
            f"Khoảng giá ({price_type.upper()})",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            format="%.2f"
        )
        df = df[(df[price_type] >= price_range[0]) & (df[price_type] <= price_range[1])]

    
    st.markdown("---")
    st.markdown("### Thống kê dữ liệu")
    st.metric("Tổng sản phẩm", len(df))
    st.metric("Loại đá", len(unique_stones))
    st.metric("Kiểu gia công", len(unique_processing))

# ------------------------------
# Main Input Section
# ------------------------------
st.markdown('<div class="search-container">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.subheader("Thông tin sản phẩm")
    stone_options = [
        "BAZAN",
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
    loai_da = st.selectbox("Loại đá", options=stone_options, index=unique_stones.index("BAZAN") if "BAZAN" in unique_stones else 0)
    gia_cong = st.selectbox("Cách gia công", options=unique_processing, index=unique_processing.index("ĐỐT XỊT") if "ĐỐT XỊT" in unique_processing else 0)

with col2:
    st.subheader("Kích thUớc (cm)")
    H = st.number_input("Chiều cao (H)", min_value=0.0, max_value=100.0, value=8.0, step=0.1)
    W = st.number_input("Chiều rộng (W)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)
    L = st.number_input("Chiều dài (L)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)

with col3:
    st.subheader("Thông tin bổ sung")
    volume = H * W * L
    st.metric("Thể tích (cm³)", f"{volume:,.0f}")
    area = W * L
    st.metric("Diện tích (cm²)", f"{area:,.0f}")
    
    # Search button
    search_button = st.button("🔍 Tìm kiếm sản phẩm", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

input_product = {
    'loai_da': loai_da,
    'gia_cong': gia_cong,
    'kich_thuoc': {'H': H, 'W': W, 'L': L}
}

# ------------------------------
# Priority scoring function (unchanged)
# ------------------------------
def calculate_priority_score_bazan(df, input_product):
    """
    Enhanced priority scoring with robust string matching
    """
    # Normalize input stone name
    input_stone = str(input_product['loai_da']).strip().upper()
    input_stone = re.sub(r'\s+', ' ', input_stone)  # Normalize spaces
    
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
    
    input_base_type = get_stone_base_type(input_stone)
    
    # Improved stone matching logic
    da_map = {
        'U1': lambda x: normalize_stone_name(x) == input_stone,  # Exact match after normalization
        'U2': lambda x: (
            get_stone_base_type(x) == input_base_type and  # Same base stone type
            normalize_stone_name(x) != input_stone  # But not exactly the same
        ),
        'U3': lambda x: True  # Any stone (fallback)
    }
    
    # Improved processing method matching
    input_processing = str(input_product['gia_cong']).strip().upper()
    input_processing = re.sub(r'\s+', ' ', input_processing)
    
    gc_map = {
        'U1': lambda x: normalize_stone_name(x) == input_processing,  # Exact match after normalization
        'U2': lambda x: True  # Any processing method
    }
    
    cao_map = {
        'U1': lambda v: abs(float(v) - input_product['kich_thuoc']['H']) < 0.01,
        'U2': lambda v: abs(float(v) - input_product['kich_thuoc']['H']) <= 1.0,
        'U3': lambda v: abs(float(v) - input_product['kich_thuoc']['H']) <= 2.0
    }

    # L-W-DISTANCE-BASED SCORING - This is the key change!
    def calculate_lwDistance_score(row_w, row_l, max_score=12):
        """
        Calculate score based on distance of L and W
        NOT based on individual width/length matching
        """
        try:
            # # Calculate areas
            # input_area = input_w * input_l  # Input product area
            # row_area = float(row_w) * float(row_l)  # Database product area
            
            # Calculate difference
            difference = abs(row_l - row_w)
            
            # Score based on distance similarity
            if difference < 1:  # Less than 1% area difference
                return max_score
            elif difference <= 5:
                return max_score * 0.95
            elif difference <= 10:
                return max_score * 0.85
            elif difference <= 20:
                return max_score * 0.7
            elif difference <= 30:
                return max_score * 0.55
            elif difference <= 50:
                return max_score * 0.4
            elif difference <= 75:
                return max_score * 0.25
            elif difference <= 100:
                return max_score * 0.15
            else:
                return max_score * 0.05
                
        except (ValueError, TypeError, ZeroDivisionError):
            return 0

    # rong_map = {
    #     'U1': lambda v: abs(float(v) - input_product['kich_thuoc']['W']) < 0.01,
    #     'U2': lambda v: abs(float(v) - input_product['kich_thuoc']['W']) <= 5.0,
    #     'U3': lambda v: abs(float(v) - input_product['kich_thuoc']['W']) <= 10.0
    # }
    # dai_map = {
    #     'U1': lambda v: abs(float(v) - input_product['kich_thuoc']['L']) < 0.01,
    #     'U2': lambda v: abs(float(v) - input_product['kich_thuoc']['L']) <= 10.0,
    #     'U3': lambda v: abs(float(v) - input_product['kich_thuoc']['L']) <= 20.0
    # }

    def score_row(r):
        s = 0
        stone_score = 0
        processing_score = 0
        
        # Stone type scoring with proper base type checking
        for lvl, fn in da_map.items():
            try:
                if fn(r['loai_da']):
                    stone_score = {'U1':30,'U2':25,'U3':20}[lvl]
                    s += stone_score
                    break
            except:
                continue
                
        # Processing method scoring
        for lvl, fn in gc_map.items():
            try:
                if fn(r['gia_cong']):
                    processing_score = {'U1':20,'U2':15}[lvl]
                    s += processing_score
                    break
            except:
                continue
                
        # Dimension scoring (with error handling)
        for lvl, fn in cao_map.items():
            try:
                if pd.notna(r['H']) and fn(r['H']):
                    s += {'U1':15,'U2':12,'U3':9}[lvl]
                    break
            except:
                continue
        
        # LW DISTANCE-BASED SCORING - This replaces width and length individual scoring
        if pd.notna(r['W']) and pd.notna(r['L']):
            lwDistance_score = calculate_lwDistance_score(
                r['W'], r['L'],  # Database product dimensions
                # input_product['kich_thuoc']['W'],  # Input width
                # input_product['kich_thuoc']['L'],  # Input length
                max_score=12  # Total points for area similarity
            )
            s += lwDistance_score
                
        return s
    
        # for lvl, fn in rong_map.items():
        #     try:
        #         if pd.notna(r['W']) and fn(r['W']):
        #             s += {'U1':9,'U2':6,'U3':3}[lvl]
        #             break
        #     except:
        #         continue
                
        # for lvl, fn in dai_map.items():
        #     try:
        #         if pd.notna(r['L']) and fn(r['L']):
        #             s += {'U1':3,'U2':2,'U3':1}[lvl]
        #             break
        #     except:
        #         continue
                
        # return s

    df['priority_score'] = df.apply(score_row, axis=1)
    
    # Add detailed scoring breakdown for debugging
    def get_match_type(row):
        row_stone = str(row['loai_da']).strip().upper()
        if input_stone == row_stone:
            return 'Exact Match'
        elif get_stone_base_type(row['loai_da']) == input_base_type:
            return f'Same Base Type ({input_base_type})'
        else:
            return f'Different Stone Type ({get_stone_base_type(row["loai_da"])})'
    
    df['stone_match_type'] = df.apply(get_match_type, axis=1)
    
    return df.sort_values('priority_score', ascending=False)

def get_dimension_info(row):
        """Add dimension difference info for debugging"""
        try:
            if pd.notna(row['W']) and pd.notna(row['L']):
                input_diff = abs(input_product['kich_thuoc']['W'] - input_product['kich_thuoc']['L'])
                row_diff = abs(float(row['W']) - float(row['L']))
                diff_similarity = abs(input_diff - row_diff)
                return f"Input W-L diff: {input_diff:.1f}, Row W-L diff: {row_diff:.1f}, Similarity: {diff_similarity:.1f}"
            return "N/A"
        except:
            return "Error"

# ------------------------------
# Search logic
# ------------------------------
if search_button:
    with st.spinner("🔄 Đang tìm kiếm..."):
        st.session_state.matches = calculate_priority_score_bazan(df.copy(), input_product)

matches = st.session_state.matches

# ------------------------------
# Display results
# ------------------------------
if matches is not None:
    if matches.empty:
        st.error("❌ Không có sản phẩm nào phù hợp.")
    else:
        top_score = matches['priority_score'].iloc[0]
        
        # Status indicator
        if top_score >= 77:
            st.success("✅ Đã tìm thấy sản phẩm chính xác!")
            status_color = "#28a745"
        else:
            st.warning("⚠️ Hiển thị sản phẩm gần giống nhất")
            status_color = "#ffc107"
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Kết quả tìm thấy", len(matches))
        with col2:
            st.metric("Điểm cao nhất", f"{top_score}/77")
        # with col3:
        #     # Safe calculation of average price with null checking
        #     valid_prices = matches.head(10)['usd_m2'].dropna()
        #     if len(valid_prices) > 0:
        #         avg_price = valid_prices.mean()
        #         st.metric("Giá trung bình", f"{avg_price:,.0f} USD/m2")
        #     else:
        #         st.metric("Giá trung bình", "N/A")
        # with col4:
        #     # Safe calculation of price range with null checking
        #     if len(valid_prices) > 0:
        #         price_range = valid_prices.max() - valid_prices.min()
        #         st.metric("Khoảng dao động giá", f"{price_range:,.0f} USD/m2")
        #     else:
        #         st.metric("Khoảng dao động giá", "N/A")
        with col3:
            avg_price = matches.head(10)['usd_m2'].mean()
            st.metric("Giá trung bình", f"${avg_price:,.0f} USD/m2")
        with col4:
            price_range = matches.head(10)['usd_m2'].max() - matches.head(10)['usd_m2'].min()
            st.metric("Khoảng dao động giá", f"${price_range:,.0f} USD/m2")
        
        # Display top matches
        st.subheader("Kết quả tìm kiếm")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Danh sách kết quả", "Biểu đồ giá", "Dự đoán giá"])
        
        # with tab1:
        #     for i, (_, r) in enumerate(matches.head(10).iterrows()):
        #         with st.expander(
        #             f"#{i+1} | {r['loai_da']} | {r['gia_cong']} | {r['H']}×{r['W']}×{r['L']} cm (Điểm: {r['priority_score']})",
        #             expanded=(i == 0)
        #         ):
        #             col1, col2 = st.columns([2, 1])
                    
        #             with col1:
        #                 st.write("**Mô tả sản phẩm:**")
        #                 st.write(r['mo_ta'])
                        
        #                 # Show matching details for debugging
        #                 st.write("**Chi tiết matching:**")
        #                 st.write(f"• Loại matching: **{r.get('stone_match_type', 'Unknown')}**")
        #                 st.write(f"• Điểm Uu tiên: **{r['priority_score']}/77**")
                        
        #                 # Price information
        #                 st.write("**Thông tin giá:**")
        #                 price_data = {
        #                     "Đơn giá (VND)": f"{r['don_gia']:,.0f}" if pd.notna(r['don_gia']) else "N/A",
        #                     "USD/PC": f"{r['usd_pc']:.2f}" if pd.notna(r['usd_pc']) else "N/A",
        #                     "USD/M²": f"{r['usd_m2']:.2f}" if pd.notna(r['usd_m2']) else "N/A",
        #                     "USD/M³": f"{r['usd_m3']:.2f}" if pd.notna(r['usd_m3']) else "N/A",
        #                     "USD/TON": f"{r['usd_ton']:.2f}" if pd.notna(r['usd_ton']) else "N/A"
        #                 }
                        
        #                 for key, value in price_data.items():
        #                     st.write(f"• {key}: **{value}**")
                    
                    # with col2:
                    #     # Similarity gauge
                    #     similarity_pct = (r['priority_score'] / 77) * 100
                    #     fig_gauge = go.Figure(go.Indicator(
                    #         mode = "gauge+number+delta",
                    #         value = similarity_pct,
                    #         domain = {'x': [0, 1], 'y': [0, 1]},
                    #         title = {'text': "Độ phù hợp (%)"},
                    #         gauge = {
                    #             'axis': {'range': [None, 100]},
                    #             'bar': {'color': status_color},
                    #             'steps': [
                    #                 {'range': [0, 50], 'color': "lightgray"},
                    #                 {'range': [50, 80], 'color': "yellow"},
                    #                 {'range': [80, 100], 'color': "lightgreen"}
                    #             ],
                    #             'threshold': {
                    #                 'line': {'color': "red", 'width': 4},
                    #                 'thickness': 0.75,
                    #                 'value': 90
                    #             }
                    #         }
                    #     ))
                    #     fig_gauge.update_layout(height=200)
                    #     st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{i}")
        
        with tab1:
            for i, (_, r) in enumerate(matches.head(10).iterrows()):
                with st.expander(
                    f"#{i+1} | {r['loai_da']} | {r['gia_cong']} | {r['H']}×{r['W']}×{r['L']} cm (Điểm: {r['priority_score']})",
                    expanded=(i == 0)
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Mô tả sản phẩm:**")
                        st.write(r['mo_ta'])
                        
                        # Price information
                        st.write("**Thông tin giá:**")
                        price_data = {
                            "Đơn giá (VND)": r['don_gia'] or "N/A",
                            "USD/PC": f"{r['usd_pc']:.2f}" if pd.notna(r['usd_pc']) else "N/A",
                            "USD/M²": f"{r['usd_m2']:.2f}" if pd.notna(r['usd_m2']) else "N/A",
                            "USD/M³": f"{r['usd_m3']:.2f}" if pd.notna(r['usd_m3']) else "N/A",
                            "USD/TON": f"{r['usd_ton']:.2f}" if pd.notna(r['usd_ton']) else "N/A"
                        }
                        
                        for key, value in price_data.items():
                            st.write(f"• {key}: **{value}**")
                    
                    with col2:
                        # Similarity gauge
                        similarity_pct = (r['priority_score'] / 77) * 100
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = similarity_pct,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Độ phù hợp (%)"},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': status_color},
                                'steps': [
                                    {'range': [0, 50], 'color': "lightgray"},
                                    {'range': [50, 80], 'color': "yellow"},
                                    {'range': [80, 100], 'color': "lightgreen"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 90
                                }
                            }
                        ))
                        fig_gauge.update_layout(height=200)
                        st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{i}")

        with tab2:
            # Historical price trends
            st.subheader("📈 Xu hUớng giá theo thời gian")
            
            top_matches = matches.head(5)
            fig_trends = make_subplots(
                rows=len(top_matches), cols=1,
                subplot_titles=[f"{r['loai_da']} - {r['gia_cong']}" for _, r in top_matches.iterrows()],
                vertical_spacing=0.1
            )
            
            for i, (_, r) in enumerate(top_matches.iterrows()):
                hist = df[
                    (df.loai_da == r['loai_da']) &
                    (df.gia_cong == r['gia_cong']) &
                    (df.H == r['H']) &
                    (df.W == r['W']) &
                    (df.L == r['L'])
                ]
                
                if not hist.empty and 'year' in hist.columns and len(hist['year'].dropna()) > 0:
                    # Filter out rows with invalid year or price data
                    hist_clean = hist.dropna(subset=['year', 'usd_m2'])
                    
                    if not hist_clean.empty:
                        fig_trends.add_trace(
                            go.Scatter(
                                x=hist_clean['year'], 
                                y=hist_clean['don_gia'],
                                mode='markers+lines',
                                name=f"Sản phẩm {i+1}",
                                line=dict(width=2)
                            ),
                            row=i+1, col=1
                        )
                        
                        # Add trend line if enough data
                        if hist_clean['year'].nunique() > 1 and len(hist_clean) > 1:
                            try:
                                lr = LinearRegression().fit(hist_clean[['year']], hist_clean['usd_m2'])
                                trend_line = lr.predict(hist_clean[['year']])
                                fig_trends.add_trace(
                                    go.Scatter(
                                        x=hist_clean['year'],
                                        y=trend_line,
                                        mode='lines',
                                        name=f"Xu hUớng {i+1}",
                                        line=dict(dash='dash', width=1)
                                    ),
                                    row=i+1, col=1
                                )
                            except Exception as e:
                                # Skip trend line if regression fails
                                pass
            
            fig_trends.update_layout(height=300*len(top_matches), showlegend=False)
            fig_trends.update_xaxes(title_text="Năm")
            fig_trends.update_yaxes(title_text="Giá (USD/m2)")
            st.plotly_chart(fig_trends, use_container_width=True, key="trends")
        
        with tab3:
            st.subheader("🎯 Dự đoán giá từ sản phẩm tUơng tự")
            best_matches = matches[matches['priority_score'] == top_score]

            if top_score == 77:
                st.success("🎯 Sản phẩm chính xác, không cần dự đoán giá thêm.")

            idx = best_matches['usd_m2'].idxmax()
            best = best_matches.loc[idx]
            st.metric("USD/PC", f"{best['usd_pc']:.2f}" if pd.notna(best['usd_pc']) else "N/A")
            st.metric("USD/M²", f"{best['usd_m2']:.2f}" if pd.notna(best['usd_m2']) else "N/A")
            st.metric("USD/M³", f"{best['usd_m3']:.2f}" if pd.notna(best['usd_m3']) else "N/A")
            st.metric("USD/TON", f"{best['usd_ton']:.2f}" if pd.notna(best['usd_ton']) else "N/A")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        💎 Hệ thống tra cứu giá sản phẩm đá công ty A Plus
    </div>
    """, 
    unsafe_allow_html=True
)