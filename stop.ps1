Write-Host "⚠️ Đang tiến hành TẮT VÀ XÓA BỎ toàn bộ hệ thống..." -ForegroundColor Yellow

Write-Host "🛑 1. Xóa bỏ luật cảnh báo và thu thập Metrics" -ForegroundColor Cyan
kubectl delete -f k8s/service-monitor.yaml --ignore-not-found
kubectl delete -f k8s/prometheus-rules.yaml --ignore-not-found

Write-Host "🔥 2. Gỡ cài đặt hệ thống giám sát (Prometheus & Grafana)" -ForegroundColor Cyan
helm uninstall prometheus --namespace monitoring
kubectl delete secret alertmanager-secrets -n monitoring --ignore-not-found

Write-Host "🛑 3. Xóa bỏ Backend API và Ingress" -ForegroundColor Cyan
kubectl delete -f k8s/ingress.yaml --ignore-not-found
kubectl delete -f k8s/backend.yaml --ignore-not-found

Write-Host "🛑 4. Xóa bỏ Cơ sở dữ liệu và Job Migration" -ForegroundColor Cyan
kubectl delete -f k8s/migration-job.yaml --ignore-not-found
kubectl delete -f k8s/database.yaml --ignore-not-found
kubectl delete -f k8s/redis.yaml --ignore-not-found

Write-Host "🧹 5. Dọn dẹp Config và Secrets" -ForegroundColor Cyan
kubectl delete -f k8s/config.yaml --ignore-not-found
kubectl delete secret backend-secrets -n backend-prod --ignore-not-found

Write-Host "🗑️ 6. Xóa vĩnh viễn Namespace (Cảnh báo: Dữ liệu PVC sẽ bị xóa)" -ForegroundColor Red
kubectl delete namespace backend-prod --ignore-not-found
kubectl delete namespace monitoring --ignore-not-found

Write-Host "✅ HỆ THỐNG ĐÃ ĐƯỢC TẮT VÀ DỌN DẸP HOÀN TOÀN!" -ForegroundColor Green
