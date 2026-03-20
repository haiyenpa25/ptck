# Nhật Ký Lưu Vết Lỗi Phát Sinh & Kế Hoạch Đóng Gói File Code (Error Resolution Ledger)

> Kiến trúc Hệ thống: Streamlit SPA Multi-Module Component Architecture.
> Tính năng ghi nhận lỗi nhằm đảm bảo Rule thứ 3. KHÁCH HÀNG: Các lỗi được giải quyết dứt điểm không quay trở lại.

## Dựa Theo Đề Bài "Chia nhỏ file để dễ quản lý & tránh ngốn quá nhiều RAM / Token"

Tái phân rã hệ thống cấu trúc 1 File duy nhất (Monolith App.py > 1000 LOC, quá tải hệ thống xử lý IDE & AI Inference Engine):
1. UI Styles / Components tách ra làm file riêng: `ui_styles.py`, `auth.py`. Tại sao nó cần thiết? Vì tránh việc IDE / AI Engine đọc hàng trăm dòng CSS thừa.
2. Data Fetching / Caching Rules: Viết đúng dạng Decorator @st.cache_data tại `data_loader.py`.
3. View Logic: Các block lớn như `live_monitor`, `expert_advisor` đã được khoanh thành các Router.

---

## 🔥 NHẬT KÝ THEO DÕI VÀ VÁ LỖI (VẤN ĐỀ VÀ HƯỚNG QUYẾT)

### [E-001] Streamlit Import Recursion Warning
- **Mô tả Hiện Tượng:** Tách file và reload lại nhưng Streamlit không nhận dạng ra component hoặc gặp Lỗi Recursion. 
- **Nguyên Nhân:** Component A gọi View B, ngược lại B cũng gọi A hoặc import chồng chéo (Circular Reference).
- **Hành Động Khắc Phục:** Chỉ gọi Các View File (`views/x.py`) trực tiếp từ gốc Menu File (`app.py`). Tuyệt đối không để `view/live_monitor.py` import lại hàm UI gốc từ `app.py`. Mọi common imports phải di chuyển về Local `components/`.

### [E-002] Tình trạng Khoá (Locking) của File DB SQLite Cục bộ
- **Mô tả Hiện Tượng:** System Engine (Chạy bằng lệnh `python -m src.main`) đang ghi dữ liệu vào DB, cùng lúc đó UI Dashboard cũng cố viết nhật ký Trading vào `portfolio`, gây ra **"OperationalError: database is locked"**.
- **Cách Khắc Phục Khẩn Cấp Được Lưu Lại:** Đảm bảo `conn.close()` luôn được kích hoạt. Không được giữ `conn` global. Bất kỳ khi nào thực hiện Write, phải tắt Context Connection. Các hàm read nên dùng `pd.read_sql` và sau đó ngắt kết nối lập tức.

### [E-003] Thư viện VNStock Bị Khoá Port
- **Mô tả:** Request gọi bằng `try/except` bị timeout liên tục nếu IP request quá nhiều.
- **Cách Khắc Phục:** Cân nhắc chỉ định số lượng mã nạp ở T+ Radar Watchlist ở mức dưới 30 mã.
