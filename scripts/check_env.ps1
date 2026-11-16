# ==============================================================================
# CsBot AI - Environment & Dependency Checker + Auto Steam Sync
# ==============================================================================

# 0. Sincronização Automática com o CS2 Oficial da Steam
$serverRoot = if (Test-Path "H:\CS2_AI_Server") { "H:\CS2_AI_Server" } else { (Resolve-Path "$PSScriptRoot\..").Path }
$serverGame = Join-Path $serverRoot "game"

# Detectar pasta do CS2 oficial da Steam
$candidateSteamPaths = @(
    "H:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game",
    "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game",
    "D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game"
)

$steamGame = $candidateSteamPaths | Where-Object { Test-Path "$_\csgo\steam.inf" } | Select-Object -First 1

if ($steamGame -and (Test-Path $serverGame)) {
    $steamInfPath = Join-Path $steamGame "csgo\steam.inf"
    $serverInfPath = Join-Path $serverGame "csgo\steam.inf"

    $steamInfRaw = Get-Content $steamInfPath -Raw -ErrorAction SilentlyContinue
    $serverInfRaw = if (Test-Path $serverInfPath) { Get-Content $serverInfPath -Raw -ErrorAction SilentlyContinue } else { "" }

    $steamPatch = if ($steamInfRaw -match 'PatchVersion=([^\r\n]+)') { $matches[1] } else { "Desconhecido" }
    $steamBuild = if ($steamInfRaw -match 'ClientVersion=([^\r\n]+)') { $matches[1] } else { "Desconhecido" }

    $serverPatch = if ($serverInfRaw -match 'PatchVersion=([^\r\n]+)') { $matches[1] } else { "Ausente" }
    $serverBuild = if ($serverInfRaw -match 'ClientVersion=([^\r\n]+)') { $matches[1] } else { "Ausente" }

    $isOutOfDate = ($steamBuild -ne $serverBuild) -or ($steamPatch -ne $serverPatch)

    if ($isOutOfDate) {
        Write-Host "[!] Atualizacao do CS2 detectada na Steam!" -ForegroundColor Yellow
        Write-Host "    -> Versao Steam:    $steamPatch (Build $steamBuild)" -ForegroundColor Cyan
        Write-Host "    -> Versao Servidor: $serverPatch (Build $serverBuild)" -ForegroundColor Magenta
        Write-Host "[*] Sincronizando binarios e definicoes do jogo automaticamente..." -ForegroundColor Yellow

        # 1. Copiar steam.inf atualizado
        Copy-Item -Path $steamInfPath -Destination $serverInfPath -Force

        # 2. Sincronizar binários executáveis e dlls mais novos via robocopy incremental
        $robocopyArgs = @("/xo", "/fft", "/e", "/r:1", "/w:1", "/njh", "/njs", "/ndl", "/nc", "/ns")
        & robocopy (Join-Path $steamGame "bin") (Join-Path $serverGame "bin") @robocopyArgs | Out-Null
        & robocopy (Join-Path $steamGame "csgo\bin") (Join-Path $serverGame "csgo\bin") @robocopyArgs | Out-Null
        & robocopy (Join-Path $steamGame "core") (Join-Path $serverGame "core") @robocopyArgs | Out-Null

        # 3. Verificar arquivos VPK novos ou modificados e sincronizar via HardLink
        $srcVpks = Get-ChildItem -Path (Join-Path $steamGame "csgo") -Filter "*.vpk" -File -ErrorAction SilentlyContinue
        $dstCsgo = Join-Path $serverGame "csgo"
        $newVpks = 0
        foreach ($vpk in $srcVpks) {
            $targetVpk = Join-Path $dstCsgo $vpk.Name
            $needsLink = $false
            if (Test-Path $targetVpk) {
                $targetItem = Get-Item $targetVpk
                if ($vpk.Length -ne $targetItem.Length -or $vpk.LastWriteTime -ne $targetItem.LastWriteTime) {
                    Remove-Item $targetVpk -Force -ErrorAction SilentlyContinue
                    $needsLink = $true
                }
            } else {
                $needsLink = $true
            }

            if ($needsLink) {
                New-Item -ItemType HardLink -Path $targetVpk -Target $vpk.FullName -ErrorAction SilentlyContinue | Out-Null
                $newVpks++
            }
        }
        if ($newVpks -gt 0) {
            Write-Host "[+] Atualizados/Criados $newVpks links VPK em game/csgo/." -ForegroundColor Green
        }

        Write-Host "[+] Servidor CS2 sincronizado com sucesso para a Versao $steamPatch (Build $steamBuild)!" -ForegroundColor Green
    } else {
        Write-Host "[+] Servidor CS2 sincronizado com o cliente Steam (Patch: $serverPatch, Build: $serverBuild)." -ForegroundColor Green
    }
} else {
    Write-Host "[i] Pasta oficial do CS2 da Steam nao encontrada para verificacao de versao." -ForegroundColor DarkGray
}

# 1. Verificando Injeção do Metamod no gameinfo.gi
$gi = Join-Path $serverGame "csgo\gameinfo.gi"
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
    $myIni = (Resolve-Path (Join-Path $serverRoot "database\my.ini")).Path
    $mysqld = (Resolve-Path (Join-Path $serverRoot "database\mariadb\bin\mysqld.exe")).Path
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

# 4. Aquecendo Qwen 2.5 1.5B/3B na VRAM da GPU (keep_alive: -1)
Write-Host "[*] Aquecendo modelo Qwen 2.5 1.5B na VRAM..." -ForegroundColor Cyan
try {
    $warmup = @{
        model = "qwen2.5:1.5b"
        prompt = "ping"
        stream = $false
        keep_alive = -1
    } | ConvertTo-Json
    $null = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $warmup -ContentType "application/json" -TimeoutSec 15
    Write-Host "[+] Qwen 2.5 1.5B aquecido e mantido na VRAM (keep_alive: -1)." -ForegroundColor Green
} catch {
    Write-Host "[!] Falha ao aquecer Qwen 2.5 1.5B no Ollama: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                  >>> COMANDO PARA CONECTAR NO JOGO <<<                         " -ForegroundColor Yellow
Write-Host "  No seu CS2, abra o console de desenvolvedor (tecla ' ou ~) e digite:          " -ForegroundColor White
Write-Host "                           connect 127.0.0.1:27016                              " -ForegroundColor Green
Write-Host "                                                                                " -ForegroundColor White
Write-Host "  Ou de duplo clique em 'conectar_cs2.bat' para conectar automaticamente!      " -ForegroundColor DarkGray
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
