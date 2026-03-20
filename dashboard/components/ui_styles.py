def apply_premium_ui(st):
    st.set_page_config(page_title="Hệ Thống CW-Quant", layout="wide", page_icon="🏦")
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

    /* Tổng quan */
    .stApp { 
        background-color: #0F172A; 
        color: #E2E8F0; 
        font-family: 'Fira Sans', sans-serif; 
    }
    
    h1, h2, h3 { 
        color: #22D3EE !important; 
        font-weight: 700 !important; 
        letter-spacing: -0.025em;
    }

    /* Monospace for Data */
    code, .stMetricValue, .stDataFrame, .stTable {
        font-family: 'Fira Code', monospace !important;
    }
    
    /* Box Metrics Khung lưới (Glassmorphism) */
    div[data-testid="stMetricValue"] { 
        color: #22D3EE !important; 
        font-size: 2.2rem !important; 
        font-weight: 700 !important;
    }
    div[data-testid="stMetricDelta"] { 
        font-size: 0.9rem !important; 
        font-weight: 500 !important;
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-right: 3px solid #06B6D4;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(34, 211, 238, 0.3);
        box-shadow: 0 20px 25px -5px rgba(0, 240, 255, 0.1), 0 10px 10px -5px rgba(0, 240, 255, 0.1);
    }
    
    /* Bảng dữ liệu */
    .stDataFrame, div[data-testid="stTable"] { 
        border-radius: 12px; 
        overflow: hidden; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        background: rgba(15, 23, 42, 0.5) !important;
    }
    
    div[data-testid="stDataFrame"] div[role="grid"] {
        background-color: transparent !important;
    }

    div[data-testid="stDataFrame"] td {
        background-color: rgba(30, 41, 59, 0.3) !important;
        color: #E2E8F0 !important;
    }
    
    /* Nút bấm Premium */
    .stButton>button {
        background: linear-gradient(135deg, #0EA5E9 0%, #22D3EE 100%);
        color: #0F172A; 
        border: none; 
        border-radius: 10px; 
        font-weight: 700; 
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stButton>button:hover {
        transform: scale(1.02); 
        box-shadow: 0 0 20px rgba(34, 211, 238, 0.4); 
        color: #0F172A;
        border: none;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #0B1120; 
        border-right: 1px solid rgba(255, 255, 255, 0.05); 
    }
    
    /* Form */
    [data-testid="stForm"] {
        border-radius: 16px;
        background: rgba(30, 41, 59, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)
