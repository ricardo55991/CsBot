@echo off
chcp 65001 >nul
title CsBot - Conectar ao Servidor CS2 (127.0.0.1:27016)
color 0A

echo ==============================================================================
echo   Iniciando CS2 e conectando automaticamente ao Servidor de IA...
echo   Servidor Local: 127.0.0.1:27016
echo ==============================================================================
echo.

start "" "steam://run/730//+connect 127.0.0.1:27016"

echo [+] Comando de conexao enviado a Steam com sucesso!
echo [*] O jogo abrira na sua tela e entrara diretamente na partida.
timeout /t 3 /nobreak >nul
