param([string]$BaseUrl = 'http://localhost', [switch]$SkipDocker)
$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues = @{'Invoke-RestMethod:TimeoutSec'=20; 'Invoke-WebRequest:TimeoutSec'=20}
$BaseUrl = $BaseUrl.TrimEnd('/')
$failed = 0
function Check($name, [scriptblock]$action) {
    try { & $action; Write-Host "PASS $name" -ForegroundColor Green }
    catch { $script:failed++; Write-Host "FAIL $name : $($_.Exception.Message)" -ForegroundColor Red }
}
function Require($condition, $message) { if (-not $condition) { throw $message } }
foreach ($path in @('/', '/blog/', '/blog/blog1.html', '/blog/blog2.html', '/blog/blog3.html')) {
    Check "Web $path" { $r = Invoke-WebRequest "$BaseUrl$path" -UseBasicParsing; Require ($r.StatusCode -eq 200) 'HTTP status' }
}
Check 'JSON + route mapping' {
    $a = Invoke-RestMethod "$BaseUrl/api/student"
    $b = Invoke-RestMethod "$BaseUrl/student/"
    Require ($a.Count -ge 5 -and ($a | ConvertTo-Json -Depth 5) -eq ($b | ConvertTo-Json -Depth 5)) 'Student lists differ'
}
Check 'MariaDB students' { $rows = Invoke-RestMethod "$BaseUrl/api/students-db"; Require ($rows.Count -ge 3) 'Expected 3 records' }
Check 'DNS records via Bind9' {
    $records = Invoke-RestMethod "$BaseUrl/api/dns"
    $expected = @{'web-frontend-server.cloud.local'='10.10.10.10'; 'app-backend.cloud.local'='10.10.10.20'; 'minio.cloud.local'='10.10.10.30'; 'keycloak.cloud.local'='10.10.10.40'}
    Require ($records.Count -eq 4) 'Expected four DNS names'
    foreach ($record in $records) { Require ($record.addresses -contains $expected[$record.name]) "Wrong IP for $($record.name)" }
}
Check 'Round Robin' {
    $servers = 1..8 | ForEach-Object { (Invoke-WebRequest "$BaseUrl/?probe=$_" -UseBasicParsing).Headers['X-Served-By'] }
    Require ((@($servers | Sort-Object -Unique)).Count -eq 2) 'Expected both web servers'
    Write-Host ($servers -join ' -> ')
}
Check 'OIDC tokens sv01 + sv02' {
    foreach ($user in @('sv01','sv02')) {
        $token = Invoke-RestMethod "$BaseUrl/auth/realms/realm_sv001/protocol/openid-connect/token" -Method Post -Body @{client_id='flask-app';username=$user;password='123456';grant_type='password'}
        $r = Invoke-RestMethod "$BaseUrl/api/secure" -Headers @{Authorization="Bearer $($token.access_token)"}
        Require ($r.preferred_username -eq $user) 'Wrong identity'
    }
}
Check 'Unauthorized request rejected' {
    $code = & curl.exe -s -o NUL -w '%{http_code}' "$BaseUrl/api/secure"
    Require ($code -eq '401') 'Expected 401'
}
Check 'Invalid token rejected' {
    $code = & curl.exe --max-time 15 -s -o NUL -w '%{http_code}' -H 'Authorization: Bearer invalid-token' "$BaseUrl/api/secure"
    Require ($code -eq '401') 'Expected 401'
}
$uri = [uri]$BaseUrl
$hostUrl = '{0}://{1}' -f $uri.Scheme,$uri.Host
Check 'MinIO public avatar' { $r=Invoke-WebRequest "${hostUrl}:9000/profile-pics/avatar.jpg" -UseBasicParsing; Require ($r.StatusCode -eq 200) 'Avatar missing' }
Check 'MinIO report private' {
    $code = & curl.exe --max-time 15 -s -o NUL -w '%{http_code}' "${hostUrl}:9000/documents/minicloud-report.pdf"
    Require ($code -eq '403') 'Report must deny anonymous download'
}
Check 'Prometheus node/web UP' {
    $targets=(Invoke-RestMethod "${hostUrl}:9090/api/v1/targets").data.activeTargets
    foreach($job in @('node','web')) { Require ([bool]($targets | Where-Object {$_.labels.job -eq $job -and $_.health -eq 'up'})) "$job is not UP" }
    foreach($metric in @('node_cpu_seconds_total','node_memory_MemAvailable_bytes','node_network_receive_bytes_total','nginx_up')) {
        $q=Invoke-RestMethod ("${hostUrl}:9090/api/v1/query?query="+[uri]::EscapeDataString($metric))
        Require (@($q.data.result).Count -gt 0) "No samples for $metric"
    }
}
Check 'Grafana provisioned dashboard' {
    $auth=[Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('admin:admin'))
    $d=Invoke-RestMethod "${hostUrl}:3000/api/dashboards/uid/minicloud-health" -Headers @{Authorization="Basic $auth"}
    Require ($d.dashboard.panels.Count -ge 3) 'Missing panels'
}
if (-not $SkipDocker) {
    Check 'Bind9 zone syntax' { docker compose exec -T internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local; Require ($LASTEXITCODE -eq 0) 'Invalid DNS zone' }
    Check 'MariaDB notes' { docker compose exec -T relational-database-server mariadb -uroot -proot -e 'SELECT * FROM minicloud.notes;'; Require ($LASTEXITCODE -eq 0) 'DB query failed' }
}
Write-Host "Failures: $failed"
if ($failed -gt 0) { exit 1 }
