import streamlit as st
import streamlit.components.v1 as components
from src.data.cw_loader import load_cw_config

def render_corporate_events():
    st.header("🔔 Lịch Cổ Tức & Sự Kiện Doanh Nghiệp (Corporate Actions)")
    st.markdown("""
    > 💡 **Tầm Quan Trọng:** Nắm bắt Lịch Chốt Quyền Cổ Tức, Phát Hành Thêm hay Họp ĐHCĐ là TỐI QUAN TRỌNG khi đánh T+ hoặc cầm Chứng Quyền (Vì Giá Thực Hiện & Tỷ Lệ Chuyển Đổi sẽ bị điều chỉnh vào Ngày Giao Dịch Không Hưởng Quyền).
    """)
    st.markdown("---")
    
    cfg = load_cw_config()
    watchlist = [k for k, v in cfg.items() if not v.get("is_cw", False)] if cfg else []
    
    if len(watchlist) > 0:
        st.info(f"📌 Các Mã Cơ Sở Đang Nằm Trong Radar Của Bạn: **{', '.join(watchlist)}**")
        
        shortcut_cols = st.columns(min(len(watchlist), 6))
        for i, sym in enumerate(watchlist[:6]):
            with shortcut_cols[i]:
                st.link_button(f"Tra Cứu Lịch {sym}", f"https://s.cafef.vn/Lich-su-kien.chn?sym={sym}", use_container_width=True)
                
    st.markdown("### 📅 Lịch Sự Kiện Toàn Thị Trường (Live Feed)")
    # Nhúng trực tiếp Lịch Sự Kiện của CafeF vào App (rất ổn định và real-time)
    components.iframe("https://s.cafef.vn/Lich-su-kien.chn", height=1000, scrolling=True)
