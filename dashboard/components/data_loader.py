import streamlit as st
import sqlite3
import pandas as pd
import requests
import os

@st.cache_data(ttl=15)
def load_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cw_quant.db")
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        try:
            signals_df = pd.read_sql_query("""
                SELECT id, symbol, underlying, state, c_score, base_mome, delta, gearing, 
                       strike_price, ratio, maturity_date, issuer, 
                       spread_score, time_score, mome_score, cw_momentum_pct,
                       timestamp FROM signals ORDER BY timestamp DESC LIMIT 100
            """, conn)
            market_df = pd.read_sql_query("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 50", conn)
        except Exception:
            # Fallback for old schema if migration failed partially
            signals_df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 100", conn)
            market_df = pd.read_sql_query("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 50", conn)
    return signals_df, market_df

def fetch_available_cws(underlying_symbol: str) -> list:
    """Gọi API VNDirect để quét toàn bộ Chứng quyền đang niêm yết của Mã Cơ sở"""
    url = f"https://finfo-api.vndirect.com.vn/v4/stocks?q=type:cw~status:listed"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        data = r.json().get('data', [])
        # Lọc thủ công để tránh lỗi query API
        filtered = [x for x in data if x.get("underlyingSymbol") == underlying_symbol]
        return filtered
    except Exception:
        return []

def color_cscore(val):
    try:
        val = float(val)
        if val >= 65: return 'color: #00FF00; background-color: rgba(0,255,0,0.1); font-weight: bold'
        elif val < 50: return 'color: #FF4B4B; background-color: rgba(255,0,0,0.1); font-weight: bold'
        return 'color: #FFA500'
    except: return ''
