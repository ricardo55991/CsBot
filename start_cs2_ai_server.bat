@echo off
title CS2 AI Dedicated Server (H:\CS2_AI_Server)

cd /d "H:\CS2_AI_Server"

echo ========================================================
echo       Iniciando CS2 Dedicated Server com IA (CsBot)
echo       Ambiente 100%% Isolado (H:\CS2_AI_Server)
echo ========================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\check_env.ps1"

echo.
echo ========================================================
echo Servidor iniciando na porta 27016...
echo Executavel isolado: H:\CS2_AI_Server\game\bin\win64\cs2.exe
echo Mapa: de_mirage ^| Modo: Competitivo 5v5 ^| Bots: 10
echo Plugins: Metamod, CounterStrikeSharp, CS2-Bot-Improver, WeaponPaints, CsBotManager (IA IGL)
echo Para entrar no servidor pelo CS2 (no mesmo PC), abra o console e digite:
echo      connect 127.0.0.1:27016
echo ========================================================
echo.

"game\bin\win64\cs2.exe" -dedicated -insecure +sv_lan 1 -port 27016 +game_type 0 +game_mode 1 +map de_mirage +bot_quota 10 +bot_quota_mode fill +exec ai_competitive.cfg

pause
