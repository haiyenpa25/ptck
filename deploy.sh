#!/bin/bash
# deploy.sh — Cập nhật CW-Quant từ GitHub và restart Docker
# Chạy trên Server Ubuntu: bash deploy.sh

set -e

REPO_DIR="/home/cwquant/app"
COMPOSE_FILE="$REPO_DIR/docker-compose.yml"

echo "📥 Pulling code mới từ GitHub..."
cd "$REPO_DIR"
git pull origin main

echo "🐳 Rebuild và restart container..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo "✅ Deploy thành công!"
docker compose -f "$COMPOSE_FILE" ps
