import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import os

from dashboard.components.data_loader import load_data
from src.data.cw_loader import load_cw_config

def render_settlement_tracker():
    st.subheader("💰 Tâm Điểm Dòng Tiền & Chu Kỳ T+3")
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cw_quant.db")
    
    with sqlite3.connect(db_path) as conn:
        # 1. Capital Flow Today
        today = datetime.now().strftime("%Y-%m-%d")
        df_today_in = pd.read_sql(f"SELECT entry_price, volume FROM portfolio WHERE entry_time LIKE '{today}%'", conn)
        df_today_out = pd.read_sql(f"SELECT exit_price, volume FROM portfolio WHERE exit_time LIKE '{today}%'", conn)
        
        money_in = (df_today_in['entry_price'] * df_today_in['volume']).sum()
        money_out = (df_today_out['exit_price'] * df_today_out['volume']).sum()
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card" style="border-right-color:#00FF00"><p style="color:#A0AEC0; margin-bottom:0">Tổng Tiền Vào Hôm Nay</p><h2 style="color:#00FF00">{money_in:,.0f}</h2><p style="font-size:0.8rem">VNĐ</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card" style="border-right-color:#FF4B4B"><p style="color:#A0AEC0; margin-bottom:0">Tổng Tiền Ra Hôm Nay</p><h2 style="color:#FF4B4B">{money_out:,.0f}</h2><p style="font-size:0.8rem">VNĐ</p></div>', unsafe_allow_html=True)
        with c3:
            net = money_out - money_in
            st.markdown(f'<div class="metric-card"><p style="color:#A0AEC0; margin-bottom:0">Dòng Tiền Ròng (Net)</p><h2>{net:,.0f}</h2><p style="font-size:0.8rem">Sức mua thay đổi</p></div>', unsafe_allow_html=True)

        # 2. T+3 Cycle Algorithm
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⏳ Trạng Thái Settlement (Chu kỳ T+3)")
        df_open = pd.read_sql("SELECT symbol, entry_time, volume FROM portfolio WHERE status = 'OPEN'", conn)
        
        if not df_open.empty:
            cols = st.columns(len(df_open) if len(df_open) < 4 else 4)
            for i, row in df_open.iterrows():
                entry_dt = pd.to_datetime(row['entry_time'])
                days_diff = (datetime.now() - entry_dt).days
                
                # Biến đổi sang Ngày 1, 2, 3, 4 (T+3)
                t_status = min(days_diff + 1, 4)
                status_text = f"Ngày {t_status}"
                if t_status == 4: status_text = "Ngày 4 (Hàng Về ✅)"
                
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style="background:rgba(30,41,59,0.3); padding:15px; border-radius:10px; border-left:4px solid {'#00F0FF' if t_status<4 else '#00FF00'}">
                        <p style="margin:0; font-weight:bold">{row['symbol']}</p>
                        <p style="margin:0; font-size:1.2rem; color:{'#00F0FF' if t_status<4 else '#00FF00'}">{status_text}</p>
                        <progress value="{t_status}" max="4" style="width:100%"></progress>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Không có vị thế mở nào đang trong chu kỳ thanh toán.")

def render_live_monitoring():
    st.header("⚡ Theo Dõi Tín Hiệu Thuật Toán (Trực Tiếp)")
    signals, market = load_data()
    
    if not signals.empty:
        # Hàng Metrics
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        latest = signals.iloc[0]
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color:#A0AEC0; margin-bottom:0">Tín Hiệu Gần Nhất (🔥)</p>
                <h2 style="margin-top:0">{latest['symbol']}</h2>
                <h4 style="color:#00F0FF; margin-top:0">{latest['state']} ({latest['c_score']})</h4>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color:#A0AEC0; margin-bottom:0">Hành Động Khuyến Nghị</p>
                <h2 style="margin-top:0; color:{'#00FF00' if latest['c_score']>=65 else '#FF4B4B'}">
                    {'MUA MẠNH' if latest['c_score']>=65 else 'ĐỨNG NGOÀI'}
                </h2>
                <p style="color:#A0AEC0; margin-top:0; font-size:0.8rem">{latest['timestamp']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            cfg = load_cw_config()
            st.markdown(f"""
            <div class="metric-card">
                <p style="color:#A0AEC0; margin-bottom:0">Tổng Số Mã Theo Dõi</p>
                <h2 style="margin-top:0">{len(cfg)}</h2>
                <p style="color:#A0AEC0; margin-top:0; font-size:0.8rem">Radar quét mỗi 15 giây</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bố cục Chia cột
        c1, c2 = st.columns([1.8, 2])
        with c1:
            st.markdown("### 📋 Lịch Sử Cảnh Báo (Click hàng để xem Chi Tiết)")
            
            selection = st.dataframe(
                signals.head(20), 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # --- SIGNAL INTELLIGENCE PANEL (PREMIUM TA STYLE) ---
            selected_rows = []
            try: selected_rows = selection.selection.rows
            except: 
                try: selected_rows = selection.get("selection", {}).get("rows", [])
                except: pass

            if selected_rows:
                st.session_state['last_selected_signal'] = signals.iloc[selected_rows[0]].to_dict()

            if 'last_selected_signal' in st.session_state:
                row = st.session_state['last_selected_signal']
                
                # Metadata helper
                s_name = row.get('issuer', 'Hệ Thống CW-Quant')
                if s_name == "Unknown": s_name = "Tổ Chức Phát Hành (HOSE)"
                
                with st.container(border=True):
                    st.markdown(f"### 🧠 Signal Analysis: {row['symbol']}")
                    st.markdown(f"**Tên:** {s_name} | **Cơ sở:** `{row['underlying']}`")
                    
                    st.markdown("---")
                    
                    # Row 1: Key Metadata
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Giá Hiện Thực", f"{row.get('strike_price', 0):,.0f} đ")
                    m2.metric("Tỉ Lệ Chuyển Đổi", f"{row.get('ratio', '1:1')}")
                    m3.metric("Ngày Đáo Hạn", f"{row.get('maturity_date', 'N/A')}")
                    m4.metric("Trạng Thái", row['state'], delta_color="normal" if row['c_score'] >= 60 else "inverse")
                    
                    st.markdown("---")
                    
                    # Row 2: Quant Engine Breakdown (Transparent)
                    import math
                    st.markdown("#### ⚖️ Bóc Tách Phương Trình Điểm Số (Quant Score Equation)")
                    
                    c_total = row['c_score']
                    
                    # Safe NaN extraction for old database records
                    def safe_float(val, default):
                        if pd.isna(val) or val is None: return default
                        return float(val)

                    s_score = safe_float(row.get('spread_score'), 10.0)
                    t_score = safe_float(row.get('time_score'), 15.0)
                    m_score = safe_float(row.get('mome_score'), 0.0)
                    cw_mome = safe_float(row.get('cw_momentum_pct'), 0.0)
                    under_mome = safe_float(row.get('base_mome'), 0.0)
                    delta_val = safe_float(row.get('delta'), 0.5)
                    gearing_val = safe_float(row.get('gearing'), 3.0)
                    
                    st.info(f"**Công thức (Thuật toán v2):** `Điểm Nền [50] + Spread [{s_score:+.0f}] + Time [{t_score:+.0f}] + Momentum [{m_score:+.0f}] = {c_total:.1f}/100`")
                    
                    b1, b2, b3 = st.columns(3)
                    
                    with b1:
                        st.markdown(f"**1. Độ Chênh Lệch (Spread)**")
                        if s_score >= 20: st.caption("🟢 Rất An Toàn: Chênh lệch Bid/Ask < 1%")
                        elif s_score >= 10: st.caption("🟡 Trung Bình: Spread trong ngưỡng 1-3%")
                        else: st.caption("🔴 Rủi Ro: Spread giãn, trượt giá cao")
                        
                    with b2:
                        st.markdown(f"**2. Thời Gian (Time Decay)**")
                        if t_score >= 15: st.caption("🟢 Vùng An Toàn: Còn trên 20 ngày")
                        elif t_score >= 0: st.caption("🟡 Cảnh Báo: Sắp đáo hạn (15-20 ngày)")
                        else: st.caption("💀 Rủi Ro Tính Mạng: Dưới 15 ngày")
                        
                    with b3:
                        st.markdown(f"**3. Động Lượng (Momentum)**")
                        st.caption(f"Cơ sở: `{under_mome:+.2f}%` × Gearing `{gearing_val}x` × Delta `{delta_val}` = Xung lực CW `{cw_mome:+.2f}%`")
                    
                    st.markdown("---")
                    
                    # Row 3: Trading Action Plan
                    st.markdown("#### 🎯 Kế Hoạch Giao Dịch Thực Chiến (Dựa trên Cơ Sở)")
                    
                    # Logic kết luận
                    entry_plan = f"**1. Vùng Giá Vào (Entry):** Canh mua {row['symbol']} quanh Tham Chiếu hoặc giảm nhẹ. Hãy chờ mã cơ sở `{row['underlying']}` lùi về hỗ trợ hoặc rung lắc nhẹ (giảm 1-1.5%) để mua được giá rẻ nhất (Chiết khấu do Gearing)."
                    target_plan = f"**2. Giá Mục Tiêu (Take Profit):** Chốt lời khi cơ sở `{row['underlying']}` tăng đạt mức +3% hoặc chạm cản trên. Với đòn bẩy {gearing_val}x, kỳ vọng {row['symbol']} có thể lãi +{(3.0 * gearing_val * delta_val):.1f}%."
                    stop_plan = f"**3. Ngưỡng Cắt Lỗ (Stoploss):** Bán dứt khoát không giữ nết nếu cơ sở `{row['underlying']}` đóng nến gãy hỗ trợ / rơi quá -2%. Mức lỗ CW ước tính khoảng -{(2.0 * gearing_val * delta_val):.1f}%."

                    st.markdown(entry_plan)
                    st.markdown(target_plan)
                    st.markdown(stop_plan)

                    if t_score < 0:
                        st.error("⚠️ Phụ lục: Thời gian đáo hạn quá sát, bạn có thể mất TOÀN BỘ VỐN nếu mã cơ sở không kịp tăng giá vượt giá hòa vốn. Không dành cho tiền lớn!")
                    
                    st.divider()
                    st.progress(c_total / 100.0, text=f"Tổng Điểm Định Lượng: {c_total:.1f}/100")
            else:
                st.info("💡 Click vào một dòng trong bảng bên dưới để xem chi tiết tiêu chí đánh giá.")
            
        with c2:
            st.markdown("### 🎢 Xu Hướng C-Score (Signals)")
            signals['timestamp'] = pd.to_datetime(signals['timestamp'])
            cln = signals.drop_duplicates(subset=['timestamp', 'symbol'])
            
            if not cln.empty:
                fig = px.line(cln, x="timestamp", y="c_score", color="symbol", 
                              template="plotly_dark",
                              markers=True,
                              color_discrete_sequence=px.colors.qualitative.Antique)
                
                fig.update_layout(
                    font_family="Fira Code",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=30, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa đủ dữ liệu vẽ đồ thị.")

        # --- T+3 SETTLEMENT & CAPITAL FLOW ---
        st.markdown("---")
        render_settlement_tracker()

    else:
        st.info("🔄 Đang nạp dữ liệu từ hệ thống lõi... Vui lòng chờ 15s nếu Bot vừa khởi động.")
