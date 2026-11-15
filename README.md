# MyMiniCloud

Đồ án môn Điện toán đám mây mô phỏng chín nhóm dịch vụ bằng Docker Compose, chạy trên laptop và AWS EC2 Ubuntu. Bản cấu hình này triển khai **13 container**, gồm hai Web Server phục vụ cân bằng tải và các exporter hỗ trợ giám sát.

- Repository: https://github.com/nguyenvantai-imfine/cloud-computing
- Docker Hub MinIO: https://hub.docker.com/r/quyn1305/myminicloud-minio
- Image MinIO: `quyn1305/myminicloud-minio:2025-10-15`
- EC2 đã dùng để demo: `56.10.26.60`.

## 1. Thành phần và cấu hình

| Nhóm | Service | Cổng trên máy chạy Docker |
|---|---|---|
| Web | `web-frontend-server`, `web-frontend-server2` | 8080, 8082 |
| Backend | `application-backend-server` | 8085, chuyển tới 8081 trong container |
| Database | `relational-database-server` | 3307 khi dùng cấu hình local; 3306 trong cấu hình cơ sở |
| Authentication | `authentication-identity-server` | 8081, chuyển tới 8080 trong container |
| Object Storage | `object-storage-server` | 9000 API, 9001 Console |
| DNS | `internal-dns-server` | UDP 1053, chuyển tới 53 trong container |
| Monitoring | `monitoring-prometheus-server`, `monitoring-node-exporter-server`, `web-nginx-exporter`, `web-nginx-exporter2` | 9090, 9100; exporter Web dùng 9113 nội bộ |
| Dashboard | `monitoring-grafana-dashboard-server` | 3000 |
| Gateway | `api-gateway-proxy-server` | 80; thêm 443 khi dùng cấu hình EC2 |

Các container cùng mạng `cloud-net`, subnet `10.10.10.0/24`. IP cố định: Web 1 `.10`, Backend `.20`, MinIO `.30`, Keycloak `.40`, Bind9 `.53`. Giữ IP Backend `10.10.10.20` để khớp zone DNS.

| File | Mục đích |
|---|---|
| `docker-compose.yml` | Cấu hình cơ sở, hai Web Server và hai exporter |
| `docker-compose.local.yml` | Lưu dữ liệu Keycloak local, đổi cổng MariaDB trên laptop thành 3307 |
| `docker-compose.ec2.yml` | HTTPS Gateway, issuer EC2, biến môi trường MinIO và volume Keycloak EC2 |
| `api-gateway-proxy-server/nginx.conf` | Gateway local HTTP |
| `api-gateway-proxy-server/nginx.ec2.conf` | Gateway EC2 HTTP và HTTPS |
| `monitoring-prometheus-server/prometheus.yml` | Thu thập Node và hai exporter Web |
| `monitoring-grafana-dashboard-server/system-health-52400153.json` | Dashboard cần thêm vào repo từ bản export Grafana |
| `.env.example` | Mẫu biến môi trường cho EC2, không phải tài khoản triển khai thật |

Realm/user Keycloak, bucket và file MinIO, datasource/dashboard Grafana là dữ liệu cấu hình khi chạy. Git clone không tự phục hồi những dữ liệu này. Thực hiện mục 4–6 khi chạy lần đầu.

## 2. Chạy local trên Windows

### Điều kiện

- Docker Desktop đang chạy Linux containers, có Docker Compose V2 hỗ trợ `!override` trong file local.
- Git và trình duyệt. Dùng PowerShell tại thư mục chứa `docker-compose.yml`.
- Cổng 80, 8080, 8082, 8085, 8081, 9000, 9001, 9090, 3000 và 3307 còn trống.
- Mạng Docker `cloud-net` chưa tồn tại với subnet khác. Xem mục 9 nếu máy có bản cũ.

### Tải và khởi động

Clone một lần, hoặc dùng thư mục repo đã có. Nếu đang chuẩn bị merge, không clone đè hay pull vào thư mục có thay đổi chưa lưu.

```powershell
git clone https://github.com/nguyenvantai-imfine/cloud-computing.git
cd cloud-computing
```

Dùng nhánh đã chứa đủ các file local/EC2; trong giai đoạn chưa merge, nhánh triển khai là `quy/fix-ec2-config`.

```powershell
docker compose version
docker pull quyn1305/myminicloud-minio:2025-10-15
docker tag quyn1305/myminicloud-minio:2025-10-15 myminicloud-minio:2025-10-15
docker compose -f docker-compose.yml -f docker-compose.local.yml config -q
docker compose -f docker-compose.yml -f docker-compose.local.yml build web-frontend-server application-backend-server
docker compose -p cloud-computing -f docker-compose.yml -f docker-compose.local.yml up -d --no-build
docker compose -p cloud-computing -f docker-compose.yml -f docker-compose.local.yml ps -a
```

Hai Web Server dùng cùng image Web vừa build. MinIO sử dụng image đã tải và tag; `--no-build` tránh build lại MinIO từ Go khi chỉ cần chạy demo. Các image dịch vụ khác được Docker tải khi chưa có. Chờ Keycloak, MariaDB khởi động rồi kiểm tra chức năng, không chỉ dựa vào trạng thái Up.

### Các địa chỉ local

| Chức năng | Địa chỉ |
|---|---|
| Trang chủ và blog | http://localhost/ và http://localhost/blog/ |
| API Hello | http://localhost/api/hello |
| Sinh viên từ JSON | http://localhost/api/student |
| Sinh viên từ MariaDB | http://localhost/api/students-db |
| Route Gateway sinh viên | http://localhost/student/ |
| Keycloak Admin | http://localhost:8081/auth/admin/ |
| MinIO Console | http://localhost:9001 |
| Avatar công khai | http://localhost:9000/profile-pics/avatar.jpg |
| Prometheus | http://localhost:9090/targets |
| Grafana | http://localhost:3000 |

Local lấy token qua **`http://localhost:8081/auth/...`** để khớp `OIDC_ISSUER` mặc định của Backend. Nếu dùng issuer khác, đổi đồng bộ cấu hình Backend và endpoint lấy token; không trộn issuer có cổng 8081 với issuer qua Gateway cổng 80.

MariaDB local dùng `localhost:3307` cho Workbench. Backend vẫn kết nối tên service `relational-database-server:3306` trong mạng Docker.

## 3. Chạy trên AWS EC2

### Máy EC2 mới

Chuẩn bị Ubuntu, Docker Engine và Docker Compose V2. Clone repo vào `~/cloud-computing`, dùng nhánh chứa đủ cấu hình. Các lệnh dưới đây chạy trong **terminal SSH Ubuntu**, không phải PowerShell laptop.

Security Group cho phép các cổng thực sự cần demo: TCP 80, 443, 8080, 8082, 8085, 8081, 9000, 9001, 9090, 3000; UDP 1053 nếu kiểm tra DNS từ bên ngoài. SSH TCP 22 nên giới hạn IP người quản trị. Không cần mở công khai 3306, 9100 hay 9113 cho các luồng nội bộ của bài.

Trong `docker-compose.ec2.yml`, sửa `OIDC_ISSUER` nếu dùng IP hoặc tên miền khác `56.10.26.60`. Issuer phải trùng URL Keycloak dùng để cấp token.

```bash
cd ~/cloud-computing
test -f .env || cp .env.example .env
chmod 600 .env
nano .env
```

Điền tài khoản MinIO thật vào `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`. Không giữ nguyên `CHANGE_ME_BEFORE_DEPLOYING`. Nếu EC2 đã có `.env`, giữ tài khoản đang dùng, không chép mẫu đè lên. File này không đưa lên Git.

Tạo chứng chỉ tự ký cho bản demo mới. **Không chạy đè nếu đã có chứng chỉ đang dùng**. Ví dụ với IP demo:

```bash
mkdir -p api-gateway-proxy-server/certs
openssl req -x509 -nodes -days 90 -newkey rsa:2048 \
  -keyout api-gateway-proxy-server/certs/server.key \
  -out api-gateway-proxy-server/certs/server.crt \
  -subj '/CN=56.10.26.60' \
  -addext 'subjectAltName=IP:56.10.26.60'
chmod 600 api-gateway-proxy-server/certs/server.key
```

Nếu IP khác, thay cả CN và subjectAltName trước khi tạo chứng chỉ. Thư mục certs được bỏ qua bởi Git.

```bash
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml config -q
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml pull object-storage-server
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml build web-frontend-server application-backend-server
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml up -d --no-build
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml ps -a
```

Các URL demo dùng IP EC2 thay `localhost`. Keycloak EC2 đăng nhập qua **https://56.10.26.60/auth/admin/**. Trình duyệt có thể cảnh báo chứng chỉ tự ký; `curl -k` chỉ dùng bỏ kiểm tra chứng chỉ trong môi trường demo này.

### EC2 đã có dữ liệu

Không coi các lệnh cho máy mới là quy trình di chuyển dữ liệu. Trước khi thay Compose, sao lưu Database, Grafana, MinIO và Keycloak. Nếu Keycloak cũ chưa có volume, việc tạo lại container có thể làm mất realm/user trong lớp dữ liệu của container. Cần dừng Keycloak, sao lưu thư mục `/opt/keycloak/data` và phục hồi vào volume phù hợp trước khi tạo lại.

Không dùng `docker compose down -v`, xóa volume hay xóa dữ liệu MinIO để xử lý lỗi thông thường. Dữ liệu demo cũ không nằm trong Git. Với EC2 đang hoạt động và đã quay video, bổ sung README hoặc export dashboard vào repo không yêu cầu triển khai lại.

## 4. Thiết lập Keycloak lần đầu

1. Mở Keycloak Admin theo URL local hoặc EC2 ở trên. Với dữ liệu mới, cấu hình hiện tại bootstrap tài khoản `admin`/`admin`; volume cũ có thể dùng tài khoản đã đổi trước đó.
2. Tạo realm **`realm_sv001`**.
3. Tạo hai user **`sv01`**, **`sv02`**, bật Enabled, điền tên và email kiểm thử.
4. Trong Credentials, đặt mật khẩu cho mỗi user, tắt **Temporary**. Đảm bảo không còn Required actions chặn việc lấy token bằng mật khẩu.
5. Tạo client OpenID Connect **`flask-app`**, Client authentication **Off**, bật **Direct access grants** cho bài kiểm thử. Có thể giữ Standard flow bật; nếu dùng đăng nhập tương tác qua trình duyệt, cần cấu hình redirect URI phù hợp.
6. Backend hiện kiểm tra audience **`account`**. Token dùng cho demo phải có audience này; nếu cấu hình client scope thay đổi, kiểm tra hoặc thêm audience mapper phù hợp. Không tắt kiểm tra JWT để làm API trả thành công.

Luồng Direct access grants được dùng để kiểm thử theo bài học. Việc chuẩn bị tài khoản trên local và trên EC2 là độc lập; tạo trên EC2 không tự xuất hiện ở local.

## 5. Thiết lập MinIO lần đầu

Local mới dùng tài khoản trong Compose: `minioadmin`/`minioadmin`. EC2 dùng tài khoản đã điền trong `.env`; không mặc định giống local. Khi dùng dữ liệu cũ, giữ tài khoản triển khai thực tế.

Trong Console:

1. Tạo bucket `profile-pics`, upload đúng tên **`avatar.jpg`**.
2. Tạo bucket `documents`, upload file PDF báo cáo.
3. Chỉ cấp quyền đọc ẩn danh cho đối tượng avatar. Giữ `documents` riêng tư.

Có thể dùng MinIO Client `mc` nếu đã cài. `mc` là MinIO Client, không phải công cụ cùng tên khác. Lệnh Bash dưới đây nhập Secret Key tương tác; không ghi khóa thật vào README:

```bash
mc alias set myminicloud http://localhost:9000 YOUR_MINIO_USER
cat > /tmp/avatar-policy.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": ["*"]},
    "Action": ["s3:GetObject"],
    "Resource": ["arn:aws:s3:::profile-pics/avatar.jpg"]
  }]
}
JSON
mc anonymous set-json /tmp/avatar-policy.json myminicloud/profile-pics
```

Thay `YOUR_MINIO_USER` bằng username thật. Lệnh policy áp dụng cho bucket `profile-pics`; xem lại policy hiện có nếu bucket đã có chính sách khác. Upload avatar bằng Console trước khi thử URL, tránh lỗi không có đối tượng.

Tải PDF bằng nút Download trong Console đã đăng nhập. URL trực tiếp của object không tự kế thừa phiên đăng nhập Console. Khi kiểm tra PDF riêng tư, dùng đúng tên file tồn tại; tên có dấu cách và tiếng Việt phải được URL-encode.

## 6. Thiết lập Grafana lần đầu

1. Mở Grafana cổng 3000. Với dữ liệu mới, đăng nhập `admin`/`admin` và đặt mật khẩu; volume cũ giữ tài khoản đã thiết lập.
2. Connections → Data sources → Add data source → Prometheus.
3. URL datasource: **`http://monitoring-prometheus-server:9090`**. Đây là kết nối từ container Grafana, không dùng `localhost:9090`.
4. Save & test, xác nhận truy vấn Prometheus thành công.
5. Dashboards → Import → chọn `monitoring-grafana-dashboard-server/system-health-52400153.json`.
6. Nếu có mục chọn datasource khi import, chọn Prometheus vừa tạo. Nếu không có và dashboard báo No data, sửa datasource các panel sang datasource này.
7. Chọn Last 15 minutes, refresh 10s, kiểm tra Node 1/1 UP, Web 2/2 UP và ba biểu đồ CPU, Memory, Network.

File JSON phải được thêm vào Git trước khi phát hành bộ code. Nếu chưa thấy file này trong thư mục, export dashboard đã demo từ Grafana, bật tùy chọn chia sẻ bên ngoài nếu có và lưu đúng đường dẫn trên. Không kết luận dashboard sẽ tự có ngay sau `up` vì bản Compose hiện tại chưa tự provision Grafana.

## 7. Kiểm thử

### Qua trình duyệt

Kiểm tra trang chủ, ba bài `blog1.html`, `blog2.html`, `blog3.html` dưới `/blog/`; API `/api/hello`, `/api/student`, `/api/students-db`, `/student/`; Console MinIO; Prometheus Targets và Grafana. Sau thay đổi dữ liệu của nhóm, đếm kết quả thực tế, không mặc định luôn đúng năm sinh viên. Yêu cầu mở rộng tối thiểu là năm bản ghi API JSON và ba bản ghi Database.

### SQL trực tiếp — terminal Ubuntu EC2

```bash
sudo docker exec relational-database-server sh -c 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -u root -e "SELECT * FROM studentdb.students;"'
```

Script init SQL chỉ tự chạy khi thư mục dữ liệu MariaDB mới, không tự chạy lại khi Git pull. Backend hiện dùng `DB_PASSWORD` mặc định `root`; nếu Database đang dùng mật khẩu khác, cấu hình Backend cùng tài khoản thật trước khi chạy, không chỉ đổi mật khẩu Database đơn lẻ.

### DNS — terminal Ubuntu EC2

```bash
for name in web-frontend-server app-backend minio keycloak; do
  printf '%s.cloud.local -> ' "$name"
  dig @127.0.0.1 -p 1053 "$name.cloud.local" +short
done
```

Kỳ vọng lần lượt `10.10.10.10`, `.20`, `.30`, `.40`. Trên PowerShell laptop có thể dùng `nslookup -port=1053 app-backend.cloud.local localhost` cho local, hoặc thay `localhost` bằng IP EC2 khi Security Group cho phép UDP 1053.

### Token — terminal Ubuntu EC2

Đoạn dưới dùng issuer EC2. Khi kiểm tra local từ PowerShell, dùng endpoint local cổng 8081 với công cụ HTTP phù hợp; không dán nguyên Bash vào PowerShell.

```bash
read -rs -p 'Nhap mat khau sv01: ' SV_PASS </dev/tty; echo
TOKEN_JSON=$(curl -ksS --max-time 15 \
  -X POST 'https://56.10.26.60/auth/realms/realm_sv001/protocol/openid-connect/token' \
  --data-urlencode 'grant_type=password' \
  --data-urlencode 'client_id=flask-app' \
  --data-urlencode 'username=sv01' \
  --data-urlencode "password=$SV_PASS")
unset SV_PASS
TOKEN=$(printf '%s' "$TOKEN_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
if [ -n "$TOKEN" ]; then
  echo 'Lay access token: THANH CONG'
  curl -ksS -w '\nHTTP %{http_code}\n' https://56.10.26.60/api/secure -H "Authorization: Bearer $TOKEN"
else
  printf '%s\n' "$TOKEN_JSON"
fi
unset TOKEN TOKEN_JSON
curl -ksS -w '\nHTTP %{http_code}\n' https://56.10.26.60/api/secure
```

Có token hợp lệ: HTTP 200, `Secure resource OK`, username sv01. Không token: HTTP 401, `Missing Bearer token`. Lấy token mới mỗi lượt kiểm thử, không đưa token vào Git hoặc video.

### Token local — PowerShell laptop

Điền mật khẩu `sv01` local trong hộp nhập thông tin; dữ liệu user local độc lập với EC2.

```powershell
$credential = Get-Credential -UserName sv01 -Message "Tai khoan Keycloak local"
$password = $credential.GetNetworkCredential().Password
$tokenResponse = curl.exe -sS -X POST "http://localhost:8081/auth/realms/realm_sv001/protocol/openid-connect/token" --data-urlencode "grant_type=password" --data-urlencode "client_id=flask-app" --data-urlencode "username=sv01" --data-urlencode "password=$password" | ConvertFrom-Json
Remove-Variable password
if ($tokenResponse.access_token) {
    curl.exe -sS -i "http://localhost/api/secure" -H "Authorization: Bearer $($tokenResponse.access_token)"
} else {
    $tokenResponse | ConvertTo-Json
}
Remove-Variable tokenResponse, credential
curl.exe -sS -i "http://localhost/api/secure"
```

Không thay endpoint cấp token local thành cổng 80 nếu Backend vẫn kiểm tra issuer cổng 8081. Cổng API bảo vệ qua Gateway vẫn là 80, không cần trùng cổng cấp token.

### Prometheus

- Targets: Node `1/1 UP`, Web `2/2 UP`.
- Query `node_cpu_seconds_total`: có dữ liệu.
- Query `nginx_up{job="web"}`: hai dòng đều bằng 1.
- `up=1` xác nhận scrape exporter thành công; `nginx_up=1` bổ sung xác nhận exporter đọc được Nginx.

Hai exporter dùng `/stub_status` nội bộ cổng 8081 của từng Web Server, không phải cổng 8081 công khai của Keycloak.

### Round Robin — terminal Ubuntu EC2

```bash
for i in $(seq 1 8); do
  printf 'Request %s: ' "$i"
  curl -sI http://56.10.26.60/ | grep -i '^X-Served-By:'
done
```

Kết quả có cả `web-frontend-server1` và `web-frontend-server2`. Khi có lưu lượng khác cùng lúc, thứ tự quan sát có thể xen kẽ. Đối với local PowerShell, có thể mở trang chủ và đối chiếu nhãn server sau khi tải lại, hoặc dùng `curl.exe -I http://localhost/` nhiều lần.

### Ping rút gọn — terminal Ubuntu EC2

```bash
sudo docker run --rm --network cloud-net alpine:3.20 sh -c '
for host in web-frontend-server web-frontend-server2 application-backend-server relational-database-server authentication-identity-server object-storage-server internal-dns-server monitoring-prometheus-server monitoring-grafana-dashboard-server monitoring-node-exporter-server api-gateway-proxy-server web-nginx-exporter web-nginx-exporter2; do
  if ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
    echo "PASS $host"
  else
    echo "FAIL $host"
  fi
done'
```

Đây là kiểm tra từ container tạm tới từng dịch vụ, không phải mọi cặp container. Container tạm tự xóa sau kiểm tra.

`script.md` trong bản cũ là các đoạn PowerShell kiểm thử, không phải script Ubuntu. Trước khi dùng bản đó cần cập nhật endpoint token HTTPS của EC2 và phép thử tài liệu MinIO trỏ đúng đối tượng; có thể dùng các phép thử riêng ở mục này trong khi script đang được hoàn thiện.

## 8. Dừng và chạy lại

Local:

```powershell
docker compose -p cloud-computing -f docker-compose.yml -f docker-compose.local.yml stop
docker compose -p cloud-computing -f docker-compose.yml -f docker-compose.local.yml up -d --no-build
```

EC2:

```bash
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml stop
sudo docker compose --env-file .env -p cloud-computing -f docker-compose.yml -f docker-compose.ec2.yml up -d --no-build
```

Không thêm `-v`. Local và EC2 độc lập, có thể chạy đồng thời. Người xem demo qua trình duyệt không cần Docker hoặc SSH; EC2 cần tiếp tục Running. Tắt laptop không tắt EC2.

## 9. Xử lý lỗi thường gặp

- **Không nhận `!override`:** dùng Docker Compose V2 đủ mới hỗ trợ tag này; không xóa `!override` tùy tiện vì có thể giữ cả cổng 3306 đang xung đột.
- **Cổng local 3306 bị chiếm:** dùng file local để publish 3307; không dừng tiến trình lạ hoặc xóa Database chỉ để giải phóng cổng.
- **Mạng cloud-net tồn tại với subnet khác:** kiểm tra `docker network inspect cloud-net`. Sao lưu dữ liệu trước nếu đang dùng cấu hình cũ. Chỉ tạo lại mạng khi đã xác định các container phụ thuộc và có kế hoạch di chuyển; không xóa mạng đang dùng hoặc volume để thử nhanh.
- **Exporter báo no such host:** kiểm tra container và alias mạng. Có thể tạo lại riêng exporter local bằng `docker compose -p cloud-computing -f docker-compose.yml -f docker-compose.local.yml up -d --no-build --no-deps --force-recreate web-nginx-exporter`. Không cần tạo lại Database.
- **Keycloak HTTP public báo HTTPS required:** dùng HTTPS qua Gateway trên EC2. Tạo chứng chỉ, mở 443 và kiểm tra issuer, không bỏ xác thực để né lỗi.
- **`invalid_grant`:** kiểm tra realm, user, mật khẩu, Enabled, Temporary và Required actions. Mật khẩu cần được nhập lại sau khi biến đã unset.
- **API token 401:** đối chiếu issuer, audience `account`, JWKS URL và thời hạn token. Thiếu token trả 401 là kết quả đúng.
- **Grafana No data:** kiểm tra datasource dùng tên service Prometheus, ánh xạ datasource sau import, Targets và khoảng thời gian.
- **MinIO NoSuchKey:** kiểm tra đúng bucket, tên file và chữ hoa/thường. 403 với PDF ẩn danh không tự chứng minh file tồn tại; cần thấy file trong Console và thử tải có đăng nhập.
- **SSH timeout:** kiểm tra EC2 Running, Elastic IP, Security Group thực sự gắn với instance và IP công khai hiện tại của người truy cập. IP Wi-Fi phía người dùng có thể thay đổi, dù EC2 có Elastic IP.
- **Terminal hiện dấu `>`:** thường còn thiếu nháy đóng hoặc đang nhập khối nhiều dòng. `Ctrl+C` hủy lệnh đang nhập, không hoàn tác lệnh đã thực thi.

## 10. Dữ liệu và phạm vi bài học

- MariaDB: named volume `db-data`; Grafana: `grafana-data`.
- Keycloak: `keycloak-data-local` khi chạy local, `keycloak-data` khi chạy EC2.
- MinIO: bind mount `./object-storage-server/data`.
- Prometheus hiện chưa có named volume lịch sử, nên không coi lịch sử metrics là dữ liệu đã được sao lưu bền vững khi tạo lại container.
- Node Exporter hiện chạy theo cấu hình Compose có sẵn. Không có cAdvisor hoặc exporter riêng cho từng ứng dụng; không mô tả các biểu đồ hiện tại là số liệu chi tiết của từng container.
- Keycloak start-dev, tài khoản mẫu, HTTP và TLS tự ký phục vụ học tập. Triển khai thực tế cần quản lý bí mật, TLS tin cậy, phân quyền và giới hạn cổng phù hợp.

Không commit `.env` thật, `.pem`, khóa TLS riêng, runtime data hoặc backup. Chỉ commit `.env.example`, cấu hình, source và dashboard export đã kiểm tra.

Khi ghép hồ sơ nộp bài, bổ sung link video demo local/EC2 và báo cáo của nhóm vào phụ lục sau khi có link chính thức. README này không tự xác nhận các thay đổi sau cùng đã được chạy trên một máy mới; kiểm tra lại local/EC2 trước khi phát hành.
