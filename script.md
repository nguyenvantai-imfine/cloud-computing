# Kiểm thử MyMiniCloud trên local và EC2

Chạy khối PowerShell dưới đây trên **laptop Windows**, không dán vào terminal Ubuntu. Chọn local hoặc EC2 khi được hỏi. Hệ thống phải được khởi động và hoàn thành cấu hình theo README trước.

Script chỉ đọc dữ liệu, không tạo tài khoản, đổi policy, xóa file hoặc khởi động lại container. Đóng gói các URL theo cấu hình: local cấp token tại cổng 8081; EC2 cấp token bằng HTTPS qua Gateway. Tùy chọn `-k` chỉ dành cho chứng chỉ tự ký EC2 trong bài demo.

Đối với tài liệu MinIO, nhập **đúng tên PDF đang tồn tại trong bucket documents**. HTTP 403 chỉ xác nhận yêu cầu ẩn danh bị chặn; cần đối chiếu Console và thử tải có đăng nhập riêng để xác nhận file tồn tại, tải được.

## Chạy trên PowerShell

Copy toàn bộ nội dung **bên trong khối code**, không copy hai dòng dấu ba backtick.

```powershell
$targetMode = Read-Host "Nhap local hoac ec2"
if ($targetMode -notin @("local", "ec2")) {
    throw "Chi nhap local hoac ec2."
}

if ($targetMode -eq "local") {
    $serviceHost = "localhost"
    $authBase = "http://localhost:8081/auth"
    $secureUrl = "http://localhost/api/secure"
} else {
    $serviceHost = Read-Host "IP EC2 (Enter de dung 56.10.26.60)"
    if ([string]::IsNullOrWhiteSpace($serviceHost)) { $serviceHost = "56.10.26.60" }
    $authBase = "https://${serviceHost}/auth"
    $secureUrl = "https://${serviceHost}/api/secure"
}
$baseUrl = "http://${serviceHost}"

function HttpCode([string]$url) {
    $output = & curl.exe -k -sS --connect-timeout 5 --max-time 20 -o NUL -w "%{http_code}" $url
    if ($LASTEXITCODE -ne 0) { return "000" }
    return "$output".Trim()
}
function FetchJson([string]$url) {
    $raw = & curl.exe -k -f -sS --connect-timeout 5 --max-time 20 $url
    if ($LASTEXITCODE -ne 0) { throw "Khong doc duoc $url" }
    return ($raw | ConvertFrom-Json -ErrorAction Stop)
}
function ShowResult([string]$name, [bool]$ok, [string]$detail) {
    $state = if ($ok) { "PASS" } else { "FAIL" }
    "{0,-38} {1,-4} {2}" -f $name, $state, $detail
}

# 1. Blog: kiem tra cac trang, khong thay cho xem anh va bam lien ket.
$blogCodes = @(1..3 | ForEach-Object { HttpCode "${baseUrl}/blog/blog$_.html" })
ShowResult "1. Blog 3 bai HTTP 200" (@($blogCodes | Where-Object { $_ -ne "200" }).Count -eq 0) ($blogCodes -join ", ")

# 2. API JSON: toi thieu 5 sinh vien, khong dung de chung minh Database.
try {
    $students = @(FetchJson "${baseUrl}/api/student")
    ShowResult "2. API sinh vien JSON >=5" ($students.Count -ge 5) "$($students.Count) ban ghi"
} catch { ShowResult "2. API sinh vien JSON >=5" $false $_.Exception.Message }

# 3. API doc Database: truy van SQL truc tiep van can kiem tra rieng.
try {
    $dbStudents = @(FetchJson "${baseUrl}/api/students-db")
    ShowResult "3. API doc MariaDB >=3" ($dbStudents.Count -ge 3) "$($dbStudents.Count) ban ghi"
} catch { ShowResult "3. API doc MariaDB >=3" $false $_.Exception.Message }

# 4. Keycloak: khong in token, nhap tai khoan cua moi truong dang test.
$kcCredential = Get-Credential -UserName "sv01" -Message "Tai khoan Keycloak $targetMode trong realm_sv001"
try {
    if ($null -eq $kcCredential) { throw "Chua nhap tai khoan Keycloak." }
    $kcPassword = $kcCredential.GetNetworkCredential().Password
    $tokenRaw = & curl.exe -k -f -sS --connect-timeout 5 --max-time 20 -X POST "${authBase}/realms/realm_sv001/protocol/openid-connect/token" --data-urlencode "grant_type=password" --data-urlencode "client_id=flask-app" --data-urlencode "username=$($kcCredential.UserName)" --data-urlencode "password=$kcPassword"
    if ($LASTEXITCODE -ne 0) { throw "Lay token that bai: kiem tra user, mat khau, realm va Direct access grants." }
    $tokenResponse = $tokenRaw | ConvertFrom-Json -ErrorAction Stop
    if (-not $tokenResponse.access_token) { throw "Phan hoi khong co access_token." }
    $secureRaw = & curl.exe -k -f -sS --connect-timeout 5 --max-time 20 $secureUrl -H "Authorization: Bearer $($tokenResponse.access_token)"
    if ($LASTEXITCODE -ne 0) { throw "Token da cap nhung API bao ve chua chap nhan. Kiem tra issuer, audience va JWKS." }
    $secureResponse = $secureRaw | ConvertFrom-Json -ErrorAction Stop
    ShowResult "4a. API voi token" ($secureResponse.message -eq "Secure resource OK") "user=$($secureResponse.preferred_username)"
} catch { ShowResult "4a. API voi token" $false $_.Exception.Message }
finally {
    Remove-Variable kcPassword, tokenRaw, tokenResponse, kcCredential -ErrorAction SilentlyContinue
}
$anonymousCode = HttpCode $secureUrl
ShowResult "4b. API khong token" ($anonymousCode -eq "401") "HTTP $anonymousCode"

# 5. MinIO: kiem tra dung doi tuong, khong chi bucket URL.
$avatarCode = HttpCode "http://${serviceHost}:9000/profile-pics/avatar.jpg"
ShowResult "5a. Avatar public" ($avatarCode -eq "200") "HTTP $avatarCode"
$pdfName = Read-Host "Ten PDF THUC TE trong documents (Enter de bo qua)"
if ([string]::IsNullOrWhiteSpace($pdfName)) {
    "5b. PDF private: SKIP - can nhap ten doi tuong thuc te."
} else {
    $pdfPath = [Uri]::EscapeDataString($pdfName)
    $pdfCode = HttpCode "http://${serviceHost}:9000/documents/$pdfPath"
    ShowResult "5b. PDF chan truy cap an danh" ($pdfCode -eq "403") "HTTP $pdfCode; doi chieu file trong Console"
}

# 6. DNS: in ket qua de doi chieu, khong gan PASS chi vi lenh da chay.
"6. DNS: ky vong app-backend=10.10.10.20, minio=10.10.10.30, keycloak=10.10.10.40"
nslookup -port=1053 app-backend.cloud.local $serviceHost
nslookup -port=1053 minio.cloud.local $serviceHost
nslookup -port=1053 keycloak.cloud.local $serviceHost

# 7. Prometheus: kiem tra target va kha nang doc Nginx.
try {
    $targetsResponse = FetchJson "http://${serviceHost}:9090/api/v1/targets"
    $targets = @($targetsResponse.data.activeTargets)
    $nodeTargets = @($targets | Where-Object { $_.labels.job -eq "node" })
    $webTargets = @($targets | Where-Object { $_.labels.job -eq "web" })
    $targets | ForEach-Object { "  {0,-8} {1,-5} {2}" -f $_.labels.job, $_.health, $_.scrapeUrl }
    $nodeOk = $nodeTargets.Count -ge 1 -and @($nodeTargets | Where-Object { $_.health -ne "up" }).Count -eq 0
    $webOk = $webTargets.Count -eq 2 -and @($webTargets | Where-Object { $_.health -ne "up" }).Count -eq 0
    $query = [Uri]::EscapeDataString('nginx_up{job="web"}')
    $nginxResponse = FetchJson "http://${serviceHost}:9090/api/v1/query?query=$query"
    $nginxRows = @($nginxResponse.data.result)
    $nginxOk = $nginxRows.Count -eq 2 -and @($nginxRows | Where-Object { $_.value[1] -ne "1" }).Count -eq 0
    ShowResult "7. Node UP, Web 2/2, nginx_up=1" ($nodeOk -and $webOk -and $nginxOk) "node=$($nodeTargets.Count), web=$($webTargets.Count), nginx=$($nginxRows.Count)"
} catch { ShowResult "7. Prometheus" $false $_.Exception.Message }

# 8. Grafana: xem giao dien de xac nhan 3 bieu do co du lieu.
$grafanaCode = HttpCode "http://${serviceHost}:3000/api/health"
ShowResult "8a. Grafana HTTP health" ($grafanaCode -eq "200") "HTTP $grafanaCode"
"8b. Dashboard: KIEM TRA THU CONG CPU, RAM, Network co du lieu. HTTP health khong chung minh dashboard dat."

# 9. Route student.
$routeCode = HttpCode "${baseUrl}/student/"
ShowResult "9. Gateway /student/" ($routeCode -eq "200") "HTTP $routeCode"

# 10. Round Robin: xem ca 8 ket qua va so ten server khac nhau.
$servedBy = @()
for ($i = 1; $i -le 8; $i++) {
    $headers = & curl.exe -k -f -sS --connect-timeout 5 --max-time 20 -I "${baseUrl}/"
    if ($LASTEXITCODE -eq 0) {
        $match = @($headers | Select-String '^X-Served-By:')
        if ($match.Count -gt 0) {
            $serverName = ($match[0].Line -replace '^X-Served-By:\s*', '').Trim()
            $servedBy += $serverName
            "Request ${i}: $serverName"
        }
    }
}
$uniqueServers = @($servedBy | Sort-Object -Unique)
ShowResult "10. Hai Web xu ly request" ($servedBy.Count -eq 8 -and $uniqueServers.Count -ge 2) ($uniqueServers -join ", ")
"Hoan tat. Xem tung dong FAIL, SKIP va ket qua thu cong; khong tu dong ket luan 10/10."
```

## Các phần kiểm tra thủ công còn lại

- **Web:** mở ba bài blog, xem ảnh minh họa và bấm liên kết quay lại.
- **Database:** thực thi SQL trực tiếp để đối chiếu API đọc DB.
- **Keycloak:** cho thấy realm, hai user và client trên Console.
- **MinIO:** upload file, tải PDF bằng Console và mở bản vừa tải.
- **DNS:** đọc kết quả nslookup, đối chiếu đúng bản ghi A. Nếu DNS từ laptop timeout, kiểm tra UDP 1053 và dùng dig trong EC2 để phân biệt lỗi truy cập bên ngoài.
- **Grafana:** xem đủ ba biểu đồ có dữ liệu; nếu export dùng layout mới, không dựa duy nhất vào số phần tử trong JSON để kết luận số panel.
- **Mạng:** chạy ping các service từ container cùng mạng cloud-net theo README. Laptop không tự phân giải tên service Docker nội bộ.

`-k` không bỏ qua đăng nhập hoặc JWT; chỉ bỏ kiểm tra chứng chỉ TLS. Nếu dùng chứng chỉ tin cậy, bỏ tùy chọn đó. Các kết quả PASS ở đây giới hạn theo phép thử ghi rõ, không thay thế toàn bộ yêu cầu và minh chứng báo cáo.
