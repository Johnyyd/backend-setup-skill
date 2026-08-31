#!/bin/bash
set -e

echo "⚠️ Đang tiến hành TẮT hệ thống Docker Compose..."

echo "🛑 Dừng toàn bộ các container..."
docker-compose down

# Tùy chọn: Nếu muốn xóa sạch volume thì dùng cờ -v
# docker-compose down -v

echo "✅ HỆ THỐNG DOCKER ĐÃ ĐƯỢC TẮT HOÀN TOÀN!"
