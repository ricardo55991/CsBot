$bytes = [System.IO.File]::ReadAllBytes('H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\RoundDamageRecap\RoundDamageRecap.dll')
$text = [System.Text.Encoding]::UTF8.GetString($bytes)
$idx = $text.IndexOf("FindOverridesDirectory")
if ($idx -ge 0) {
    $start = [Math]::Max(0, $idx - 500)
    $len = [Math]::Min($text.Length - $start, 1500)
    $sub = $text.Substring($start, $len)
    $clean = $sub -replace '[^\x20-\x7E]', ' '
    Write-Host $clean
}
