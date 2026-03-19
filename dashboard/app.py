import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import sys
import requests

# Khởi tạo đường dẫn Backend
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.backtest.runner import run_backtest
from src.data.cw_loader import load_cw_config, save_cw_config
from alerts.telegram_bot import load_telegram_config, save_telegram_config

# -----------------------------------------------------------------
# CẤU HÌNH TRANG & GIAO DIỆN (PREMIUM UI)
# -----------------------------------------------------------------
st.set_page_config(page_title="Hệ Thống CW-Quant", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    /* Tổng quan */
    .stApp { background-color: #0F1116; color: #E0E6ED; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #00F0FF !important; font-weight: 600 !important; }
    
    /* Box Metrics Khung lưới */
    div[data-testid="stMetricValue"] { color: #00F0FF !important; font-size: 2rem !important; }
    div[data-testid="stMetricDelta"] { font-size: 1rem !important; }
    .metric-card {
        background: linear-gradient(145deg, #1A1D24 0%, #0F1116 100%);
        border: 1px solid #2A2D35;
        border-right: 2px solid #00F0FF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,240,255,0.05);
    }
    
    /* Bảng dữ liệu */
    .stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #2A2D35; }
    
    /* Nút bấm */
    .stButton>button {
        background: linear-gradient(90deg, #0052D4 0%, #4364F7 50%, #6FB1FC 100%);
        color: white; border: none; border-radius: 8px; font-weight: 600; transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px); box-shadow: 0 5px 15px rgba(67, 100, 247, 0.4); border: none; color: white;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #15181E; border-right: 1px solid #2A2D35; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------
# DATA LOADER & API KẾT NỐI
# -----------------------------------------------------------------
@st.cache_data(ttl=15)
def load_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cw_quant.db")
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        try:
            signals_df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 100", conn)
            market_df = pd.read_sql_query("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 50", conn)
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
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
    except Exception as e:
        st.error(f"Lỗi kết nối API Danh mục: {e}")
        return []

def color_cscore(val):
    try:
        val = float(val)
        if val >= 65: return 'color: #00FF00; background-color: rgba(0,255,0,0.1); font-weight: bold'
        elif val < 50: return 'color: #FF4B4B; background-color: rgba(255,0,0,0.1); font-weight: bold'
        return 'color: #FFA500'
    except: return ''

# -----------------------------------------------------------------
# MODULE 1: BẢNG TRUNG TÂM (LIVE MONITORING)
# -----------------------------------------------------------------
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
        c1, c2 = st.columns([1.5, 2])
        with c1:
            st.markdown("### 📋 Lịch Sử Cảnh Báo")
            styled_signals = signals.head(15).style.map(color_cscore, subset=['c_score'])
            st.dataframe(styled_signals, use_container_width=True, hide_index=True)
            
        with c2:
            st.markdown("### 🎢 Xu Hướng C-Score (Real-time)")
            signals['timestamp'] = pd.to_datetime(signals['timestamp'])
            cln = signals.drop_duplicates(subset=['timestamp', 'symbol'])
            chart_data = cln.pivot(index='timestamp', columns='symbol', values='c_score').ffill().bfill()
            st.line_chart(chart_data, height=400)
    else:
        st.info("🔄 Đang nạp dữ liệu từ hệ thống lõi... Vui lòng chờ 15s nếu Bot vừa khởi động.")

# -----------------------------------------------------------------
# MODULE 2: KHÁM PHÁ & CẤU HÌNH DANH MỤC LỌC
# -----------------------------------------------------------------
def render_watchlist_manager():
    st.header("🎯 Cấu Hình Danh Mục Quét Tự Động")
    st.markdown("""
    > **Cơ chế Tiết kiệm Tài nguyên (Local-Optimized):** Máy tính của bạn sẽ KHÔNG quét toàn bộ thị trường. Bạn chỉ định những mã Cơ Sở và Chứng Quyền nào ở dưới đây, Bot sẽ chỉ kết nối API lấy đúng các mã đó để đảm bảo tốc độ tối đa!
    """)
    
    current_config = load_cw_config()
    
    st.markdown("---")
    st.subheader("🔍 Máy Quét Phái Sinh (Auto-Discovery)")
    # Lựa chọn mã cơ sở phổ biến
    base_symbols = ["FPT", "HPG", "VNM", "MWG", "STB", "MBB", "TCB", "SSI", "VPB", "VHM", "VIC", "VRE", "MSN"]
    selected_base = st.selectbox("1. Chọn mã Chứng Khoán Cơ Sở bạn muốn tìm Chứng Quyền:", base_symbols)
    
    if st.button(f"Quét Chứng Quyền cho {selected_base}"):
        with st.spinner("Đang kết nối Dữ liệu Thị trường (VNDirect API)..."):
            cws = fetch_available_cws(selected_base)
            if cws:
                st.success(f"Phát hiện {len(cws)} Chứng quyền đang niêm yết cho {selected_base}.")
                # Chuyển thành DataFrame để hiển thị và chọn
                cw_df = pd.DataFrame(cws)[["symbol", "issuerName", "strikePrice", "maturityDate"]]
                # Thêm cột boolean để người dùng Check
                cw_df.insert(0, "Chọn Thêm", False)
                # Lưu vào session_state để render editor
                st.session_state['cw_scan_result'] = cw_df
            else:
                st.warning("Không tìm thấy Chứng quyền khả dụng hoặc API lỗi.")
                
    if 'cw_scan_result' in st.session_state:
        st.markdown("**2. Đánh dấu (Tick) vào các mã bạn muốn đưa vào Hệ Thống:**")
        edited_scan = st.data_editor(
            st.session_state['cw_scan_result'], 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Chọn Thêm": st.column_config.CheckboxColumn("Thêm vào Radar", default=False),
                "symbol": st.column_config.TextColumn("Mã CW", disabled=True),
                "issuerName": st.column_config.TextColumn("Tổ chức Phát hành", disabled=True),
                "strikePrice": st.column_config.TextColumn("Giá Hiện Thực", disabled=True),
                "maturityDate": st.column_config.TextColumn("Ngày Đáo Hạn", disabled=True)
            }
        )
        if st.button("📥 Hợp nhất vào Danh mục (Merge)"):
            selected_cws = edited_scan[edited_scan["Chọn Thêm"] == True]
            count = 0
            for _, row in selected_cws.iterrows():
                sym = row["symbol"]
                if sym not in current_config:
                    current_config[sym] = {"is_cw": True, "delta": 0.5, "gearing": 3.0} # Giá trị mặc định an toàn cho CW
                    count += 1
            if count > 0:
                # Đảm bảo mã cơ sở cũng nằm trong danh mục
                if selected_base not in current_config:
                    current_config[selected_base] = {"is_cw": False, "delta": 1.0, "gearing": 1.0}
                save_cw_config(current_config)
                st.success(f"Thành công! Đã thêm Mã cơ sở {selected_base} và {count} Mã Chứng quyền vào Danh Mục của Bot lõi.")
                st.rerun()
            else:
                st.info("Chưa chọn mã nào để đánh dấu.")

    st.markdown("---")
    st.subheader("📝 Danh Mục Radar Hiện Có")
    st.markdown("Tinh chỉnh thông số `Delta` (Xác suất sinh lời) và `Gearing` (Đòn bẩy thực tế) từ Bảng giá CTCK để Bot C-Score tính toán chính xác nhất.")
    
    if not current_config:
        st.warning("Danh mục rỗng. Vui lòng thêm từ Máy quét ở trên.")
    else:
        df_cfg = pd.DataFrame.from_dict(current_config, orient='index').reset_index()
        df_cfg.columns = ["Mã_CK", "Loại_CW", "Delta", "Gearing"]
        
        final_edt = st.data_editor(df_cfg, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Cập Nhật Ghi Đè (Save All Changes)"):
            new_config = {}
            for _, r in final_edt.dropna(subset=['Mã_CK']).iterrows():
                s = str(r["Mã_CK"]).strip().upper()
                if s: new_config[s] = {"is_cw": bool(r["Loại_CW"]), "delta": float(r["Delta"]), "gearing": float(r["Gearing"])}
            save_cw_config(new_config)
            st.success("Đã ghi đè xong! Bot tự động áp dụng vòng lặp tiếp theo.")

# -----------------------------------------------------------------
# MODULE 3: KIỂM THỬ GIAO DỊCH QUÁ KHỨ
# -----------------------------------------------------------------
def render_backtesting():
    st.header("🔬 Kiểm Thử Định Lượng (Backtest)")
    st.markdown("""
    Đưa Thuật toán về quá khứ để xem kết quả Giao dịch có tạo ra **LỢI NHUẬN THỰC TẾ** hay không.
    """)
    
    cfg = load_cw_config()
    symbols = list(cfg.keys()) if cfg else ["FPT", "HPG", "VNM"]
    
    c1, c2 = st.columns(2)
    with c1: t_sym = st.selectbox("Chọn Mã Kiểm Thử", symbols)
    with c2: t_days = st.slider("Khung thời gian (Ngày)", 30, 365, 180)
        
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

# -----------------------------------------------------------------
# MODULE 4: TÀI LIỆU & HƯỚNG DẪN KỸ THUẬT
# -----------------------------------------------------------------
def render_documentation():
    st.header("📚 Sách Hướng Dẫn Thuật Toán CW-Quant")
    
    with st.expander("1. Chỉ Số Đầu Đầu Tư C-Score Là Gì?", expanded=True):
        st.markdown("""
        **C-Score (CW Score)** là một chỉ số định lượng do Hệ thống này đặc chế, có thang điểm từ 0 - 100.
        Chỉ số này được tính toán liên tục dựa trên 3 trụ cột:
        - **Thời gian đáo hạn (Time Factor):** Càng xa ngày đáo hạn, độ an toàn càng cao (điểm cộng). Dưới 15 ngày là mức rủi ro tử thần (điểm trừ nặng).
        - **Độ chênh lệch giá (Spread Factor):** Giá Ask và Bid của CTCK chênh lệnh càng ít, quy mô thanh khoản càng đẹp.
        - **Động lượng Hỗn hợp (Delta-Adjusted Momentum):** Động lực tăng/giảm giá của Mã Cơ sở, được KHUẾCH ĐẠI bởi hệ số cực kỳ quan trọng là **Delta** và **Gearing** thực tế của Chứng Quyền.
        
        👉 *Kết luận:* Khi C-Score vọt lên trên 65, hệ thống sẽ Báo động Trạng thái **CONFIRM** hoặc **MAX_SIZE**, đây là điểm MUA VÀO lý tưởng. Nếu C-Score rớt xuống dưới 50 (**IDLE**), đó là lúc dòng tiền suy yếu cần CHỐT LỜI/CẮT LỖ.
        """)
        
    with st.expander("2. Cách Nạp Thông Số Delta và Gearing Ở Đâu?"):
        st.markdown("""
        Không có bất kỳ API miễn phí nào tại Việt Nam cung cấp Live Greek cho Chứng quyền. Bạn BẮT BUỘC phải lấy thủ công mỗi sáng sớm từ các nguồn:
        - **Bảng Giá VNDirect:** Cột "Đòn bẩy thực tế (Effective Gearing)" và "Delta".
        - **Bảng Giá SSI (Iboard):** Có chuyên trang Chứng quyền chi tiết.
        
        Sau khi có thông số, hãy qua Tab **[🔍 Cấu Hình Radar]** -> Chỉnh sửa ở Bảng *Danh Mục Radar Hiện Có* rồi bấm *Save*. Bot sẽ dùng thông số bạn nạp để nhân với Thuật toán sinh ra tín hiệu.
        """)
        
    with st.expander("3. Hướng Dẫn Kết Nối Telegram Đẩy Tin Báo"):
        st.markdown("""
        Để bot nhắn tin thẳng vào điện thoại của bạn, hãy cung cấp 2 chìa khóa: `Bot Token` và `Chat ID`.
        """)
        tele_config = load_telegram_config()
        with st.form("guide_tele_form"):
            t_token = st.text_input("🔑 Bot Token (Tạo từ @BotFather trên Telegram)", value=tele_config.get("bot_token", ""), type="password")
            t_chat = st.text_input("💬 Chat ID (Nhắn cho @userinfobot để lấy số)", value=tele_config.get("chat_id", ""))
            
            if st.form_submit_button("Lưu Liên Kết API"):
                if save_telegram_config({"bot_token": t_token, "chat_id": t_chat}):
                    st.success("✅ Lưu thành công. Điện thoại của bạn sẽ rung lên ngay khi có Tín Hiệu!")
                else:
                    st.error("Lỗi cấu hình.")

# -----------------------------------------------------------------
# ĐIỀU HƯỚNG THANH BÊN (SIDEBAR ROUTING)
# -----------------------------------------------------------------
st.sidebar.title("🤖 CW-Quant Assistant")
st.sidebar.markdown("Phiên bản Bot Nội Bộ Chạy Lõi Thuật Toán Momentum Phái Sinh.")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "ĐIỀU HƯỚNG VÙNG LÀM VIỆC:",
    [
        "📊 Bảng Điều Khiển Trực Tiếp", 
        "🔍 Cấu Hình Radar & Quét API", 
        "📈 Kiểm Thử Quá Khứ (Backtest)", 
        "📚 Hướng Dẫn Thuật Toán"
    ]
)

if menu == "📊 Bảng Điều Khiển Trực Tiếp":
    render_live_monitoring()
elif menu == "🔍 Cấu Hình Radar & Quét API":
    render_watchlist_manager()
elif menu == "📈 Kiểm Thử Quá Khứ (Backtest)":
    render_backtesting()
elif menu == "📚 Hướng Dẫn Thuật Toán":
    render_documentation()

st.sidebar.markdown("---")
st.sidebar.caption("System Status: **ONLINE**")
st.sidebar.caption("Data Provider: **VNStock3 & VNDirect**")
