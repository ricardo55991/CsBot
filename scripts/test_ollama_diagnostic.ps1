# Script de Diagnostico Isolado do Ollama (V4.2 Parte 10)
param(
    [string]$OllamaUrl = "http://localhost:11434/api/generate",
    [string]$Model = "qwen2.5:1.5b",
    [int]$TimeoutSeconds = 10
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSTICO ISOLADO DO OLLAMA - CSBOTMANAGER V4.2" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Endpoint: $OllamaUrl | Modelo: $Model | Timeout: ${TimeoutSeconds}s`n"

function Invoke-OllamaMeasurement {
    param(
        [string]$TestName,
        [string]$PromptText
    )

    $payload = @{
        model = $Model
        prompt = $PromptText
        stream = $false
        options = @{
            temperature = 0.2
            num_predict = 180
        }
    } | ConvertTo-Json -Compress

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $result = @{
        test_name = $TestName
        model = $Model
        prompt_tokens = 0
        generated_tokens = 0
        load_duration_ms = 0
        prompt_eval_duration_ms = 0
        eval_duration_ms = 0
        total_duration_ms = 0
        tokens_per_second = 0.0
        response_size_bytes = 0
        parse_success = $false
        timeout = $false
        error = $null
    }

    try {
        $response = Invoke-RestMethod -Uri $OllamaUrl -Method Post -Body $payload -ContentType "application/json" -TimeoutSec $TimeoutSeconds
        $sw.Stop()

        $result.total_duration_ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 1)
        if ($response) {
            $result.prompt_tokens = [int]$response.prompt_eval_count
            $result.generated_tokens = [int]$response.eval_count
            $result.load_duration_ms = [Math]::Round(($response.load_duration / 1000000.0), 1)
            $result.prompt_eval_duration_ms = [Math]::Round(($response.prompt_eval_duration / 1000000.0), 1)
            $result.eval_duration_ms = [Math]::Round(($response.eval_duration / 1000000.0), 1)
            $result.response_size_bytes = ($response.response).Length

            if ($response.eval_duration -gt 0) {
                $result.tokens_per_second = [Math]::Round(($response.eval_count / ($response.eval_duration / 1000000000.0)), 2)
            }

            try {
                $parsed = $response.response | ConvertFrom-Json -ErrorAction Stop
                $result.parse_success = ($null -ne $parsed)
            } catch {
                $result.parse_success = $false
            }
        }
    } catch {
        $sw.Stop()
        $result.total_duration_ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 1)
        if ($_.Exception.Message -match "timed out" -or $_.Exception.Message -match "Timeout") {
            $result.timeout = $true
        }
        $result.error = $_.Exception.Message
    }

    return $result
}

$promptCT = "You are Counter-Terrorist IGL on de_mirage. Team budget: 4500, Enemy budget: 2000, Round: 2. Return JSON with tactic and role orders."
$promptTR = "You are Terrorist IGL on de_mirage. Team budget: 4500, Enemy budget: 2000, Round: 2. Return JSON with tactic and role orders."

# 1. Chamada CT (Fria)
Write-Host "[1/4] Executando chamada CT..." -ForegroundColor Yellow
$res1 = Invoke-OllamaMeasurement -TestName "CT_Cold" -PromptText $promptCT
$res1 | Format-List

# 2. Chamada TR
Write-Host "[2/4] Executando chamada TR..." -ForegroundColor Yellow
$res2 = Invoke-OllamaMeasurement -TestName "TR_Live" -PromptText $promptTR
$res2 | Format-List

# 3. Chamada CT pós-warmup
Write-Host "[3/4] Executando chamada CT pos-warmup..." -ForegroundColor Yellow
$res3 = Invoke-OllamaMeasurement -TestName "CT_PostWarmup" -PromptText $promptCT
$res3 | Format-List

# 4. CT e TR em Concorrência
Write-Host "[4/4] Executando CT e TR concorrentes..." -ForegroundColor Yellow
$taskCT = [System.Threading.Tasks.Task]::Run({
    Invoke-OllamaMeasurement -TestName "Concurrent_CT" -PromptText $using:promptCT
})
$taskTR = [System.Threading.Tasks.Task]::Run({
    Invoke-OllamaMeasurement -TestName "Concurrent_TR" -PromptText $using:promptTR
})
[System.Threading.Tasks.Task]::WaitAll($taskCT, $taskTR)
$resCT = $taskCT.Result
$resTR = $taskTR.Result

Write-Host "`nConcorrente CT:" -ForegroundColor Green
$resCT | Format-List
Write-Host "Concorrente TR:" -ForegroundColor Green
$resTR | Format-List

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  RESUMO DOS RESULTADOS" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
$all = @($res1, $res2, $res3, $resCT, $resTR)
$all | Format-Table test_name, total_duration_ms, eval_duration_ms, tokens_per_second, parse_success, timeout -AutoSize
