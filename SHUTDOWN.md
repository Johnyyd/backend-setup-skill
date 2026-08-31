# Hướng dẫn Tắt Hệ thống (Teardown & Shutdown Guide)

Tài liệu này hướng dẫn bạn cách dừng, xóa bỏ hoặc dọn dẹp toàn bộ các dịch vụ và tài nguyên đang chạy trong hệ thống một cách an toàn. Bạn có thể chọn chỉ dừng tạm thời hoặc xóa vĩnh viễn tùy theo nhu cầu.

---

## 1. Tắt hệ thống trên Kubernetes

Nếu bạn đang chạy hệ thống trên Minikube, Docker Desktop K8s, hoặc trên Cloud (EKS/GKE), hãy sử dụng các lệnh sau để gỡ bỏ tài nguyên:

### Bước 1.1: Tắt toàn bộ Backend & Database
Lệnh sau sẽ xóa Deployment, StatefulSet, Service, Ingress, HPA, ConfigMap, và Job của hệ thống backend:
```bash
# Xóa toàn bộ tài nguyên trong thư mục k8s (trừ namespace nếu bạn muốn giữ lại namespace)
kubectl delete -f k8s/ingress.yaml --ignore-not-found
kubectl delete -f k8s/backend.yaml --ignore-not-found
kubectl delete -f k8s/database.yaml --ignore-not-found
kubectl delete -f k8s/redis.yaml --ignore-not-found
kubectl delete -f k8s/config.yaml --ignore-not-found
kubectl delete -f k8s/migration-job.yaml --ignore-not-found
```

### Bước 1.2: Tắt hệ thống Giám sát (Prometheus & Grafana)
Để gỡ cài đặt hoàn toàn bộ `kube-prometheus-stack` mà chúng ta đã cài bằng Helm:
```bash
# Gỡ cài đặt Helm release
helm uninstall prometheus --namespace monitoring

# Xóa các file cấu hình ServiceMonitor và PrometheusRule của backend
kubectl delete -f k8s/service-monitor.yaml --ignore-not-found
kubectl delete -f k8s/prometheus-rules.yaml --ignore-not-found

# (Tùy chọn) Xóa secret Alertmanager
kubectl delete secret alertmanager-secrets -n monitoring --ignore-not-found
```

### Bước 1.3: Dọn dẹp Namespace (Xóa sạch sẽ mọi thứ)
Nếu bạn muốn **phá hủy hoàn toàn** môi trường này (bao gồm cả dữ liệu trong Database và Redis được lưu trong K8s Persistent Volumes), bạn chỉ cần xóa toàn bộ Namespace:
```bash
kubectl delete namespace backend-prod
kubectl delete namespace monitoring
```
> **⚠️ CẢNH BÁO:** Lệnh này sẽ xóa toàn bộ Data Volume. Nếu bạn chỉ muốn dừng tạm thời để tiết kiệm tài nguyên thì KHÔNG nên chạy lệnh này, mà chỉ chạy Bước 1.1 bằng lệnh `kubectl scale deployment backend --replicas=0 -n backend-prod` để scale pod về 0.

---

## 2. Tắt hệ thống trên Docker Compose (Môi trường Local)

Nếu bạn đang phát triển ở môi trường Local bằng `docker-compose`, việc tắt hệ thống sẽ đơn giản hơn rất nhiều.

### Cách 1: Tắt và giữ lại dữ liệu
Lệnh này sẽ dừng các container nhưng giữ nguyên dữ liệu trong Postgres và Redis (dành cho việc nghỉ ngơi và ngày mai làm tiếp):
```bash
docker-compose down
```

### Cách 2: Tắt và xóa sạch mọi dữ liệu (Reset hệ thống)
Lệnh này sẽ dừng container và xóa toàn bộ các Volume chứa dữ liệu. Hệ thống sẽ trở lại như mới (phải chạy lại Migration từ đầu vào lần sau):
```bash
docker-compose down -v
```

---

## 3. Tắt cụm Kubernetes cục bộ (Local Cluster)

Nếu bạn đang chạy Kubernetes trên máy cá nhân và muốn giải phóng toàn bộ RAM/CPU cho máy tính:

- **Nếu dùng Docker Desktop:** Mở Docker Desktop Dashboard -> Settings -> Kubernetes -> Bỏ chọn "Enable Kubernetes" -> Apply & Restart.
- **Nếu dùng Minikube:** 
  - Tạm dừng: `minikube stop`
  - Xóa bỏ hoàn toàn cụm (Mất sạch dữ liệu): `minikube delete`
- **Nếu dùng Kind:** `kind delete cluster`
