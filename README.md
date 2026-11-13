# MyMiniCloud

Cổng tổng hợp dịch vụ của nhóm. Trang chính ở http://localhost/ chỉ hiển thị danh sách dịch vụ. Bảng sinh viên JSON/DB, kiểm thử Round Robin, DNS và tài nguyên bảo vệ nằm trong các trang riêng khi chọn dịch vụ tương ứng.

## Khởi động local

```powershell
docker compose up -d --build
docker compose ps
```

Chờ MariaDB healthy và Keycloak khởi động xong. `storage-init` kết thúc với exit code 0 là bình thường.

| Dịch vụ | URL | Tài khoản lab |
|---|---|---|
| Cổng tổng | http://localhost/ | Không cần |
| Blog | http://localhost/blog/ | Không cần |
| Keycloak | http://localhost/auth/admin/ | admin / admin |
| Kiểm thử tài nguyên bảo vệ | http://localhost/service.html?view=identity | sv01 hoặc sv02 / 123456 |
| MinIO Console | http://localhost:9001/ | minioadmin / minioadmin |
| Prometheus | http://localhost:9090/targets | Không cần |
| Grafana | http://localhost:3000/d/minicloud-health | admin / admin, trừ khi đã đổi |

Realm mẫu chỉ được import khi realm chưa tồn tại; không ghi đè cấu hình realm có sẵn. Login trên portal là luồng cấp token trực tiếp để demo đề tài, token chỉ giữ trong biến tạm và không lưu localStorage. Đây chưa phải luồng SSO Authorization Code của sản phẩm thực tế.

## Dữ liệu và khả năng tái tạo

- MariaDB dùng volume `db-data-v2`. Volume `db-data` cũ bị lỗi InnoDB được giữ nguyên để phục hồi, không bị xóa.
- Keycloak dùng `keycloak-data`; cấu hình mẫu nằm tại `authentication-identity-server/realm_sv001.json`.
- Grafana và Prometheus dùng volume riêng; datasource/dashboard được provision từ mã nguồn.
- MinIO giữ dữ liệu hiện tại trong `object-storage-server/data`. Bootstrap tạo profile-pics (public download), documents (private), avatar.jpg và `documents/minicloud-report.pdf`. PDF là báo cáo kỹ thuật local năm chương; thay/bổ sung bản nộp cuối sau khi có thông tin nhóm và minh chứng EC2.
- SQL init chỉ chạy lần đầu trên volume DB rỗng. Không dùng `down -v` nếu muốn giữ dữ liệu.
- Dữ liệu nhạy cảm, backup và artifacts kiểm thử không commit lên Git.

## Kiểm thử

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-project.ps1
```

Script trả exit code khác 0 nếu có bước thất bại. Test DNS trực tiếp trong Docker phải chạy trên máy chứa dự án. Để test EC2 từ Windows, dùng `-BaseUrl http://PUBLIC_IP -SkipDocker`; DNS và kết nối nội bộ cần kiểm tra thêm qua SSH trên EC2.

Node Exporter local phản ánh môi trường Linux của Docker Desktop. EC2 dùng override để đọc root filesystem host; network metrics cần diễn giải theo namespace mạng của container. Prometheus web job giám sát web 1 qua Nginx Exporter.

## AWS EC2 Ubuntu

1. Chuẩn bị EC2 có Docker Engine và Docker Compose, đủ RAM cho Keycloak/Grafana (khuyến nghị ít nhất 4 GiB cho lab).
2. Clone repository, tạo `.env` theo `.env.example`. Đặt `OIDC_ISSUER=http://PUBLIC_IP/auth/realms/realm_sv001` và Docker Hub namespace của nhóm.
3. Sao lưu dữ liệu trên EC2 trước khi thay đổi cấu hình mạng/container. Nếu network cloud-net cũ khác subnet, dừng riêng stack này và tạo lại mạng; không xóa volume dữ liệu.
4. Chạy `docker compose -f docker-compose.yml -f docker-compose.ec2.yml up -d --build`.
5. Security Group: mở HTTP 80 cho người xem; 3000, 9001, 9090 chỉ cho IP người demo khi cần mở các giao diện riêng. SSH 22 chỉ cho IP quản trị. Không cần public DB hay DNS.
6. Mở portal bằng Public IP. Các link dịch vụ tự dùng hostname hiện tại; issuer phải khớp URL lấy token.
7. Realm lab cho phép HTTP để demo. Khi triển khai thực tế, cấu hình domain/TLS và đổi thông tin đăng nhập mẫu.

## Docker Hub và minh chứng

```powershell
docker login
docker compose build web-frontend-server application-backend-server
docker compose push web-frontend-server application-backend-server
```

Chỉ chạy push khi đã chọn đúng namespace và được phép xuất bản. Việc có tên image trong Compose không chứng minh image đã được push. Báo cáo cuối kỳ cần thêm MSSV, ảnh kiểm thử thực tế, link Docker Hub, video và kết quả EC2; chưa ghi hoàn thành các mục bên ngoài nếu chưa có minh chứng.
