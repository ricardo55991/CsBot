$dllPath = "H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\WeaponPaints\WeaponPaints.dll"
$bytes = [System.IO.File]::ReadAllBytes($dllPath)
$asm = [System.Reflection.Assembly]::Load($bytes)
try {
    $asm.GetTypes() | Out-Null
} catch [System.Reflection.ReflectionTypeLoadException] {
    foreach ($le in $_.Exception.LoaderExceptions) {
        Write-Host $le.Message
    }
}
