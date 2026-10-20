$src = "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\BotBuy"
$dstDir = "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins_disabled"
if (-not (Test-Path $dstDir)) {
    New-Item -ItemType Directory -Path $dstDir | Out-Null
}
$dst = Join-Path $dstDir "BotBuy"
if (Test-Path $src) {
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Move-Item -Path $src -Destination $dst -Force
    Write-Host "BotBuy successfully archived to plugins_disabled/BotBuy"
} else {
    Write-Host "BotBuy is already moved or not present in plugins."
}
