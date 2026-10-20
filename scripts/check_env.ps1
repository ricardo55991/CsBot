$gi = Join-Path $PSScriptRoot "..\game\csgo\gameinfo.gi"
if (Test-Path $gi) {
    $content = [System.IO.File]::ReadAllText($gi, [System.Text.Encoding]::UTF8)
    if ($content -notmatch 'csgo/addons/metamod') {
        Write-Host "[!] Metamod ausente no gameinfo.gi do servidor dedicado. Injetando..." -ForegroundColor Yellow
        $target = "Game_LowViolence\s+csgo_lv[^\r\n]*"
        $content = $content -replace $target, "`$0`r`n`t`t`tGame`tcsgo/addons/metamod"
        [System.IO.File]::WriteAllText($gi, $content, [System.Text.Encoding]::UTF8)
        Write-Host "[+] Metamod configurado com sucesso em H:\CS2_AI_Server!" -ForegroundColor Green
    } else {
        Write-Host "[+] Metamod verificado com sucesso no gameinfo.gi do servidor (H:\CS2_AI_Server)." -ForegroundColor Green
    }
}

# 2. Verificando MariaDB (Porta 3306)
$mysqldProc = Get-Process mysqld -ErrorAction SilentlyContinue
if ($mysqldProc) {
    Write-Host "[+] MariaDB ja esta em execucao na porta 3306." -ForegroundColor Green
} else {
    Write-Host "[*] Iniciando MariaDB portatil em H:\CS2_AI_Server\database..." -ForegroundColor Cyan
    $myIni = (Resolve-Path (Join-Path $PSScriptRoot "..\database\my.ini")).Path
    $mysqld = (Resolve-Path (Join-Path $PSScriptRoot "..\database\mariadb\bin\mysqld.exe")).Path
    Start-Process -FilePath $mysqld -ArgumentList "--defaults-file=`"$myIni`"" -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Write-Host "[+] MariaDB iniciado." -ForegroundColor Green
}

# 3. Verificando Ollama (Porta 11434)
try {
    $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[+] Ollama ja esta em execucao na porta 11434." -ForegroundColor Green
} catch {
    Write-Host "[*] Iniciando servico do Ollama em segundo plano..." -ForegroundColor Cyan
    $ollamaExe = "C:\Users\ricar\AppData\Local\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaExe) {
        Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Write-Host "[+] Ollama iniciado." -ForegroundColor Green
    } else {
        Write-Host "[!] Executavel do Ollama nao encontrado em $ollamaExe" -ForegroundColor Red
    }
}

# 4. Aquecendo Qwen 2.5 3B na VRAM da GPU (keep_alive: -1)
Write-Host "[*] Aquecendo modelo Qwen 2.5 3B na VRAM (AMD RX 6600M)..." -ForegroundColor Cyan
try {
    $warmup = @{
        model = "qwen2.5:3b"
        prompt = "ping"
        stream = $false
        keep_alive = -1
    } | ConvertTo-Json
    $null = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $warmup -ContentType "application/json" -TimeoutSec 15
    Write-Host "[+] Qwen 2.5 3B aquecido e mantido na VRAM (keep_alive: -1)." -ForegroundColor Green
} catch {
    Write-Host "[!] Falha ao aquecer Qwen 2.5 3B no Ollama: $($_.Exception.Message)" -ForegroundColor Yellow
}
