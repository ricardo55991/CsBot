@echo off
chcp 65001 >nul
title CsBot Arsenal Web UI - Painel de Skins, Luvas e Facas
color 0B

echo ==============================================================================
echo                 CSBOT ARSENAL WEB UI - PAINEL DE SKINS & FACAS
echo ==============================================================================
echo.

:: 1. Verificar MariaDB (Porta 3306)
echo [*] Verificando conexao com o banco MariaDB local...
netstat -ano | findstr ":3306" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [+] MariaDB ja esta ativo na porta 3306.
) else (
    echo [*] MariaDB inativo. Inicializando banco portatil...
    if exist "H:\CS2_AI_Server\database\mariadb\bin\mysqld.exe" (
        start "" /min "H:\CS2_AI_Server\database\mariadb\bin\mysqld.exe" --defaults-file="H:\CS2_AI_Server\database\my.ini"
        timeout /t 2 /nobreak >nul
        echo [+] MariaDB inicializado com sucesso.
    ) else (
        echo [!] Aviso: Executavel do MariaDB nao encontrado em H:\CS2_AI_Server\database.
    )
)

echo.
:: 2. Verificar se a porta 8080 ja esta em uso
netstat -ano | findstr ":8080" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [+] O servidor do Arsenal Web UI ja esta em execucao na porta 8080!
    echo [*] Abrindo o painel no seu navegador padrao...
    start "" "http://localhost:8080"
    echo.
    echo ==============================================================================
    echo   O painel web ja esta online no seu navegador!
    echo   - Pressione ENTER para manter o servidor atual e fechar esta janela.
    echo   - Digite R e pressione ENTER se desejar forcar o reinicio do servidor.
    echo ==============================================================================
    set /p "OPT=Sua escolha [Enter para sair, R para reiniciar]: "
    if /i "%OPT%"=="R" (
        echo [*] Finalizando processo anterior na porta 8080...
        for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /f /pid %%p >nul 2>&1
        timeout /t 1 /nobreak >nul
        goto start_server
    )
    exit /b 0
)

:start_server
echo [*] Backend e Frontend estao unificados via FastAPI em uma unica aplicacao:
echo     - Backend API REST:  http://localhost:8080/api/
echo     - Frontend Panorama: http://localhost:8080/
echo.
echo [*] Abrindo o painel no seu navegador padrao...
start "" "http://localhost:8080"

echo.
echo ==============================================================================
echo   O painel web esta online! Escolha suas facas (Doppler Ruby, Sapphire, etc.),
echo   luvas e skins. No servidor CS2, digite !wp no chat para sincronizar!
echo ==============================================================================
echo.
echo [*] Servidor FastAPI em execucao... (Pressione Ctrl+C para encerrar)
echo.

cd /d "H:\CS2_AI_Server\arsenal_web"
python app.py

pause
