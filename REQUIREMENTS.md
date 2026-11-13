# Đối chiếu yêu cầu

| Mục mở rộng | Cài đặt | Minh chứng local |
|---|---|---|
| 1 Blog | blog1.html, blog2.html, blog3.html; ảnh và liên kết | HTTP và trình duyệt |
| 2 JSON sinh viên | students.json, /student | Portal và test-project.ps1 |
| 3 Database | studentdb.students, 3 bản ghi, /students-db | Query SQL và portal |
| 4 Keycloak | realm_sv001, sv01/sv02, public client flask-app, /secure | Token của cả hai user + 401 khi thiếu/sai token |
| 5 MinIO | profile-pics/avatar.jpg, documents/minicloud-report.pdf | Download có xác thực và từ chối public PDF |
| 6 DNS | Zone cloud.local, bốn IP tĩnh | dig, named-checkzone, portal /api/dns |
| 7 Prometheus | node + web targets; exporter cho Nginx | UP và các metric có sample |
| 8 Grafana | Provision Prometheus, 3 panel CPU/RAM/network | Dashboard minicloud-health |
| 9 Gateway | /student/ ánh xạ /student | So sánh JSON trực tiếp qua gateway |
| 10 Round Robin | 2 web cùng image, header X-Served-By | 8 request có cả hai server |

Yêu cầu cơ bản: web, /hello, minicloud.notes, auth admin, S3 upload/download, DNS, metric, dashboard, reverse proxy và thông mạng có trong stack. Healthcheck chờ DB/backend/Keycloak; dữ liệu dùng volume hoặc bind mount.

Giới hạn trước nộp: tên realm/dashboard đang dùng mã ví dụ realm_sv001; cần MSSV thật theo hướng dẫn giảng viên. Avatar hiện là ảnh mẫu, thay ảnh cá nhân khi nộp. PDF là báo cáo kỹ thuật, cần bổ sung sơ đồ/ảnh minh chứng và thông tin nhóm cho bản nộp chính thức. Docker Hub push, AWS, video do nhóm thực hiện sau nghiệm thu local theo yêu cầu người dùng, chưa được xác nhận hoàn thành.
