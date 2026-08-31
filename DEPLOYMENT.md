# Hướng dẫn Triển khai (Deployment Guide)

Tài liệu này mô tả chi tiết quy trình đưa ứng dụng từ môi trường phát triển (Local/Development) lên môi trường thực tế (Production) bằng Kubernetes (K8s).

## 1. Chuẩn bị (Prerequisites)
- Một cluster Kubernetes đang hoạt động (EKS, GKE, AKS, hoặc cụm tự quản lý).
- Nginx Ingress Controller đã được cài đặt trên cluster.
- **Helm v3+** được cài đặt để triển khai hệ thống giám sát.
- `kubectl` đã được cấu hình trỏ tới cluster.
- Container Registry (Docker Hub, AWS ECR, GitHub CR) để lưu trữ image.

## 2. Quản lý Bí mật (Secret Management) - BẮT BUỘC
**LỖ HỔNG ĐƯỢC VÁ:** Tuyệt đối không lưu plaintext password (như `SECRET_KEY`, `POSTGRES_PASSWORD`) vào các file YAML (`k8s/config.yaml`) hoặc commit lên Git.
- Hệ thống K8s tự động chờ `backend-secrets` xuất hiện trước khi khởi động Pod.
- Bạn phải sử dụng **External Secrets Operator** hoặc tạo thủ công. Không được commit file Secret.

## 3. Quy trình Triển khai Hạ tầng Giám sát (Prometheus & Grafana)

Hệ thống giám sát BẮT BUỘC phải được cài đặt trước, nhằm đảm bảo các Resource `ServiceMonitor` hoạt động được.

### Bước 3.1: Khởi tạo Alertmanager Secrets
Sử dụng script để cấu hình Token của Slack/Telegram thay vì nhập plaintext:
```bash
./k8s/create-alertmanager-secrets.sh
```

### Bước 3.2: Triển khai Prometheus Stack qua Helm
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f k8s/alertmanager-values.yaml
```

## 4. Quy trình Triển khai Lên Kubernetes (An toàn)

Toàn bộ cấu hình ứng dụng nằm trong thư mục `k8s/`.

### Bước 4.1: Khởi tạo Namespace, Config và Cơ sở Dữ liệu
```bash
# Tạo Namespace và ConfigMap
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/config.yaml

# LỖ HỔNG ĐƯỢC VÁ: Redis và Postgres chạy trên StatefulSet + PVC
kubectl apply -f k8s/database.yaml
kubectl apply -f k8s/redis.yaml
```

### Bước 4.2: Tự động chạy Database Migrations
Quá trình apply cấu trúc Database phải được tự động hóa thông qua K8s Job.
**Quan trọng:** Bạn bắt buộc phải xóa Job cũ đi trước khi chạy bản mới.
```bash
kubectl delete job backend-db-migration -n backend-prod --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
# Đợi Job Migrate hoàn thành (timeout 5 phút)
kubectl wait --for=condition=complete job/backend-db-migration -n backend-prod --timeout=300s
```

### Bước 4.3: Triển khai Backend API, Gateway và Rules Giám sát
```bash
# Khởi động Backend (Deployment, HPA, Service)
kubectl apply -f k8s/backend.yaml

# Khởi động Ingress (Routing, SSL, CORS) - ĐÃ BỊ CHẶN PUBLIC ACCESS VÀO /metrics
kubectl apply -f k8s/ingress.yaml

# Kích hoạt Monitor (Prometheus sẽ bắt đầu cào dữ liệu)
kubectl apply -f k8s/service-monitor.yaml
kubectl apply -f k8s/prometheus-rules.yaml
```

## 5. Quy trình Rollback & Expand-Contract Pattern
**LỖ HỔNG ĐƯỢC VÁ:** Không có khái niệm "Rollback không downtime" bằng `kubectl rollout undo` nếu Database Schema không tương thích ngược.

Để không gây sập hệ thống (CrashLoop), mọi Alembic migration bạn tạo ra **PHẢI** tuân thủ nguyên tắc **Expand and Contract**:
- **Không bao giờ xóa một cột hoặc đổi tên cột ngay lập tức**.
- Nếu thêm tính năng, hãy tạo cột mới cho phép `NULL` (Expand).
- Khi Code cũ (V1) có thể chạy bình thường trên Schema mới (V2) thì tính năng Rollback mới thực sự an toàn.
