@echo off
title CsBot - Servidor de Gravacao de Spots (Mirage)
color 0B

echo ================================================================================
echo          CsBot - MODO DE GRAVACAO E HOMOLOGACAO DE SPOTS (DE_MIRAGE)
echo ================================================================================
echo.
echo [*] Fechando qualquer processo CS2 anterior...
taskkill /F /IM cs2.exe >nul 2>nul
ping -n 2 127.0.0.1 >nul

echo [*] Configuracoes da Sessao:
echo     - Modo: Gravacao Livre (Zero Bots)
echo     - Imortalidade: Modo God / Buddha Ativado (HP: 99999)
echo     - Tempo de Round: 60 minutos
echo     - Tecla de Voo: [ALT Esquerdo] (Noclip ligado)
echo.
echo [*] Iniciando o Servidor CS2 Dedicado na porta 27016...
start "CsBot Dedicated Server (Gravacao)" /min cmd /c "cd /d H:\CS2_AI_Server && game\bin\win64\cs2.exe -dedicated -insecure +sv_lan 1 -port 27016 +game_type 0 +game_mode 1 +map de_mirage +bot_quota 0 +bot_quota_mode normal +bot_stop 1 +exec spot_recording.cfg +bot_kick"

echo [*] Aguardando 15 segundos para o servidor carregar a Mirage...
ping -n 16 127.0.0.1 >nul

echo.
echo [*] Conectando automaticamente seu CS2 ao servidor...
start "" "steam://run/730//+connect 127.0.0.1:27016"

echo.
echo ================================================================================
echo                      COMO USAR NO JOGO:
echo ================================================================================
echo   1. Pressione [ALT Esquerdo] para voar (noclip) ate o spot desejado.
echo   2. Pressione [ALT Esquerdo] novamente para pousar no chao.
echo   3. Fique em pe ou agachado (o sistema detecta automaticamente).
echo   4. Mire no alvo desejado (onde o bot deve mirar).
echo   5. Abra o CHAT do jogo (tecla Y) e digite:
echo.
echo         !spot_28    (ou !spot 28, com o numero do spot)
echo.
echo   6. O jogo vai avisar na tela e esperar 2 segundos.
echo   7. Mantenha a mira firme durante esses 2 segundos!
echo   8. O sistema grava Coordenadas [X, Y, Z], Mira (Yaw/Pitch) e Postura.
echo   9. O jogo confirma na tela grande e no chat:
echo.
echo         "[+] SPOT #XX GRAVADO! Pode ir para o proximo."
echo.
echo   COMANDOS UTEIS NO CHAT:
echo   - !god     : Reativa o modo imortal com 99999 HP
echo   - !noclip  : Alterna modo de voo (ou aperte ALT Esquerdo)
echo   - !kick    : Expulsa qualquer bot que tente entrar
echo ================================================================================
echo.
echo Mantenha esta janela aberta enquanto estiver gravando os spots.
echo Quando terminar, basta fechar o CS2 e esta janela.
pause
