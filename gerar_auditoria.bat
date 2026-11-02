@echo off
chcp 65001 >nul
title Auditoria de Codigo - CsBot e CsAIServer
echo ======================================================================
echo           GERADOR DE AUDITORIA DE CODIGO (CsBot ^& CsAIServer)
echo ======================================================================
echo.
set SCRIPT_PATH=%~dp0scripts\gerar_auditoria.ps1
if not exist %SCRIPT_PATH% set SCRIPT_PATH=%~dp0gerar_auditoria.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File %SCRIPT_PATH%
echo.
pause
