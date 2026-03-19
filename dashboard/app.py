import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import sys

# Ensure backend imports work 
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.backtest.runner import run_backtest
from src.data.cw_loader import load_cw_config, save_cw_config

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

tab1, tab2, tab3 = st.tabs(["Live Monitoring", "Historical Backtesting", "⚙️ Watchlist Settings"])

with tab1:
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

with tab2:
    st.header("📈 Historical Strategy Backtesting")
    st.markdown("Kiểm thử chiến lược C-Score Momentum trên dữ liệu thị trường quá khứ.")
    
    col1, col2 = st.columns(2)
    with col1:
        test_symbol = st.selectbox("Underlying Symbol", ["FPT", "VNM", "HPG", "VPB", "SSI"])
    with col2:
        test_days = st.slider("Lookback Period (Days)", 30, 365, 180)
        
    if st.button("Run Quantitative Backtest", type="primary"):
        with st.spinner(f"Running engine for {test_symbol}..."):
            results = run_backtest(test_symbol, test_days)
            
            if "error" in results:
                st.error(f"Backtest Failed: {results['error']}")
            else:
                st.success("Backtest Complete!")
                m1, m2, m3 = st.columns(3)
                m1.metric("Final Capital", f"{results['final_capital']:,.0f} VND", f"{results['total_return_pct']}%")
                m2.metric("Total Trades", results['total_trades'])
                
                win_rate = "TBD"
                if not results['trades'].empty and len(results['trades']) >= 2:
                    # simplistic win rate representation
                    sells = results['trades'][results['trades']['type'] == 'SELL']
                    win_rate = f"{len(sells)} pair(s)"
                m3.metric("Sell Cycles", win_rate)
                
                st.subheader("Equity Curve")
                chart_df = results['equity_curve'].set_index("time")
                st.line_chart(chart_df)
                
                st.subheader("Trade Log")
                st.dataframe(results['trades'], use_container_width=True)

with tab3:
    st.header("⚙️ Configuration & Watchlist")
    st.markdown("Quản lý danh mục theo dõi và thông số Greek cho CW.")
    
    current_config = load_cw_config()
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("Add/Edit Symbol")
        with st.form("add_symbol_form", clear_on_submit=True):
            new_symbol = st.text_input("Symbol (e.g., FPT, CFPT2305)").upper()
            is_cw = st.checkbox("Is Covered Warrant? (Check for CWs, uncheck for Base Stocks)")
            new_delta = st.number_input("Delta", value=1.0, format="%.2f", step=0.05)
            new_gearing = st.number_input("Gearing", value=1.0, format="%.2f", step=0.1)
            
            submitted = st.form_submit_button("Save Configuration")
            if submitted and new_symbol:
                current_config[new_symbol] = {
                    "is_cw": is_cw,
                    "delta": new_delta,
                    "gearing": new_gearing
                }
                if save_cw_config(current_config):
                    st.success(f"Saved {new_symbol}! The engine will pick it up on the next tick.")
                    st.rerun()
                else:
                    st.error("Failed to save.")
                    
        st.subheader("Remove Symbol")
        with st.form("remove_form"):
            rem_symbol = st.selectbox("Symbol to delete", list(current_config.keys()) if current_config else ["None"])
            rem_submitted = st.form_submit_button("Delete")
            if rem_submitted and rem_symbol != "None":
                del current_config[rem_symbol]
                if save_cw_config(current_config):
                    st.success(f"Deleted {rem_symbol}.")
                    st.rerun()
                    
    with col_b:
        st.subheader("Current Settings Viewer")
        st.json(current_config)
