# ─────────────────────────────────────────────────────
# Dockerfile — CW-Quant Dashboard (Streamlit + Python)
# Tối ưu cho CyberPanel / Docker Compose deployment
# ─────────────────────────────────────────────────────
FROM python:3.10-slim

# Metadata
LABEL maintainer="CW-Quant" \
      description="Streamlit Dashboard cho Phân Tích Chứng Khoán & Chứng Quyền"

# Biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Cài dependencies hệ thống (cần cho một số Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Thư mục làm việc trong container
WORKDIR /app

# Copy requirements trước (tận dụng Docker layer cache)
COPY requirements.txt .

# Cài Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code (trừ những file trong .dockerignore)
COPY . .

# Tạo thư mục data và alerts nếu chưa có
RUN mkdir -p /app/data /app/alerts

# Expose port Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Lệnh khởi động
CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.fileWatcherType=none"]
