from pathlib import Path
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

root = Path(__file__).resolve().parents[1]
out = root / "object-storage-server/bootstrap/minicloud-report.pdf"
pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("ArialBold", "C:/Windows/Fonts/arialbd.ttf"))
styles = getSampleStyleSheet()
for name in ("Normal", "Title", "Heading1", "Heading2"):
    styles[name].fontName = "ArialBold" if name != "Normal" else "Arial"
styles["Normal"].fontSize = 11
styles["Normal"].leading = 17
styles["Normal"].spaceAfter = 10
styles["Title"].fontSize = 24
styles["Title"].leading = 32
styles["Heading1"].fontSize = 18
styles["Heading1"].leading = 26
chapters = [
 ("Chương 1 Giới thiệu và mục tiêu", [
  "MyMiniCloud mô phỏng chín loại dịch vụ cloud trên mạng Docker cloud-net. Cổng tổng hợp cung cấp liên kết đến blog, ứng dụng, xác thực, lưu trữ và giám sát; người dùng có thể đọc sinh viên từ JSON hoặc MariaDB, tra cứu DNS và kiểm thử tài nguyên bảo vệ.",
  "Đạt phụ trách Web Nginx, Gateway, Bind9, blog và Round Robin. Tài phụ trách Flask, MariaDB, Keycloak. Quý phụ trách MinIO, Prometheus, Grafana và tích hợp AWS. Báo cáo này là bản kỹ thuật cho kiểm thử local; chưa phải minh chứng đã triển khai AWS.",
  "Phạm vi mở rộng gồm 10 mục: blog ba bài; JSON sinh viên; studentdb; realm và token; hai bucket; bản ghi DNS; giám sát web; dashboard ba biểu đồ; route /student/; cân bằng tải hai web. MSSV và họ tên đầy đủ cần nhóm bổ sung trước khi nộp." ]),
 ("Chương 2 Kiến trúc và luồng request", [
  "Trình duyệt gửi HTTP đến gateway cổng 80. Request web đi vào upstream gồm web-frontend-server1 và web-frontend-server2, dùng Round Robin. Các request /api/ được bỏ tiền tố trước khi tới Flask cổng 8081. /student/ ánh xạ tới /student. /auth/ giữ nguyên đường dẫn tới Keycloak.",
  "Flask /student đọc students.json, /students-db truy vấn studentdb.students. Người dùng lấy token từ Keycloak realm_sv001 rồi gửi Bearer token đến /secure. Flask xác minh chữ ký RS256, issuer và audience bằng JWKS nội bộ.",
  "Bind9 phục vụ cloud.local: web 10.10.10.10, backend .20, MinIO .30, Keycloak .40, DNS .53. Docker DNS tiếp tục phân giải tên service; API /dns chủ động truy vấn Bind9. Prometheus scrape Node Exporter và metric Nginx; Grafana đọc Prometheus để hiển thị CPU, RAM và network." ]),
 ("Chương 3 Cấu hình và đóng gói", [
  "docker-compose.yml mô tả image, build context, network, port, volume và restart policy. Web dùng nginx:stable, chép html và conf.default vào image. Backend dùng Python 3.11 Alpine với Flask, python-jose, pymysql, requests, dnspython. MinIO được biên dịch bằng Dockerfile nhiều giai đoạn từ mã Go.",
  "MariaDB dùng db-data-v2 và healthcheck; volume db-data cũ lỗi InnoDB được giữ để phục hồi. Keycloak dùng keycloak-data và import realm mẫu nếu realm chưa có. Hai user sv01, sv02 có mật khẩu lab 123456; client flask-app là public. Grafana provision datasource và dashboard từ file; Prometheus có volume lịch sử.",
  "Bootstrap S3 tạo profile-pics cho tải ảnh công khai và documents riêng tư, upload avatar.jpg và PDF này. MinIO tiếp tục dùng dữ liệu bind mount hiện tại. Không dùng docker compose down -v để bảo toàn dữ liệu. OIDC_ISSUER cấu hình theo địa chỉ công khai khi chuyển môi trường." ]),
 ("Chương 4 Demo và kiểm thử", [
  "Chạy docker compose up -d --build, đợi MariaDB healthy và Keycloak sẵn sàng. Mở cổng tổng tại http://localhost/. Kiểm tra ba bài blog có hình và liên kết; chuyển nguồn sinh viên JSON sang MariaDB; kiểm thử đăng nhập sv01 và sv02.",
  "Nhấn kiểm tra phân phối để quan sát X-Served-By từ hai web; nhấn tra cứu DNS để kiểm tra bốn tên miền. Mở MinIO Console cổng 9001, kiểm tra profile-pics/avatar.jpg tải công khai và documents/minicloud-report.pdf tải bằng tài khoản. Mở Prometheus cổng 9090 để xem node/web UP; Grafana cổng 3000 hiển thị dashboard ba panel.",
  "scripts/test-project.ps1 kiểm tra HTTP, dữ liệu, DNS, token, lỗi 401, Round Robin, metric và dashboard. scripts/check-browser.cjs kiểm tra tương tác và chụp giao diện desktop/mobile. Kết quả kiểm thử và ảnh chụp cần đính kèm bản nộp, không thay thế bằng mô tả kỳ vọng." ]),
 ("Chương 5 Đánh giá và hướng phát triển", [
  "Ưu điểm: cấu hình dịch vụ trong mã nguồn, tách trách nhiệm rõ ràng, có volume dữ liệu, hai web và quy trình kiểm thử lặp lại. Khó khăn đã gặp gồm dữ liệu MariaDB hỏng, Keycloak khởi động chậm, URL issuer khác giữa máy và route /auth không đồng bộ.",
  "Giới hạn: một máy chủ chưa có tính sẵn sàng cao ở cấp hạ tầng; chỉ web được cân bằng tải; Node Exporter local phản ánh Linux Docker Desktop. Tài khoản và HTTP là cấu hình lab. Sản phẩm thực tế cần TLS, quản lý secrets, OIDC Authorization Code với PKCE và backup định kỳ.",
  "Phụ lục triển khai: README.md mô tả EC2, Security Group, override Linux và Docker Hub. Nhóm cần bổ sung Public IP/domain thực tế, MSSV cho realm/dashboard theo yêu cầu giảng viên, link image đã xuất bản, video demo và minh chứng AWS. Không đánh dấu các mục này hoàn thành trước khi thực hiện." ])
]
story = []
for index, (title, paragraphs) in enumerate(chapters):
    if index:
        story.append(PageBreak())
    else:
        story.extend([Paragraph("Báo cáo kỹ thuật MyMiniCloud", styles["Title"]), Paragraph("Bản tích hợp local của Đạt, Tài và Quý", styles["Normal"]), Spacer(1, 18)])
    story.append(Paragraph(title, styles["Heading1"]))
    story.append(Spacer(1, 14))
    story.extend(Paragraph(escape(text), styles["Normal"]) for text in paragraphs)
def footer(canvas, doc):
    canvas.setFont("Arial", 9)
    canvas.setFillColor(colors.HexColor("#526766"))
    canvas.drawString(44, 30, "MyMiniCloud | Báo cáo kỹ thuật local")
    canvas.drawRightString(550, 30, str(doc.page))
SimpleDocTemplate(str(out), title="Báo cáo kỹ thuật MyMiniCloud", author="Đạt, Tài, Quý", leftMargin=44, rightMargin=44, topMargin=44, bottomMargin=50).build(story, onFirstPage=footer, onLaterPages=footer)
print(out)
