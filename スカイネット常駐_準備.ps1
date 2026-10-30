# スカイネット常駐_準備 — 家のパソコンで1回流すと、ログインのたびに Claude(remote-control)が自動で起き、
# 落ちても30秒後に起こし直す(ザオリク係)。管理者は要らない(自分のユーザーの「ログイン時に起動」に入れるだけ)。
# 使い方:右クリック →「PowerShell で実行」。最後に「照らし」で、入れた物を読み直して見せる。
# やめる時:このファイルを -Yameru を付けて流す(powershell -File スカイネット常駐_準備.ps1 -Yameru)。

param([switch]$Yameru)

# ここを変えれば、Claude が働く場所が変わる
$Basho = Join-Path $env:USERPROFILE 'Downloads\キャッスル防衛AI'

$RunKey  = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$RunName = 'SkynetClaudeJochu'
$Home2   = Join-Path $env:LOCALAPPDATA 'SkynetJochu'
$Launch  = Join-Path $Home2 'jochu.ps1'
$Log     = Join-Path $Home2 'jochu_log.txt'

if ($Yameru) {
    Remove-ItemProperty -Path $RunKey -Name $RunName -ErrorAction SilentlyContinue
    $left = Get-ItemProperty -Path $RunKey -Name $RunName -ErrorAction SilentlyContinue
    if ($left) { Write-Host "失敗:まだ残っている" } else { Write-Host "やめた:ログイン時の起動から外した" }
    Read-Host "Enter で閉じる"; return
}

$ng = @()

# 1. claude が入っているか
$cmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $cmd) {
    Write-Host "claude が見つからない。先に Claude Code を入れて、一度 claude を起動してログインしておくこと。"
    Write-Host "入れ方(公式):PowerShell で  irm https://claude.ai/install.ps1 | iex"
    Read-Host "Enter で閉じる"; return
}
$Claude = $cmd.Source
$ver = (& $Claude --version 2>$null) -join ' '
Write-Host ("claude: " + $Claude + "  版: " + $ver)

# 2. 働く場所があるか
if (-not (Test-Path $Basho)) { Write-Host ("働く場所が無い: " + $Basho + "  → 上の `$Basho を直して流し直す"); Read-Host "Enter で閉じる"; return }

# 3. 起こし係(落ちたら30秒後に起こし直す)を書く
New-Item -ItemType Directory -Force -Path $Home2 | Out-Null
$body = @"
`$Claude = '$($Claude -replace "'", "''")'
`$Basho  = '$($Basho -replace "'", "''")'
`$Log    = '$($Log -replace "'", "''")'
while (`$true) {
    Add-Content -Path `$Log -Value ((Get-Date -Format 's') + ' 起動 ' + `$Basho) -Encoding UTF8
    Set-Location `$Basho
    & `$Claude remote-control
    Add-Content -Path `$Log -Value ((Get-Date -Format 's') + ' 終了 code=' + `$LASTEXITCODE + ' → 30秒後に起こし直し') -Encoding UTF8
    Start-Sleep -Seconds 30
}
"@
Set-Content -Path $Launch -Value $body -Encoding UTF8

# 4. ログイン時に起動へ入れる(最小化した窓で。初回の確認が出たら見えるように隠さない)
$val = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File "' + $Launch + '"'
Set-ItemProperty -Path $RunKey -Name $RunName -Value $val

# 5. 照らし:入れた物を読み直す
Write-Host ""
Write-Host "=== 照らし ==="
$got = (Get-ItemProperty -Path $RunKey -Name $RunName -ErrorAction SilentlyContinue).$RunName
if ($got -eq $val) { Write-Host "OK ログイン時の起動: $got" } else { Write-Host "NG ログイン時の起動が入っていない"; $ng += 'Run' }
if (Test-Path $Launch) {
    $txt = Get-Content -Path $Launch -Raw
    if ($txt -match 'remote-control' -and $txt -match [regex]::Escape($Basho)) { Write-Host "OK 起こし係: $Launch" } else { Write-Host "NG 起こし係の中身が違う"; $ng += 'Launch' }
} else { Write-Host "NG 起こし係が無い"; $ng += 'Launch' }

Write-Host ""
if ($ng.Count -eq 0) {
    Write-Host "入れた。いまからすぐ起こすなら次の窓で始める(初回は確認が出たら y で答える)。"
    Write-Host "スマホの Claude Code アプリにこのパソコンのセッションが出れば常駐成功。ログ: $Log"
    $go = Read-Host "いま起動する? (y/n)"
    if ($go -eq 'y') { Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$Launch`"") }
} else {
    Write-Host ("入れられなかった物: " + ($ng -join ', ') + "  → この画面を写真で送って")
}
Read-Host "Enter で閉じる"
