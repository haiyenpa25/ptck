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
from alerts.telegram_bot import load_telegram_config, save_telegram_config

st.set_page_config(page_title="CW-Quant Dashboard", layout="wide", page_icon="📈")

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- Database & Config Loaders ---
def load_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cw_quant.db")
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        try:
            signals_df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 50", conn)
            market_df = pd.read_sql_query("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 50", conn)
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
    return signals_df, market_df

def color_cscore(val):
    """Color styling for C-Score column"""
    try:
        val = float(val)
        if val >= 65: return 'color: #00FF00; font-weight: bold'
        elif val < 50: return 'color: #FF4B4B; font-weight: bold'
        return 'color: #FFA500'
    except: return ''

# --- UI Components ---
def render_live_monitoring():
    st.subheader("📊 Phân Tích C-Score Real-time")
    signals, market = load_data()
    
    if not signals.empty:
        # Header Metrics
        col1, col2, col3 = st.columns(3)
        latest_signal = signals.iloc[0]
        col1.metric("🔥 Tín hiệu Nóng nhất", f"{latest_signal['symbol']}", f"{latest_signal['state']} ({latest_signal['c_score']})")
        col2.metric("📦 Tổng lệnh log", len(signals))
        cfg = load_cw_config()
        col3.metric("🎯 Mã đang theo dõi", len(cfg))
        
        st.markdown("---")
        # Split layout for data and chart
        c1, c2 = st.columns([1.5, 2])
        with c1:
            st.markdown("**Bảng điểm Tín hiệu (Latest)**")
            styled_signals = signals.head(15).style.map(color_cscore, subset=['c_score'])
            st.dataframe(styled_signals, use_container_width=True, hide_index=True)
            
        with c2:
            st.markdown("**Biểu đồ C-Score Trends**")
            signals['timestamp'] = pd.to_datetime(signals['timestamp'])
            chart_data = signals.pivot(index='timestamp', columns='symbol', values='c_score')
            chart_data = chart_data.ffill().bfill()
            st.line_chart(chart_data, height=350)
    else:
        st.info("Hệ thống chưa ghi nhận tín hiệu nào. Đang chờ Engine tính toán...")

    st.markdown("---")
    st.subheader("📈 Dữ liệu Market Data Feed (Raw)")
    if not market.empty:
        st.dataframe(market.head(10), use_container_width=True, hide_index=True)

def render_backtesting():
    st.header("📈 Historical Strategy Backtesting")
    st.markdown("Chạy mô phỏng tính hiệu quả chiến lược Định lượng trên dữ liệu lịch sử Vnstock.")
    
    cfg = load_cw_config()
    available_symbols = list(cfg.keys()) if cfg else ["FPT", "VNM", "HPG"]
    
    c1, c2 = st.columns(2)
    with c1: test_symbol = st.selectbox("Chọn Mã Cơ Sở / Chứng Quyền", available_symbols)
    with c2: test_days = st.slider("Số ngày Backtest", 30, 365, 180)
        
    if st.button("🚀 Chạy Kiểm Thử Định Lượng (Run Quant Backtest)", type="primary", use_container_width=True):
        with st.spinner(f"Xử lý lượng lớn {test_days} ngày lịch sử cho {test_symbol}..."):
            results = run_backtest(test_symbol, test_days)
            if "error" in results:
                st.error(f"Lỗi truy xuất dữ liệu từ Vnstock3: {results['error']}")
            else:
                st.success("Kiểm thử thành công!")
                r1, r2, r3 = st.columns(3)
                r1.metric("Vốn Còn Lại (Final Capital)", f"{results['final_capital']:,.0f} đ", f"{results['total_return_pct']}%")
                r2.metric("Tổng Số Lệnh (Trades)", results['total_trades'])
                
                win_rate = "N/A"
                if not results['trades'].empty and len(results['trades']) >= 2:
                    sells = results['trades'][results['trades']['type'] == 'SELL']
                    win_rate = f"{len(sells)} Chu kỳ"
                r3.metric("Hoàn thành", win_rate)
                
                st.markdown("**Biểu đồ Tăng trưởng Tài khoản (Equity Curve)**")
                chart_df = results['equity_curve'].set_index("time")
                st.line_chart(chart_df, height=300)
                
                st.markdown("**Nhật ký Giao dịch (Trade Log)**")
                st.dataframe(results['trades'], use_container_width=True, hide_index=True)

def render_settings():
    st.header("⚙️ Dynamic Configurations")
    st.markdown("Quản lý thông số thuật toán trực tiếp trên giao diện.")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("1. Danh Mục Đầu Tư (Watchlist)")
        st.caption("Chỉnh sửa tự do trực tiếp trên bảng. Bot Data Crawler sẽ nhận update tự động.")
        config = load_cw_config()
        
        # Convert config dict to list of dicts for data_editor
        data_list = []
        for sym, props in config.items():
            data_list.append({
                "Symbol": sym,
                "is_cw": props.get("is_cw", False),
                "delta": props.get("delta", 1.0),
                "gearing": props.get("gearing", 1.0)
            })
            
        df = pd.DataFrame(data_list)
        if df.empty:
            df = pd.DataFrame(columns=["Symbol", "is_cw", "delta", "gearing"])
            
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Symbol": st.column_config.TextColumn("Mã CK", required=True),
                "is_cw": st.column_config.CheckboxColumn("Chứng quyền"),
                "delta": st.column_config.NumberColumn("Delta", min_value=0.0, max_value=2.0, format="%.2f"),
                "gearing": st.column_config.NumberColumn("Gearing", min_value=0.0, max_value=20.0, format="%.2f")
            }
        )
        
        if st.button("💾 Lưu Cấu hình Watchlist"):
            new_config = {}
            for _, row in edited_df.dropna(subset=['Symbol']).iterrows():
                sym = str(row["Symbol"]).strip().upper()
                if sym:
                    new_config[sym] = {"is_cw": bool(row["is_cw"]),"delta": float(row["delta"]),"gearing": float(row["gearing"])}
            
            if save_cw_config(new_config):
                st.success("✅ Đã lưu danh sách theo dõi thành công!")
            else:
                st.error("Lỗi cập nhật cấu hình.")
                
    with c2:
        st.subheader("2. Cảnh báo Telegram")
        st.caption("Khai báo API Bot để nhận tín hiệu vào điện thoại.")
        tele_config = load_telegram_config()
        with st.form("tele_form"):
            t_token = st.text_input("Bot Token (Từ @BotFather)", value=tele_config.get("bot_token", ""), type="password")
            t_chat = st.text_input("Chat ID (Từ @userinfobot)", value=tele_config.get("chat_id", ""))
            
            if st.form_submit_button("Lưu Thiết Lập API"):
                if save_telegram_config({"bot_token": t_token, "chat_id": t_chat}):
                    st.success("✅ Đã kết nối Telegram thành công!")
                else:
                    st.error("Lỗi ghi file cấu hình telegram.")

# --- Main App Execution ---
st.title("🛡️ CW-Quant Local Trading System")
t1, t2, t3 = st.tabs(["🔴 Live Monitoring", "📈 Backtesting", "⚙️ Configurations"])

with t1: render_live_monitoring()
with t2: render_backtesting()
with t3: render_settings()
