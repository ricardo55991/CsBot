# =====================================================================
# Script de Auditoria e Consolidacao de Codigo
# CsBot e CsAIServer
# =====================================================================

$includeExtensions = @(
    ".cs",
    ".csproj",
    ".sln",
    ".json",
    ".py",
    ".md",
    ".props",
    ".targets",
    ".config",
    ".yml",
    ".yaml"
)

$excludedDirectories = @(
    ".git",
    ".vs",
    "bin",
    "obj",
    "models",
    "checkpoints",
    "demos",
    "logs",
    "extracted_tensors",
    "raw_demos",
    "downloads"
)

function Gerar-Auditoria-Projeto {
    param(
        [Parameter(Mandatory = $true)]
        [string]$NomeProjeto,

        [Parameter(Mandatory = $true)]
        [string]$Root,

        [Parameter(Mandatory = $true)]
        [string]$NomeArquivoSaida
    )

    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Iniciando Auditoria: $NomeProjeto" -ForegroundColor Cyan
    Write-Host "Raiz: $Root" -ForegroundColor DarkGray
    Write-Host "==================================================" -ForegroundColor Cyan

    if (-not (Test-Path $Root)) {
        Write-Warning "Diretorio nao encontrado: $Root. Pulando..."
        Write-Host ""
        return
    }

    $output = Join-Path $Root $NomeArquivoSaida
    Remove-Item $output -ErrorAction SilentlyContinue

    Write-Host "Mapeando arquivos em $Root..." -ForegroundColor DarkGray

    $files = Get-ChildItem $Root -Recurse -File |
        Where-Object {
            if ($_.FullName -eq $output) { return $false }

            $extensionAllowed = $includeExtensions -contains $_.Extension.ToLowerInvariant()

            $relativePath = $_.FullName.Substring($Root.Length).TrimStart("\")
            $pathParts = $relativePath -split "[\\/]"

            $excluded = $false
            foreach ($directory in $excludedDirectories) {
                if ($pathParts -contains $directory) {
                    $excluded = $true
                    break
                }
            }

            $extensionAllowed -and -not $excluded
        } |
        Sort-Object FullName

    Write-Host "Consolidando $($files.Count) arquivos em $output..." -ForegroundColor DarkGray

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($output, $false, $utf8NoBom)

    try {
        $count = 0
        $total = $files.Count
        foreach ($file in $files) {
            $count++
            $relativePath = $file.FullName.Substring($Root.Length).TrimStart("\")

            $writer.WriteLine()
            $writer.WriteLine("==================================================")
            $writer.WriteLine("FILE: $relativePath")
            $writer.WriteLine("==================================================")
            $writer.WriteLine()

            try {
                $content = [System.IO.File]::ReadAllText($file.FullName)
                $writer.WriteLine($content)
            }
            catch {
                $writer.WriteLine("// [ERRO AO LER ARQUIVO: $_]")
            }
        }
    }
    finally {
        $writer.Dispose()
    }

    Write-Host ""
    Write-Host "Arquivo gerado:" -ForegroundColor Green
    Write-Host $output -ForegroundColor White
    Write-Host ""
    Write-Host "Quantidade de arquivos incluídos: $($files.Count)"
    if (Test-Path $output) {
        Write-Host "Tamanho: $([math]::Round((Get-Item $output).Length / 1MB, 2)) MB"
    }
    Write-Host ""
}

# 1. Auditoria do CsBot
$csBotRoot = "C:\Users\ricar\OneDrive\Documentos\Dev\CsBot"
if (-not (Test-Path $csBotRoot)) {
    $csBotRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
}
Gerar-Auditoria-Projeto -NomeProjeto "CsBot" -Root $csBotRoot -NomeArquivoSaida "AUDITORIA_CODIGO_COMPLETO.txt"

# 2. Auditoria do CsAIServer
$serverRoot = "H:\CS2_AI_Server"
if (-not (Test-Path $serverRoot)) {
    $alt = "C:\Users\ricar\OneDrive\Documentos\Dev\CsAIServer"
    if (Test-Path $alt) { $serverRoot = $alt }
}
Gerar-Auditoria-Projeto -NomeProjeto "CsAIServer" -Root $serverRoot -NomeArquivoSaida "AUDITORIA_CSAISERVER_COMPLETO.txt"
