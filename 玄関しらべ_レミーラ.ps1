# 玄関しらべ(レミーラ) — 家のパソコンで流すと、玄関(ルーター)のようすを読むだけ。何も変えない。
# 使い方:このファイルを右クリック →「PowerShell で実行」。管理者は要らない。
# 結果はデスクトップ「玄関しらべ_結果.txt」にも書き出す。パスワード類は読まない・書かない。

$out = New-Object System.Collections.Generic.List[string]
function Say($s) { Write-Host $s; $out.Add($s) }

Say "=== 玄関しらべ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

# 1. いまつながっている Wi-Fi の名前(有線だけのパソコンなら出ない)
Say ""
Say "[1] Wi-Fi の名前"
$wlan = netsh wlan show interfaces 2>$null | Select-String '^\s*SSID\s*:'
if ($wlan) { foreach ($l in $wlan) { Say ("  " + $l.ToString().Trim()) } }
else { Say "  Wi-Fi は使っていない(有線)か、無線の部品がない" }

# 2. このパソコンの住所と、玄関(既定のゲートウェイ)
Say ""
Say "[2] 住所と玄関"
$gws = @()
foreach ($c in Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway }) {
    $gw = $c.IPv4DefaultGateway.NextHop
    $gws += $gw
    Say ("  つなぎ口: " + $c.InterfaceAlias + " / 自分: " + $c.IPv4Address.IPAddress + " / 玄関: " + $gw)
}
if (-not $gws) { Say "  玄関が見つからない(ネットにつながっていない?)" }

# 3. 外に出るまでに家の中の箱を何枚くぐるか(2枚なら skynet は別のルーター)
Say ""
Say "[3] 外に出るまでの道(最初の4つ)"
$hops = tracert -d -h 4 -w 800 8.8.8.8 2>$null | Select-String '^\s*\d+\s'
$inside = 0
foreach ($h in $hops) {
    $line = $h.ToString().Trim()
    Say ("  " + $line)
    if ($line -match '(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)\s*$') { $inside++ }
}
Say ("  家の中の箱の数: " + $inside)
if ($inside -ge 2) { Say "  → 家の中っぽい住所が2つ以上。2つめが 192.168.x なら別ルーター(B)の見込み。10.x なら au 側の中継のこともあるので写真で送って" }
elseif ($inside -eq 1) { Say "  → ルーターは1枚。白い箱の名前を skynet に変えた見込み(A)" }

# 4. 設定画面の入口が開くか
Say ""
Say "[4] 設定画面の入口"
$targets = @('192.168.0.1') + $gws | Select-Object -Unique
foreach ($t in $targets) {
    try {
        $r = Invoke-WebRequest -Uri ("http://" + $t + "/") -UseBasicParsing -TimeoutSec 5
        $title = ""
        if ($r.Content -match '<title>(.*?)</title>') { $title = $Matches[1] }
        Say ("  http://" + $t + " → 開いた(" + $r.StatusCode + ") 題: " + $title)
    } catch {
        Say ("  http://" + $t + " → 開かない: " + $_.Exception.Message)
    }
}

# 5. UPnP(勝手に扉を開ける機能)が点いているか:家の中に呼びかけて返事を数える
Say ""
Say "[5] UPnP の返事"
$udp = New-Object System.Net.Sockets.UdpClient
$udp.Client.ReceiveTimeout = 3000
$msg = "M-SEARCH * HTTP/1.1`r`nHOST: 239.255.255.250:1900`r`nMAN: `"ssdp:discover`"`r`nMX: 2`r`nST: urn:schemas-upnp-org:device:InternetGatewayDevice:1`r`n`r`n"
$bytes = [Text.Encoding]::ASCII.GetBytes($msg)
$ep = New-Object System.Net.IPEndPoint ([Net.IPAddress]::Parse('239.255.255.250'), 1900)
[void]$udp.Send($bytes, $bytes.Length, $ep)
$seen = @{}
$end = (Get-Date).AddSeconds(4)
while ((Get-Date) -lt $end) {
    try {
        $from = New-Object System.Net.IPEndPoint ([Net.IPAddress]::Any, 0)
        $data = $udp.Receive([ref]$from)
        $ip = $from.Address.ToString()
        if (-not $seen.ContainsKey($ip)) {
            $seen[$ip] = $true
            $server = ([Text.Encoding]::ASCII.GetString($data) -split "`r`n" | Where-Object { $_ -match '^SERVER:' }) -join ''
            Say ("  返事あり: " + $ip + "  " + $server)
        }
    } catch { break }
}
$udp.Close()
if ($seen.Count -eq 0) { Say "  返事なし → UPnP は切れている見込み(良い)" }
else { Say "  → 上の箱で UPnP が点いている。設定画面で切る候補" }

Say ""
Say "=== おわり(読むだけ。何も変えていない) ==="

$file = Join-Path ([Environment]::GetFolderPath('Desktop')) '玄関しらべ_結果.txt'
$out | Out-File -FilePath $file -Encoding utf8
Write-Host ""
Write-Host ("書き出した: " + $file)
Read-Host "Enter で閉じる"
