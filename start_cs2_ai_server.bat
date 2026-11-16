@echo off
title CS2 AI Dedicated Server [connect 127.0.0.1:27016]

cd /d "H:\CS2_AI_Server"

echo ================================================================================
echo             Iniciando CS2 Dedicated Server com IA (CsBot)
echo             Ambiente 100%% Isolado (H:\CS2_AI_Server)
echo ================================================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\check_env.ps1"

echo.
echo [*] Iniciando Voice IGL Client (Push-to-Talk via Faster-Whisper)...
start "CsBot Voice IGL (PTT: Segure V)" cmd /k "cd /d H:\CS2_AI_Server\voice_client && python voice_igl_client.py"

echo.
echo [*] Iniciando Arsenal Web UI (Painel de Skins, Luvas e Facas Doppler)...
start "CsBot Arsenal Web UI" /min cmd /c "cd /d H:\CS2_AI_Server\arsenal_web && python app.py"

echo.
echo ================================================================================
echo   Servidor iniciando na porta 27016...
echo   Mapa: de_mirage ^| Modo: Competitivo 5v5 ^| Bots: 10
echo   Voice Bridge: http://127.0.0.1:27080/voice/ (Segure 'V' para falar)
echo   Arsenal Web UI: http://localhost:8080 (Painel Visual de Skins e Luvas)
echo   Radar 2D (2a Tela): http://localhost:8080/radar (Central de Comando ao Vivo)
echo.
echo   ******************************************************************************
echo   *              ^>^>^> CONECTAR AO SERVIDOR NO SEU CS2: ^<^<^<                      *
echo   *                                                                            *
echo   *                        connect 127.0.0.1:27016                             *
echo   *                                                                            *
echo   *   (Digite no console ['] do CS2 ou execute o script 'conectar_cs2.bat')    *
echo   ******************************************************************************
echo ================================================================================
echo.
echo [*] Carregando mapa de_mirage e plugins de IA (aguarde ~15 segundos antes de conectar)...
echo [*] Servidor em execucao! Mantenha esta janela aberta enquanto estiver jogando.
echo.

"game\bin\win64\cs2.exe" -dedicated -insecure +sv_lan 1 -port 27016 +game_type 0 +game_mode 1 +map de_mirage +bot_quota 10 +bot_quota_mode fill +exec ai_competitive.cfg

echo.
echo [!] O servidor CS2 foi encerrado.
pause
