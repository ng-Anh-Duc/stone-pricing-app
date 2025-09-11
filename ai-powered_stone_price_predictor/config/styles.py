# config/styles.py
"""CSS styles for the Stone Price Predictor app."""

from .settings import UI_CONFIG

def get_custom_css():
    """Return custom CSS styles for the application."""
    theme_color = UI_CONFIG["theme_color"]
    bg_dark = UI_CONFIG["background_dark"]
    bg_darker = UI_CONFIG["background_darker"]
    
    return f"""
    <style>
        .chat-container {{
            background: {bg_dark};
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            color: {theme_color};
            font-family: 'Courier New', monospace;
            border: 1px solid {theme_color};
        }}
        
        .ai-response {{
            background: {bg_darker};
            border-left: 3px solid {theme_color};
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 5px;
            color: {theme_color};
            font-family: 'Courier New', monospace;
        }}
        
        .prediction-container {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .report-section {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        
        .metric-highlight {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin: 0.5rem;
        }}
        
        .stButton > button {{
            background: {theme_color};
            color: black;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 2rem;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }}
        
        .streaming-text {{
            color: {theme_color};
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
        }}
    </style>
    """

def get_header_style():
    """Return header styling."""
    theme_color = UI_CONFIG["theme_color"]
    return f"""
    <div style="background: linear-gradient(90deg, #1a1a1a 0%, #333 100%); 
         padding: 8px; border-radius: 10px; text-align: center; 
         color: {theme_color}; font-family: 'Courier New', monospace;">
        <h1>🤖 AI-Powered Stone Price Prediction System</h1>
        <h5>Advanced automation for intelligent price forecasting</h5>
    </div>
    """