@echo off
chcp 65001 >nul
title CsBot - Treinador MLMove 16Hz (AMD RX 6600M)
cls

set PYTHON_BIN=F:\CS2_MLMove_Pipeline\venv\Scripts\python.exe
if not exist "%PYTHON_BIN%" (
    set PYTHON_BIN=D:\CS2_MLMove_Pipeline\venv\Scripts\python.exe
)
if not exist "%PYTHON_BIN%" (
    set PYTHON_BIN=python.exe
)

set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%tools\mlmove_pipeline\train_and_export_onnx.py" (
    set SCRIPT_DIR=%SCRIPT_DIR%tools\mlmove_pipeline\
)

echo [*] Disparando Treinador e Exportador ONNX MLMove 16Hz (Disco F:)...
"%PYTHON_BIN%" "%SCRIPT_DIR%train_and_export_onnx.py" %*
pause
