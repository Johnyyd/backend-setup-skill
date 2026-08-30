# Backend Setup Troubleshooting Guide

## 1. Bẫy URL-Encoding trong PgBouncer (The Special Character Crash)

**Triệu chứng:**
Khi kết nối thông qua PgBouncer hoặc ứng dụng, bạn nhận được lỗi `Connection refused`, `Invalid database name`, hoặc URL parser báo lỗi.

**Nguyên nhân:**
Mật khẩu chứa các ký tự đặc biệt như `@`, `/`, `#`, `?`. Khi được nội suy vào chuỗi URI `postgres://user:password@host:port/db`, các ký tự này phá vỡ định dạng chuẩn của URI scheme. Ví dụ: `postgres://postgres:my@super/pass@database...` sẽ khiến parser nhầm hostname là `super/pass@database`.

**Cách khắc phục:**
1. **Lựa chọn 1 (Khuyên dùng):** BẮT BUỘC thiết lập chính sách tạo mật khẩu (trên AWS Secrets Manager hoặc HashiCorp Vault) chỉ sử dụng các ký tự **Alphanumeric** (Chữ và Số).
2. **Lựa chọn 2:** Nếu bắt buộc phải dùng ký tự đặc biệt, mật khẩu phải được **URL-Encoded** (Mã hóa URL, ví dụ `@` thành `%40`, `/` thành `%2F`) trước khi lưu vào K8s Secret hoặc file `.env`.
