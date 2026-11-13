$H  = "56.10.26.60"        # khi test AWS: đổi thành PUBLIC IP
$PW = Read-Host "Mat khau cua sv01 trong realm_sv001"
$grafanaCredential = Get-Credential -UserName "admin" -Message "Nhap tai khoan Grafana"
$grafanaAuth = "{0}:{1}" -f $grafanaCredential.UserName, $grafanaCredential.GetNetworkCredential().Password
function Code($u){ curl.exe -s -o NUL -w "%{http_code}" $u }
function Show($n,$ok,$d){ "{0,-36} {1} {2}" -f $n, $(if($ok){"PASS"}else{"FAIL"}), $d }

# 1. Blog: 3 bai viet

$c = 1..3 | ForEach-Object { Code "http://${H}:8080/blog/blog$_.html" }
Show "1. Blog (blog1-3.html)" (($c | Where-Object {$_ -ne "200"}).Count -eq 0) ($c -join ",")

# 2. API /student (JSON) qua proxy

$s = curl.exe -s "http://${H}/api/student" | ConvertFrom-Json
Show "2. /api/student (>=5 SV)" ($s.Count -ge 5) "$($s.Count) sinh vien"

# 3. API doc tu MariaDB

$d = curl.exe -s "http://${H}/api/students-db" | ConvertFrom-Json
Show "3. /api/students-db (>=3 ban ghi)" ($d.Count -ge 3) "$($d.Count) ban ghi"

# 4. Keycloak realm_sv001 -> token -> /secure

$tk  = curl.exe -s -X POST "http://${H}/auth/realms/realm_sv001/protocol/openid-connect/token" -d "grant_type=password" -d "client_id=flask-app" -d "username=sv01" -d "password=$PW" | ConvertFrom-Json
$sec = curl.exe -s -H "Authorization: Bearer $($tk.access_token)" "http://${H}:8085/secure"
Show "4. Keycloak token + /secure" ($sec -match "Secure resource OK") $sec

# 5. MinIO: profile-pics public, documents private

$a = Code "http://${H}:9000/profile-pics/avatar.jpg"
$b = Code "http://${H}:9000/documents/"
Show "5. MinIO avatar public / docs private" (($a -eq "200") -and ($b -in "403","404")) "avatar=$a documents=$b"

# 6. DNS trên EC2 — chạy riêng trong PowerShell
nslookup -port=1053 app-backend.cloud.local $H
nslookup -port=1053 minio.cloud.local $H
nslookup -port=1053 keycloak.cloud.local $H

# 7. Prometheus: co job 'web'

$t = (curl.exe -s "http://${H}:9090/api/v1/targets" | ConvertFrom-Json).data.activeTargets
$t | ForEach-Object { "      {0,-14} {1,-5} {2}" -f $_.labels.job, $_.health, $_.scrapeUrl }
Show "7. Prometheus co job 'web'" ([bool]($t | Where-Object { $_.labels.job -eq "web" })) "xem UP/DOWN o bang tren"

# 8. Grafana: dashboard System Health co >=3 panel

$g = curl.exe -s -u $grafanaAuth "http://${H}:3000/api/search?query=System%20Health" | ConvertFrom-Json
$p = 0
if ($g.Count -ge 1) { $p = (curl.exe -s -u $grafanaAuth "http://${H}:3000/api/dashboards/uid/$($g[0].uid)" | ConvertFrom-Json).dashboard.panels.Count }
Show "8. Grafana dashboard (>=3 panel)" (($g.Count -ge 1) -and ($p -ge 3)) "$($g[0].title) - $p panel"

# 9. Proxy route /student/

Show "9. Proxy route /student/" ((Code "http://${H}/student/") -eq "200") ""

# 10. Load balancing Round Robin

$u = 1..8 | ForEach-Object { "$(curl.exe -sI "http://${H}/" | Select-String 'X-Served-By')".Trim() } | Sort-Object -Unique
Show "10. Round Robin (>=2 upstream)" ($u.Count -ge 2) ($u -join " | ")