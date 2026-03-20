import streamlit as st
from src.data.settings_loader import load_app_settings
from src.data.cw_loader import load_cw_config
from src.backtest.runner import run_backtest

def render_backtesting():
    st.header("🔬 Kiểm Thử Định Lượng (Backtest)")
    st.markdown("""
    Đưa Thuật toán về quá khứ để xem kết quả Giao dịch có tạo ra **LỢI NHUẬN THỰC TẾ** hay không.
    """)
    
    settings = load_app_settings()
    res = settings.get("resolution", "1D")
    max_days = 365 if res == "1D" else 30
    default_days = 180 if res == "1D" else 15
    
    cfg = load_cw_config()
    symbols = list(cfg.keys()) if cfg else ["FPT", "HPG", "VNM"]
    
    c1, c2 = st.columns(2)
    with c1: t_sym = st.selectbox("Chọn Mã Kiểm Thử", symbols)
    with c2: t_days = st.slider(f"Khoảng thời gian (Ngày) - Cho Nến {res}", 3, max_days, default_days)
        
    if st.button("🚀 Bắt Đầu Backtest", use_container_width=True):
        with st.spinner("Đang đồng bộ dữ liệu VNStock quá khứ và Dựng cây mô phỏng..."):
            res = run_backtest(t_sym, t_days)
            if "error" in res:
                st.error(f"Thất bại: {res['error']}")
            else:
                st.success("Hoàn thành Phân Tích Lịch Sử!")
                r1, r2, r3 = st.columns(3)
                r1.metric("Vốn Tổng Sau Cùng", f"{res['final_capital']:,.0f} VNĐ", f"{res['total_return_pct']}% Tổng Lợi Nhuận")
                r2.metric("Số Khớp Lệnh", f"{res['total_trades']} Lần")
                
                cycles = 0
                if not res['trades'].empty:
                    cycles = len(res['trades'][res['trades']['type'] == 'SELL'])
                r3.metric("Số Vòng Tròn (Chu kỳ)", f"{cycles} Vòng mua/bán khép kín")
                
                st.markdown("### 📈 Biểu Đồ Tăng Trưởng Tài Khoản Của Thuật Toán")
                st.line_chart(res['equity_curve'].set_index("time"), height=300)
                
                st.markdown("### 📔 Nhật Ký Giao Dịch Vào/Ra")
                st.dataframe(res['trades'], use_container_width=True, hide_index=True)
