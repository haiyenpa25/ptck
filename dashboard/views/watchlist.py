import streamlit as st
import pandas as pd
from src.data.settings_loader import load_app_settings, save_app_settings
from src.data.cw_loader import load_cw_config, save_cw_config
from dashboard.components.data_loader import fetch_available_cws

def render_watchlist_manager():
    st.header("🎯 Cấu Hình Danh Mục Quét Tự Động")
    st.markdown("""
    > **Cơ chế Tiết kiệm Tài nguyên (Local-Optimized):** Máy tính của bạn sẽ KHÔNG quét toàn bộ thị trường. Bạn chỉ định những mã Cơ Sở và Chứng Quyền nào ở dưới đây, Bot sẽ chỉ kết nối API lấy đúng các mã đó để đảm bảo tốc độ tối đa!
    """)
    
    st.markdown("---")
    st.subheader("⚡ Tần Số Quét Lệnh (Timeframe Engine V4)")
    settings = load_app_settings()
    current_res = settings.get("resolution", "1D")
    
    modes = {"1D": "Nhịp Swing Đoạn Ngắn (Khung Ngày / 1D)", "1H": "Day Trading Biến Động (Khung 1 Giờ / 1H)", "15": "Cướp Tàu Thần Tốc (Khung 15 Phút / 15m)"}
    rev_modes = {v: k for k, v in modes.items()}
    c1, c2 = st.columns([2, 1])
    with c1:
        sel_mode = st.radio("Chọn Nhịp Mạch (Heartbeat) Của Lõi Quant:", list(modes.values()), index=list(modes.keys()).index(current_res), key="timeframe_radio")
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("💾 Áp Dụng Nhịp Mạch", use_container_width=True):
            settings["resolution"] = rev_modes[sel_mode]
            save_app_settings(settings)
            st.success(f"Hệ thống đã chuyển tần số lõi sang {sel_mode}! Chức năng Backtest cũng sẽ tuân theo tần số này.")
            st.rerun()
            
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
                st.warning("⚠️ Mạng Local của bạn đang chặn API VNDirect (Timeout). Vui lòng kéo xuống Bảng bên dưới, chọn [+] Add Row để tự gõ thêm Mã Chứng Quyền thủ công.")
                
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
            num_selected = len(selected_cws)
            if num_selected > 0:
                for _, row in selected_cws.iterrows():
                    sym = row["symbol"]
                    if sym not in current_config:
                        current_config[sym] = {"is_cw": True, "delta": 0.5, "gearing": 3.0}
                # Đảm bảo mã cơ sở cũng hiển diện
                if selected_base not in current_config:
                    current_config[selected_base] = {"is_cw": False, "delta": 1.0, "gearing": 1.0}
                save_cw_config(current_config)
                st.success(f"Thành công! Đã thêm {num_selected} Mã Chứng quyền vào Danh Mục.")
            else:
                st.info("Chưa chọn mã nào để đánh dấu.")

    st.markdown("---")
    st.subheader("📝 Danh Mục Radar Hiện Có")
    st.markdown("Tinh chỉnh thông số `Delta` (Xác suất sinh lời) và `Gearing` (Đòn bẩy thực tế) từ Bảng giá CTCK để Bot C-Score tính toán chính xác nhất.")
    
    if not current_config:
        st.warning("Danh mục rỗng. Vui lòng thêm từ Máy quét ở trên.")
    else:
        # Build safe dataframe independent of config extra keys
        data_list = []
        for sym, props in current_config.items():
            data_list.append({
                "Mã_CK": sym,
                "Loại_CW": props.get("is_cw", False),
                "Delta": props.get("delta", 1.0),
                "Gearing": props.get("gearing", 1.0)
            })
        df_cfg = pd.DataFrame(data_list)
        
        final_edt = st.data_editor(
            df_cfg, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Mã_CK": st.column_config.TextColumn("Mã CK", required=True),
                "Loại_CW": st.column_config.CheckboxColumn("Chứng quyền"),
                "Delta": st.column_config.NumberColumn("Delta", min_value=0.0, max_value=2.0, format="%.2f"),
                "Gearing": st.column_config.NumberColumn("Gearing", min_value=0.0, max_value=20.0, format="%.2f")
            }
        )
        if st.button("💾 Cập Nhật Ghi Đè (Save All Changes)"):
            new_config = {}
            for _, r in final_edt.dropna(subset=['Mã_CK']).iterrows():
                s = str(r["Mã_CK"]).strip().upper()
                if s: new_config[s] = {"is_cw": bool(r["Loại_CW"]), "delta": float(r["Delta"]), "gearing": float(r["Gearing"])}
            save_cw_config(new_config)
            st.success("Đã ghi đè xong! Bot tự động áp dụng vòng lặp tiếp theo.")
