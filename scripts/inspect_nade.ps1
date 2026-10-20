$dllPath = "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\NadeSystem\NadeSystem.dll"
$bytes = [System.IO.File]::ReadAllBytes($dllPath)
$asm = [System.Reflection.Assembly]::Load($bytes)
foreach ($t in $asm.GetTypes()) {
    Write-Host "Type: $($t.FullName)"
    $t.GetMethods([System.Reflection.BindingFlags]'Public,NonPublic,Instance,Static') | Where-Object { $_.DeclaringType -eq $t } | Select-Object Name | Format-Table -AutoSize | Out-String | Write-Host
}
