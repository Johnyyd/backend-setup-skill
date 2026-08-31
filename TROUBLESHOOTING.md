# Backend Setup Troubleshooting Guide

## 1. Bẫy URL-Encoding trong PgBouncer (The Special Character Crash)

**Triệu chứng:**
Khi kết nối thông qua PgBouncer hoặc ứng dụng, bạn nhận được lỗi `Connection refused`, `Invalid database name`, hoặc URL parser báo lỗi.

**Nguyên nhân:**
Mật khẩu chứa các ký tự đặc biệt như `@`, `/`, `#`, `?`. Khi được nội suy vào chuỗi URI `postgres://user:password@host:port/db`, các ký tự này phá vỡ định dạng chuẩn của URI scheme. Ví dụ: `postgres://postgres:my@super/pass@database...` sẽ khiến parser nhầm hostname là `super/pass@database`.

**Cách khắc phục:**
1. **Lựa chọn 1 (Khuyên dùng):** BẮT BUỘC thiết lập chính sách tạo mật khẩu (trên AWS Secrets Manager hoặc HashiCorp Vault) chỉ sử dụng các ký tự **Alphanumeric** (Chữ và Số).
2. **Lựa chọn 2:** Nếu bắt buộc phải dùng ký tự đặc biệt, mật khẩu phải được **URL-Encoded** (Mã hóa URL, ví dụ `@` thành `%40`, `/` thành `%2F`) trước khi lưu vào K8s Secret hoặc file `.env`.

## 2. Nghịch lý Thời gian ân hạn K8s vs Gunicorn (The Grace Period Clash)

**Triệu chứng:**
Pod backend thỉnh thoảng bị K8s báo `OOMKilled` hoặc khởi động lại với lý do `SIGKILL` một cách bạo lực, dẫn đến Request của người dùng bị đứt gánh giữa chừng (502 Bad Gateway).

**Nguyên nhân:**
Gunicorn được cấu hình `--timeout 120` để xử lý các request dài. Tuy nhiên, Kubernetes mặc định `terminationGracePeriodSeconds` là 30 giây. Khi K8s gửi tín hiệu tắt Pod (Scale down, Rollout), K8s đếm ngược 30s. Dù Gunicorn đang bận xử lý request (nó nghĩ có 120s), đúng 30s K8s sẽ gửi tín hiệu giết bạo lực SIGKILL.

**Cách khắc phục:**
Trong `backend.yaml`, **bắt buộc** phải khai báo `terminationGracePeriodSeconds` lớn hơn tổng thời gian chờ của ứng dụng (VD: 130 giây).

## 3. Lỗi ServiceMonitor không hoạt động

**Triệu chứng:**
Prometheus hoàn toàn không thu thập được bất kỳ Metric nào từ Backend, dù đã cấu hình `ServiceMonitor`.

**Nguyên nhân:**
Kubernetes ServiceMonitor cực kỳ nghiêm ngặt về định nghĩa Port. Nếu `Service` của K8s không khai báo đúng thuộc tính `name:` tương ứng với những gì ServiceMonitor cần tìm, Prometheus sẽ âm thầm bỏ qua Service đó mà không hề báo lỗi.

**Cách khắc phục:**
Đảm bảo cổng trong file `backend.yaml` (`backend-service`) phải có tên chính xác là `name: http`, trùng với giá trị `- port: http` cấu hình trong `service-monitor.yaml`.

## 4. Tràn RAM Prometheus do Cardinality Explosion

**Triệu chứng:**
Prometheus liên tục bị OOMKilled do quá tải bộ nhớ RAM khi kết nối với FastAPI.

**Nguyên nhân:**
Thư viện `prometheus-fastapi-instrumentator` mặc định sẽ tạo ra một Metric chuỗi riêng biệt cho mỗi URL độc nhất (vd: `/api/users/1`, `/api/users/2`...). Kẻ tấn công hoặc hệ thống quét tự động có thể spam hàng triệu ID, làm phình to bộ nhớ (Cardinality Explosion) khiến Prometheus sập.

**Cách khắc phục:**
Tại file `main.py`, đã được thiết lập gom nhóm URL (Grouping paths). Tham số `should_group_status_codes=True`, `should_group_untemplated=True` sẽ gom tất cả `api/users/{id}` về chung một Metric duy nhất, vô hiệu hóa hoàn toàn vector tấn công này.

## 5. Lộ lọt Metrics ra ngoài Internet (Metric Leakage)

**Triệu chứng:**
Ai đó có thể truy cập `https://your-domain.com/metrics` và tải về toàn bộ dữ liệu nhạy cảm của hệ thống.

**Nguyên nhân:**
Khi mở Ingress để phục vụ API, path `/metrics` bị public theo.

**Cách khắc phục:**
Đã sử dụng cấu hình Ingress Nginx Configuration Snippet (file `ingress.yaml`) để chặn hoàn toàn (trả về 403 Forbidden) cho bất kỳ truy cập nào tới `/metrics` từ Internet bên ngoài. Việc cào dữ liệu (scraping) chỉ được phép diễn ra nội bộ (Internal Cluster IP) bởi Prometheus.
