$body = @{
    model = "qwen2.5:3b"
    prompt = "You are a CS2 IGL. Return a JSON with fields: tactic_name (string), tactic_summary (string)."
    stream = $false
    format = "json"
    keep_alive = -1
} | ConvertTo-Json

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$res = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
$sw.Stop()

Write-Host "Response in $($sw.ElapsedMilliseconds) ms:"
Write-Host $res.response
