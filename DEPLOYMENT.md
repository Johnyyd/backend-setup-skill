# Hướng dẫn Triển khai (Deployment Guide)

Tài liệu này mô tả chi tiết quy trình đưa ứng dụng từ môi trường phát triển (Local/Development) lên môi trường thực tế (Production) bằng Kubernetes (K8s).

## 1. Chuẩn bị (Prerequisites)
- Một cluster Kubernetes đang hoạt động (EKS, GKE, AKS, hoặc cụm tự quản lý).
- Nginx Ingress Controller đã được cài đặt trên cluster.
- `kubectl` đã được cấu hình trỏ tới cluster.
- Container Registry (Docker Hub, AWS ECR, GitHub CR) để lưu trữ image.

## 2. Quản lý Bí mật (Secret Management) - BẮT BUỘC
**LỖ HỔNG ĐƯỢC VÁ:** Tuyệt đối không lưu plaintext password (như `SECRET_KEY`, `POSTGRES_PASSWORD`) vào các file YAML (`k8s/config.yaml`) hoặc commit lên Git.
- Mặc định K8s Secret chỉ mã hóa Base64, không có khả năng bảo mật.
- Bạn phải sử dụng hệ thống như **External Secrets Operator** (đồng bộ từ AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) hoặc **Bitnami SealedSecrets**. File `config.yaml` hiện tại đã xóa bỏ phần Secret. Hệ thống K8s tự động chờ Secret này xuất hiện trước khi khởi động Pod.

## 3. Quy trình CI/CD (GitHub Actions)
Hệ thống sử dụng file `.github/workflows/ci.yml`. Mỗi khi có code mới đẩy lên nhánh `main`:
1. **Testing**: Hệ thống chạy Unit & Integration Test tự động.
2. **Build & Push**: CI build image bằng `Dockerfile.prod` (multi-stage) và push lên Registry.

## 4. Quy trình Triển khai Lên Kubernetes (An toàn)

Toàn bộ cấu hình nằm trong thư mục `k8s/`.

### Bước 4.1: Khởi tạo Storage và Database
```bash
# Tạo Namespace và ConfigMap
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/config.yaml

# LỖ HỔNG ĐƯỢC VÁ: Cả PostgreSQL và Redis đều sử dụng StatefulSet kèm Persistent Volume (PVC)
# Redis được cấu hình `--appendonly yes` để bảo toàn Token và State qua các đợt Restart.
kubectl apply -f k8s/database.yaml
kubectl apply -f k8s/redis.yaml
```

### Bước 4.2: Tự động chạy Database Migrations (Pre-Upgrade Hook)
**LỖ HỔNG ĐƯỢC VÁ:** Không thao tác thủ công qua CLI để tránh lộ mật khẩu trong `bash_history` và bảo toàn luồng CI/CD.
Quá trình apply cấu trúc Database phải được tự động hóa thông qua K8s Job `k8s/migration-job.yaml`.
Job này đã được gắn annotation: `"helm.sh/hook": pre-upgrade` và `argocd.argoproj.io/sync-wave: "-1"` để đảm bảo Database Schema được hoàn tất *trước* khi code mới được triển khai.
**Quan trọng (Tính Bất Biến của K8s Job):** K8s Job không cho phép ghi đè (apply) nếu nó đã chạy xong. Bạn bắt buộc phải xóa Job cũ đi trước khi chạy bản mới.
```bash
kubectl delete job backend-db-migration -n backend-prod --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
```

### Bước 4.3: Triển khai Backend API & Gateway
**LỖ HỔNG ĐƯỢC VÁ:** Lệnh apply không có tác dụng khóa đồng bộ. Nếu apply migration rồi apply backend ngay, backend sẽ khởi động khi DB chưa migrate xong.
Bạn phải dùng lệnh `wait` để ép quá trình CI/CD dừng lại chờ Job.
```bash
# Đợi Job Migrate hoàn thành (timeout 5 phút)
kubectl wait --for=condition=complete job/backend-db-migration -n backend-prod --timeout=300s

# Khởi động Backend (Deployment, HPA, Service)
kubectl apply -f k8s/backend.yaml

# Khởi động Ingress (Routing, SSL, CORS)
kubectl apply -f k8s/ingress.yaml
```

## 5. Quy trình Rollback & Expand-Contract Pattern
**LỖ HỔNG ĐƯỢC VÁ:** Không có khái niệm "Rollback không downtime" bằng `kubectl rollout undo` nếu Database Schema không tương thích ngược.

Nếu ứng dụng mới bị lỗi, lệnh sau có thể roll về phiên bản trước:
```bash
kubectl rollout undo deployment/backend -n backend-prod
```
**TUY NHIÊN**, để không gây sập hệ thống (CrashLoop), mọi Alembic migration bạn tạo ra **PHẢI** tuân thủ nguyên tắc **Expand and Contract**:
- **Không bao giờ xóa một cột hoặc đổi tên cột ngay lập tức**.
- Nếu thêm tính năng, hãy tạo cột mới cho phép `NULL` (Expand).
- Chạy hệ thống một thời gian để code mới ghi dữ liệu vào cả cũ và mới.
- Sau khi mọi thứ ổn định, mới tạo một migration khác để xóa cột cũ (Contract).
Chỉ khi Code cũ (V1) có thể chạy bình thường trên Schema mới (V2) thì tính năng `kubectl rollout undo` mới an toàn và hoàn toàn không gây downtime.
