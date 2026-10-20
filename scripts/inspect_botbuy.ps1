$bytes = [System.IO.File]::ReadAllBytes('H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\BotBuy\BotBuy.dll')
$text = [System.Text.Encoding]::ASCII.GetString($bytes)
$regex = [regex]'[a-zA-Z0-9_\.\\/:]{4,60}'
$matches = $regex.Matches($text) | ForEach-Object { $_.Value } | Select-Object -Unique
$matches | Where-Object { $_ -match 'buy' -or $_ -match 'bot_' -or $_ -match 'freeze' -or $_ -match 'money' -or $_ -match 'round' -or $_ -match 'weapon' } | Out-String | Write-Host
