# 🚀 Hướng Dẫn Deploy CW-Quant Lên CyberPanel Qua Docker

## 📁 Bước 1: Nén Project Trên Máy Windows

Mở **PowerShell** ở thư mục `d:\Xampp\htdocs\dautu` và chạy:

```powershell
# Tạo file zip chỉ gồm những file cần thiết (bỏ .venv và .git)
Compress-Archive -Path .\src, .\dashboard, .\data, .\alerts, .\Dockerfile, .\docker-compose.yml, .\requirements.txt, .\cw_quant.db -DestinationPath .\cw_quant_deploy.zip -Force
```

> Hoặc dùng cách thủ công: Chuột phải → **Send to → Compressed folder**, bỏ qua thư mục `.venv`, `.git`, `.agents`

---

## 📤 Bước 2: Upload Lên Server CyberPanel

Dùng **SCP, SFTP (WinSCP/FileZilla)** hoặc **File Manager của CyberPanel**:

```bash
# Upload bằng scp (thay YOUR_SERVER_IP)
scp cw_quant_deploy.zip root@YOUR_SERVER_IP:/home/cwquant/
```

---

## 🐳 Bước 3: Chạy Trên Server CyberPanel

SSH vào server, sau đó:

```bash
# Di chuyển vào thư mục vừa upload
cd /home/cwquant/

# Giải nén
unzip cw_quant_deploy.zip -d cw_quant && cd cw_quant

# Build và chạy container
docker compose up -d --build

# Kiểm tra đang chạy không
docker compose ps
docker compose logs -f   # Xem log realtime (Ctrl+C để thoát)
```

---

## 🌐 Bước 4: Cài Nginx Reverse Proxy Trên CyberPanel

Để trỏ domain về cổng 8501 của Streamlit, vào **CyberPanel → Websites → YOUR_DOMAIN → Rewrite Rules** và thêm:

```nginx
location / {
    proxy_pass         http://127.0.0.1:8501;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection "upgrade";
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_read_timeout 86400;
}
```

> ⚠️ **Streamlit cần WebSocket** — bắt buộc phải có `Upgrade` và `Connection "upgrade"` trong Nginx.

---

## 🔁 Bước 5: Update App Khi Có Thay Đổi Code

```bash
# Upload file zip mới lên server, sau đó:
cd /home/cwquant/cw_quant

# Pull code mới (hoặc giải nén lại)
unzip -o ../cw_quant_deploy.zip

# Rebuild và restart container (không mất dữ liệu DB)
docker compose up -d --build
```

---

## 📋 Lệnh Docker Hữu Ích

| Lệnh | Tác dụng |
|---|---|
| `docker compose up -d` | Chạy ngầm |
| `docker compose down` | Dừng container |
| `docker compose logs -f` | Xem log realtime |
| `docker compose restart` | Restart không build lại |
| `docker compose up -d --build` | Rebuild sau khi thay đổi code |
| `docker exec -it cw_quant_dashboard bash` | Vào trong container debug |

---

## ⚠️ Lưu Ý Quan Trọng

- **Database (`cw_quant.db`)** được mount ra ngoài container bằng volume — dữ liệu **KHÔNG BỊ MẤT** khi update image.
- **Port 8501** phải được mở trong Firewall của server (CyberPanel → Security → UFW/Firewall).
- Nếu CyberPanel đang dùng OpenLiteSpeed, cách cấu hình Reverse Proxy khác Nginx — vào **Virtual Host → External App → Proxy** để thêm.
