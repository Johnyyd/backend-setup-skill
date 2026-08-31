Write-Host "⚠️ Đang tiến hành TẮT hệ thống Docker Compose..." -ForegroundColor Yellow

Write-Host "🛑 Dừng toàn bộ các container..." -ForegroundColor Cyan
docker-compose down

# Tùy chọn: Nếu muốn xóa sạch volume thì dùng lệnh dưới đây thay vì lệnh trên
# docker-compose down -v

Write-Host "✅ HỆ THỐNG DOCKER ĐÃ ĐƯỢC TẮT HOÀN TOÀN!" -ForegroundColor Green
