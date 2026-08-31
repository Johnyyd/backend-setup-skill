Write-Host "🚀 Bắt đầu khởi chạy hệ thống Kubernetes..." -ForegroundColor Green

Write-Host "📦 1. Khởi tạo Namespace và Secrets cho Monitoring" -ForegroundColor Cyan
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic alertmanager-secrets -n monitoring `
  --from-literal=slack-url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX" `
  --from-literal=telegram-bot-token="123456789:ABCDefghIJKLmnopQRSTuvwxYZ" `
  --from-literal=telegram-chat-id="-1001234567890" `
  --dry-run=client -o yaml | kubectl apply -f -

Write-Host "📊 2. Cài đặt hệ thống giám sát Prometheus & Grafana (Helm)" -ForegroundColor Cyan
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack `
  --namespace monitoring `
  -f k8s/alertmanager-values.yaml

Write-Host "🛠️ 3. Khởi tạo Namespace và Config cho Backend" -ForegroundColor Cyan
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/config.yaml

Write-Host "🔐 4. Khởi tạo Backend Secrets" -ForegroundColor Cyan
kubectl create secret generic backend-secrets -n backend-prod `
  --from-literal=POSTGRES_USER=postgres `
  --from-literal=POSTGRES_PASSWORD=postgres `
  --from-literal=POSTGRES_DB=app `
  --from-literal=REDIS_PASSWORD=secure_redis_password `
  --from-literal=SECRET_KEY=your-secret-key-here-make-it-long-and-random `
  --dry-run=client -o yaml | kubectl apply -f -

Write-Host "🗄️ 5. Khởi chạy Cơ sở dữ liệu (Postgres & Redis)" -ForegroundColor Cyan
kubectl apply -f k8s/database.yaml
kubectl apply -f k8s/redis.yaml

Write-Host "⏳ Đang đợi Cơ sở dữ liệu sẵn sàng..." -ForegroundColor Yellow
kubectl rollout status statefulset/database -n backend-prod --timeout=300s
kubectl rollout status statefulset/redis -n backend-prod --timeout=300s
kubectl rollout status deployment/pgbouncer -n backend-prod --timeout=300s

Write-Host "🔄 6. Chạy Database Migrations" -ForegroundColor Cyan
kubectl delete job backend-db-migration -n backend-prod --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/backend-db-migration -n backend-prod --timeout=300s

Write-Host "🌐 7. Khởi chạy Backend API và Ingress" -ForegroundColor Cyan
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/ingress.yaml

Write-Host "📈 8. Kích hoạt luật cảnh báo và thu thập Metrics" -ForegroundColor Cyan
kubectl apply -f k8s/service-monitor.yaml
kubectl apply -f k8s/prometheus-rules.yaml

Write-Host "✅ HỆ THỐNG ĐÃ SẴN SÀNG!" -ForegroundColor Green
Write-Host "👉 Kiểm tra trạng thái Pods:" -ForegroundColor Yellow
Write-Host "   kubectl get pods -n backend-prod"
Write-Host "   kubectl get pods -n monitoring"
