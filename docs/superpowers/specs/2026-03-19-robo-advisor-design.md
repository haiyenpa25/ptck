# Robo-Advisor (Technical Analysis Expert) Design Spec

## 1. Mục Đích (Purpose)
Xây dựng một Module Cố Vấn Tự Động (Robo-Advisor) trong Giao diện Dashboard để phân tích kỹ thuật chuyên sâu bất kỳ Mã Cổ Phiếu Cơ Sở nào. Module này sẽ tổng hợp các Chỉ báo Động lượng, Xu hướng và Dòng tiền để đưa ra Khuyến nghị bằng văn bản (Textual Summary) giống như một Chuyên gia thực thụ.

## 2. Luồng Xử Lý (Data Flow)
1. Người dùng chọn Mã Cổ Phiếu trên Tab "🔮 Cố Vấn Kỹ Thuật" của Streamlit.
2. Bot sử dụng hàm `stock_historical_data` từ vnstock để lấy dữ liệu nến Ngày (1D) của 6 tháng gần nhất.
3. Bot tự động tính toán 4 chỉ báo cốt lõi thông qua thư viện `pandas` (Không cài thêm thư viện ngoài để giữ dung lượng nhẹ):
   - Tính SMA 20 và EMA 50 (Xác định Xu Hướng Trend).
   - Tính RSI 14 (Đo lường Quá mua / Quá bán).
   - Tính MACD (Đo lường Sức mạnh Khởi đầu/Kết thúc chu kỳ).
   - Tính Trung bình Khối lượng 20 Phiên (Volume Profile).
4. Hệ chuyên gia (Expert Ruleset) chấm điểm (Scoring):
   - **Tín Hiệu Tăng Trưởng (Bullish):** RSI < 30 (Bắt đáy), Giá cắt lên MA20, Khối lượng đột biến > 150%.
   - **Tín Hiệu Chốt Lời (Bearish):** RSI > 70 (Đu đỉnh), Giá gãy MA20, MACD cắt xuống.
5. In ra màn hình Streamlit các Cột Số Liệu trực quan và 1 Đoạn Văn Bản Khuyến Nghị Tóm Tắt.

## 3. Kiến Trúc File (Architecture)
- **File Mới:** Tích hợp trực tiếp 1 hàm `render_robo_advisor()` vào `dashboard/app.py` và đưa vào thanh điều hướng Sidebar.
- Các hàm phân tích toán học (Toán RSI, EMA, MACD) sẽ được viết nhúng gọn nhẹ bên trong file UI để đảm bảo tốc độ phản hồi nhanh nhất.

## 4. Giao Diện (UI)
- Hiển thị Giá Trị Hiện Tại (Giá Hiện Tại, RSI, Tín hiệu MACD).
- Thanh Trạng Thái (Thước đo Mức độ Đẹp của Biểu đồ: Rất Tốt / Bình Thường / Cực Kì Xấu).
- Khung Văn Bản Tóm Tắt: "Chuyên gia AI nhận định: Dòng tiền đang nổ mạnh... Khuyến nghị MUA."
