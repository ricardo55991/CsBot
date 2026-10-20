$steamGame = "H:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game"
$serverGame = "H:\CS2_AI_Server\game"

Write-Host "=== 1. Criando Junções de Diretórios em game/ ==="
$gameDirs = @("csgo_community_addons", "csgo_lv")
foreach ($d in $gameDirs) {
    $src = Join-Path $steamGame $d
    $dst = Join-Path $serverGame $d
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            New-Item -ItemType Junction -Path $dst -Target $src | Out-Null
            Write-Host "Criada Junção: $dst -> $src"
        } else {
            Write-Host "Já existe: $dst"
        }
    }
}

Write-Host "=== 2. Criando Junções de Diretórios em game/csgo/ ==="
$csgoDirs = @("maps", "panorama", "resource", "rpt", "save", "_iconcache")
foreach ($d in $csgoDirs) {
    $src = Join-Path (Join-Path $steamGame "csgo") $d
    $dst = Join-Path (Join-Path $serverGame "csgo") $d
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            New-Item -ItemType Junction -Path $dst -Target $src | Out-Null
            Write-Host "Criada Junção: $dst -> $src"
        } else {
            Write-Host "Já existe: $dst"
        }
    }
}

Write-Host "=== 3. Criando HardLinks para arquivos VPK de game/csgo/ ==="
$srcCsgo = Join-Path $steamGame "csgo"
$dstCsgo = Join-Path $serverGame "csgo"

$vpkFiles = Get-ChildItem -Path $srcCsgo -Filter "*.vpk" -File
Write-Host "Total de arquivos VPK encontrados: $($vpkFiles.Count)"

$createdCount = 0
$skippedCount = 0
foreach ($f in $vpkFiles) {
    $targetFile = Join-Path $dstCsgo $f.Name
    if (-not (Test-Path $targetFile)) {
        New-Item -ItemType HardLink -Path $targetFile -Target $f.FullName | Out-Null
        $createdCount++
    } else {
        $skippedCount++
    }
}
Write-Host "HardLinks criados: $createdCount | Já existentes: $skippedCount"
Write-Host "=== Concluído com sucesso! ==="
