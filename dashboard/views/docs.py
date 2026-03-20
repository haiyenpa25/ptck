import streamlit as st
from alerts.telegram_bot import load_telegram_config, save_telegram_config

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
