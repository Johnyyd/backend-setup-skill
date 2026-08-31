Write-Host "🚀 Bắt đầu khởi chạy hệ thống trên Docker Compose (Local Environment)..." -ForegroundColor Green

Write-Host "📦 1. Xây dựng và khởi chạy các container" -ForegroundColor Cyan
docker-compose up -d --build

Write-Host "⏳ Đang đợi Cơ sở dữ liệu (Postgres & Redis) sẵn sàng..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "✅ HỆ THỐNG ĐÃ SẴN SÀNG TRÊN DOCKER!" -ForegroundColor Green
Write-Host "👉 Kiểm tra trạng thái các container:" -ForegroundColor Yellow
Write-Host "   docker-compose ps"
Write-Host "👉 Xem log của backend:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f backend"
