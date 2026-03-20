import streamlit as st
import sqlite3
import pandas as pd
import os

def render_portfolio_manager():
    st.header("💼 Sổ Nhật Ký & Quản Trị Danh Mục Thực Chiến")
    st.markdown("Nơi Ghi nhận Lệnh đã khớp (Paper Trading) và Tự động Tính Toán Khoản Lỗ/Lãi (PnL) Động.")
    
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cw_quant.db")
    
    # 1. Form Nhập Lệnh
    with st.expander("➕ Ghi Nhận Lệnh Vừa Khớp (Mở Vị Thế Mới)", expanded=False):
        with st.form("new_position_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                p_sym = st.text_input("Mã CW/Cơ Sở (VD: CFPT2305)").upper()
            with col2:
                p_price = st.number_input("Giá Lúc Khớp Lệnh (VND)", min_value=1.0)
            with col3:
                p_vol = st.number_input("Khối Lượng Mua", min_value=1, step=100)
                
            p_type = st.selectbox("Loại Lệnh Đang Đánh", ["MUA (LONG THEO C-SCORE)", "BÁN KHỐNG (HEDGE CƠ SỞ)"])
            submit_pos = st.form_submit_button("Lưu Vào Sổ & Theo dõi Tự động")
            
            if submit_pos and p_sym:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO portfolio (symbol, entry_price, volume, position_type) VALUES (?, ?, ?, ?)", (p_sym, p_price, p_vol, p_type))
                conn.commit()
                conn.close()
                st.success(f"Quản lý rủi ro: Đã khóa vị thế {p_vol} x {p_sym} vào Sổ Giao Dịch! Mở rộng tab bên dưới để Live PNL.")
                import time
                time.sleep(1)
                st.rerun()

    # 2. Hiển thị Vị thế Mở Trực tiếp
    st.subheader("🟢 Vị Thế Mở (Hàng Chưa Về / Đang Gồng Lãi)")
    try:
        conn = sqlite3.connect(DB_PATH)
        df_open = pd.read_sql("SELECT id, symbol, position_type, volume, entry_price, entry_time FROM portfolio WHERE status = 'OPEN'", conn)
        
        if not df_open.empty:
            df_open["Giá Hiện Tại (Check TCBS)"] = 0.0
            df_open["[X] Bấm Chốt Lời / Cắt Lỗ"] = False
            
            st.markdown("👉 **Điền Giá CW cập nhật mới nhất từ CTCK** vào cột `Giá Hiện Tại` để tự động tính PnL Tạm Tính:")
            edited_open = st.data_editor(df_open, disabled=["id", "symbol", "position_type", "volume", "entry_price", "entry_time"], hide_index=True, use_container_width=True)
            
            for index, row in edited_open.iterrows():
                exit_p = row["Giá Hiện Tại (Check TCBS)"]
                
                if exit_p > 0:
                    diff = exit_p - row['entry_price']
                    if "SHORT" in row['position_type']:
                        diff = -diff
                    pnl = diff * row['volume']
                    pct = (diff / row['entry_price']) * 100
                    if pnl >= 0:
                        st.success(f"📈 [PnL Live] {row['symbol']}: Lãi +{pnl:,.0f} VND (+{pct:.2f}%)")
                    else:
                        st.error(f"📉 [PnL Live] {row['symbol']}: Lỗ {pnl:,.0f} VND ({pct:.2f}%)")
                        
                # Closing condition
                if row["[X] Bấm Chốt Lời / Cắt Lỗ"] and exit_p > 0:
                    c = conn.cursor()
                    realized = (exit_p - row['entry_price']) * row['volume']
                    if "SHORT" in row['position_type']: realized = -realized
                    
                    c.execute("UPDATE portfolio SET status='CLOSED', exit_price=?, exit_time=CURRENT_TIMESTAMP, realized_pnl=? WHERE id=?", (exit_p, realized, row['id']))
                    conn.commit()
                    st.balloons()
                    st.success(f"BING BONG! Đã Chốt lệnh {row['symbol']} thành công! Lợi nhuận gộp đã được chuyển vào Lịch Sử Hình Tròn.")
                    import time
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Hiện không có Vị Thế Mở nào. Đợi C-Score bắn lệnh và đi tiền thôi!")
            
        st.subheader("🔴 Lịch Sử Trận Đánh (Closed Positions)")
        df_closed = pd.read_sql("SELECT symbol, position_type, volume, entry_price, entry_time, exit_price, exit_time, realized_pnl FROM portfolio WHERE status = 'CLOSED' ORDER BY exit_time DESC", conn)
        if not df_closed.empty:
            st.dataframe(df_closed, hide_index=True)
            total_pnl = df_closed['realized_pnl'].sum()
            st.markdown("---")
            if total_pnl > 0: 
                st.markdown(f"### 🏆 TỔNG LỢI NHUẬN RÒNG ĐÃ CHỐT: <span style='color:green'>+{total_pnl:,.0f} VND</span> 💰", unsafe_allow_html=True)
            else: 
                st.markdown(f"### 📉 TỔNG TỔN THẤT GIAO DỊCH: <span style='color:red'>{total_pnl:,.0f} VND</span>", unsafe_allow_html=True)
        else:
            st.empty()
            
        conn.close()
    except Exception as e:
        st.error(f"Waiting for database structure initialization... {e}")
