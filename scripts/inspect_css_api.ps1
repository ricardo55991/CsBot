$bytes = [System.IO.File]::ReadAllBytes('H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\api\CounterStrikeSharp.API.dll')
$text = [System.Text.Encoding]::ASCII.GetString($bytes)
$regex = [regex]'[a-zA-Z0-9_\.]{6,50}'
$matches = $regex.Matches($text) | ForEach-Object { $_.Value } | Select-Object -Unique
$matches | Where-Object { $_ -match 'CounterStrikeSharp.API.Core' -or $_ -match 'PrintTo' -or $_ -match 'CCSPlayerController' } | Select-Object -First 30 | Out-String | Write-Host
