import sys
import os
import streamlit as st

# Khởi tạo đường dẫn Backend
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard.components.ui_styles import apply_premium_ui
from dashboard.components.auth import check_password
from dashboard.views.live_monitor import render_live_monitoring
from dashboard.views.watchlist import render_watchlist_manager
from dashboard.views.backtest_view import render_backtesting
from dashboard.views.portfolio import render_portfolio_manager
from dashboard.views.expert_advisor import render_expert_advisor
from dashboard.views.corporate import render_corporate_events
from dashboard.views.docs import render_documentation

# 1. Cấu hình giao diện Premium
apply_premium_ui(st)

# 2. Bước tường lửa bảo mật
if not check_password(st):
    st.stop()

# 3. Sidebar Navigation
st.sidebar.title("🤖 CW-Quant Assistant")
st.sidebar.markdown("Phiên bản Bot Nội Bộ Chạy Lõi Thuật Toán Momentum Phái Sinh.")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "ĐIỀU HƯỚNG VÙNG LÀM VIỆC:",
    [
        "📊 Bảng Điều Khiển Trực Tiếp", 
        "🔍 Cấu Hình Radar & Quét API", 
        "📈 Kiểm Thử Quá Khứ (Backtest)", 
        "💼 Sổ Lệnh & Danh Mục (Tracker)",
        "🔮 Cố Vấn Tự Động (TA Expert)",
        "🔔 Lịch Cổ Tức & Sự Kiện",
        "📚 Hướng Dẫn Thuật Toán"
    ]
)

# 4. Dispatcher
if menu == "📊 Bảng Điều Khiển Trực Tiếp":
    render_live_monitoring()
elif menu == "🔍 Cấu Hình Radar & Quét API":
    render_watchlist_manager()
elif menu == "📈 Kiểm Thử Quá Khứ (Backtest)":
    render_backtesting()
elif menu == "💼 Sổ Lệnh & Danh Mục (Tracker)":
    render_portfolio_manager()
elif menu == "🔮 Cố Vấn Tự Động (TA Expert)":
    render_expert_advisor()
elif menu == "🔔 Lịch Cổ Tức & Sự Kiện":
    render_corporate_events()
elif menu == "📚 Hướng Dẫn Thuật Toán":
    render_documentation()

st.sidebar.markdown("---")
st.sidebar.caption("System Status: **ONLINE**")
st.sidebar.caption("Data Provider: **VNStock3 & VNDirect**")
