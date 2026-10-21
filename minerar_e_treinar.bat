@echo off
chcp 65001 >nul
title CsBot - Minerador e Treinador Automatizado MLMove 16Hz (AMD RX 6600M)
cls

echo =======================================================================
echo          CsBot - Pipeline de Mineração e Treinamento MLMove 16Hz
echo                   Aceleração via GPU AMD RX 6600M
echo =======================================================================
echo.
echo Escolha o modo de operação desejado:
echo.
echo  [1] Minerar Lote Automático da Web + Extrair 16Hz + Treinar ONNX (Limpa .dem após extrair)
echo  [2] Processar Demos Colocadas Manualmente em D:\CS2_MLMove_Pipeline\raw_demos\de_mirage + Treinar ONNX
echo  [3] Apenas Re-Treinar Modelo ONNX com Todos os Tensores (.npz) Atuais na RX 6600M
echo  [4] Sair
echo.
echo =======================================================================
set /p opcao="Digite a opção desejada [1-4]: "

set PYTHON_BIN=D:\CS2_MLMove_Pipeline\venv\Scripts\python.exe
if not exist "%PYTHON_BIN%" (
    set PYTHON_BIN=python.exe
)

set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%tools\mlmove_pipeline\run_mining_and_training_loop.py" (
    set SCRIPT_DIR=%SCRIPT_DIR%tools\mlmove_pipeline\
)

if "%opcao%"=="1" (
    cls
    echo [*] Iniciando Mineração Automática da Web (HuggingFace + URLs/HLTV) + Treinamento...
    "%PYTHON_BIN%" "%SCRIPT_DIR%run_mining_and_training_loop.py" --source all --batch-size 25 --epochs 15
    goto fim
)

if "%opcao%"=="2" (
    cls
    echo [*] Processando Demos Manuais em D:\CS2_MLMove_Pipeline\raw_demos\de_mirage...
    "%PYTHON_BIN%" "%SCRIPT_DIR%run_mining_and_training_loop.py" --source local --batch-size 25 --epochs 15
    goto fim
)

if "%opcao%"=="3" (
    cls
    echo [*] Disparando Re-treinamento Incremental na GPU AMD RX 6600M com tensores existentes...
    "%PYTHON_BIN%" "%SCRIPT_DIR%train_and_export_onnx.py" --epochs 15 --batch-size 256
    goto fim
)

if "%opcao%"=="4" (
    echo Encerrando.
    exit /b 0
)

echo Opção inválida!
pause
goto fim

:fim
echo.
echo =======================================================================
echo Ciclo concluído. O modelo ONNX gerado em H:\CS2_AI_Server\models\
echo foi atualizado automaticamente no servidor CS2 via hot-swap!
echo =======================================================================
pause
