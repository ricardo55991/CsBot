$dlls = @(
    "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\BotState\BotState.dll",
    "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\NadeSystem\NadeSystem.dll",
    "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\BotControllerImpl\BotControllerImpl.dll"
)

foreach ($dll in $dlls) {
    Write-Host "=== Inspecting $dll ==="
    $bytes = [System.IO.File]::ReadAllBytes($dll)
    $text = [System.Text.Encoding]::ASCII.GetString($bytes)
    $regex = [regex]'[a-zA-Z0-9_\.]{6,40}'
    $matches = $regex.Matches($text) | ForEach-Object { $_.Value } | Select-Object -Unique
    $relevant = $matches | Where-Object { $_ -match 'bot_' -or $_ -match 'nav_' -or $_ -match 'mp_' -or $_ -match 'freeze' -or $_ -match 'stop' -or $_ -match 'Controller' }
    $relevant | Select-Object -First 20 | Out-String | Write-Host
}
