import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="CW-Quant Dashboard", layout="wide")
st.title("CW-Quant Local Trading Assistant")

def load_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cw_quant.db")
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
        
    conn = sqlite3.connect(db_path)
    try:
        signals_df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 50", conn)
        market_df = pd.read_sql_query("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 50", conn)
    except Exception:
        signals_df = pd.DataFrame()
        market_df = pd.DataFrame()
    finally:
        conn.close()
    return signals_df, market_df

st.subheader("📊 C-Score Signals Over Time")
signals, market = load_data()

if not signals.empty:
    st.dataframe(signals.head(10), use_container_width=True)
    
    # Render interactive line chart for C-Score
    signals['timestamp'] = pd.to_datetime(signals['timestamp'])
    chart_data = signals.pivot(index='timestamp', columns='symbol', values='c_score')
    st.line_chart(chart_data)
else:
    st.info("No signals recorded yet. Database might be empty.")

st.subheader("📈 Live Market Data Feed")
if not market.empty:
    st.dataframe(market.head(10), use_container_width=True)
else:
    st.info("No market data recorded yet. Database might be empty.")
