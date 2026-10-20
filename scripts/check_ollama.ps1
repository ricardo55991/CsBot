try {
    $cli = (Get-Command ollama -ErrorAction Stop).Source
    Write-Host "Ollama CLI path: $cli"
    $ver = & $cli --version
    Write-Host "Ollama version: $ver"
} catch {
    Write-Host "Ollama CLI not found in PATH"
}

try {
    $res = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3
    Write-Host "Ollama HTTP Service is RUNNING on port 11434."
    Write-Host "Models:"
    $res.models | Select-Object name, size | Format-Table -AutoSize | Out-String | Write-Host
} catch {
    Write-Host "Ollama HTTP Service is NOT responding on port 11434: $($_.Exception.Message)"
}
