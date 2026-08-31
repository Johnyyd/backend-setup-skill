#!/bin/bash
set -e

echo "🚀 Bắt đầu khởi chạy hệ thống trên Docker Compose (Local Environment)..."

echo "📦 1. Xây dựng và khởi chạy các container"
docker-compose up -d --build

echo "⏳ Đang đợi Cơ sở dữ liệu (Postgres & Redis) sẵn sàng..."
# Đợi một chút để DB khởi động
sleep 10

echo "✅ HỆ THỐNG ĐÃ SẴN SÀNG TRÊN DOCKER!"
echo "👉 Kiểm tra trạng thái các container:"
echo "   docker-compose ps"
echo "👉 Xem log của backend:"
echo "   docker-compose logs -f backend"
