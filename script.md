# Kịch bản demo MiniCloud

## Chuẩn bị

Chạy `docker compose up -d --build`, đợi DB, backend và Keycloak healthy. Không cần xóa volume. Chạy `powershell -ExecutionPolicy Bypass -File scripts/test-project.ps1`; kết quả phải là `Failures: 0`.

## Demo qua cổng tổng

1. Mở http://localhost/. Giới thiệu 9 loại dịch vụ và ba thành viên.
2. Mở Blog, đọc ba bài, kiểm tra ảnh và liên kết quay về cổng tổng.
3. Từ trang chủ, chọn API sinh viên hoặc MariaDB để mở trang dữ liệu riêng: JSON có 5 bản ghi, MariaDB có 3 bản ghi. Mở API /student/ để xem JSON thật.
4. Chọn dịch vụ Keycloak để mở trang đăng nhập; dùng sv01 / 123456, kết quả phải có Secure resource OK. Thử sai mật khẩu để xem thông báo lỗi. Lặp lại với sv02.
5. Mở quản trị Keycloak qua /auth/admin/, tài khoản admin / admin; kiểm tra realm_sv001, client flask-app, hai user. Không quay màn hình lộ token/mật khẩu.
6. Chọn Gateway & cân bằng tải, nhấn Kiểm tra phân phối trên trang riêng: kết quả có cả web-frontend-server1 và web-frontend-server2. Giải thích Nginx upstream Round Robin, header X-Served-By do web trả.
7. Chọn DNS nội bộ, nhấn Tra cứu trên trang riêng: bốn tên miền phải khớp IP .10/.20/.30/.40. Đây là truy vấn thật từ Flask đến Bind9, không phải bảng dữ liệu cố định.
8. Mở MinIO từ portal, đăng nhập minioadmin / minioadmin. Xem profile-pics/avatar.jpg và documents/minicloud-report.pdf. Upload thêm ảnh cá nhân và PDF nộp cuối của nhóm; tải lại để đối chiếu. Avatar công khai; tài liệu phải cần xác thực.
9. Mở Prometheus từ portal: node/web UP. Truy vấn node_cpu_seconds_total và nginx_up. Giải thích /metrics của web được cấp dữ liệu từ Nginx Exporter.
10. Mở Grafana từ portal: admin / admin nếu chưa đổi. Dashboard System Health có CPU Usage, Memory Usage, Network Traffic. Đợi tối thiểu hai lần scrape cho rate có dữ liệu.

## Kiểm thử bổ sung

```powershell
docker compose exec -T web-frontend-server nginx -t
docker compose exec -T api-gateway-proxy-server nginx -t
docker compose exec -T internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local
docker compose exec -T internal-dns-server dig '@127.0.0.1' app-backend.cloud.local +short
docker compose exec -T relational-database-server mariadb -uroot -proot -e 'SELECT * FROM minicloud.notes; SELECT * FROM studentdb.students;'
docker compose run --rm --no-deps --entrypoint python storage-init /bootstrap/verify.py
```

## EC2 sau khi local được nghiệm thu

Theo README.md. Thay localhost bằng Public IP trong URL trình duyệt và issuer; không thay tên service nội bộ. Link portal tự lấy hostname. DNS/SQL/docker exec phải chạy qua SSH trên EC2. Lưu ảnh mỗi mục, link Docker Hub đã push và video thật trước khi đánh dấu hoàn thành triển khai.
