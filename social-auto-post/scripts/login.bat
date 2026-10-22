@echo off
setlocal
chcp 65001 >nul
title Social Auto-Post - Conectar Redes Sociais
color 0b

echo =================================================================
echo   [SOCIAL AUTO-POST] Configuracao de Login de Sessao
echo =================================================================
echo.
echo Escolha qual plataforma deseja conectar:
echo.
echo [1] Threads (Instagram) [Recomendado]
echo [2] Instagram Web
echo [3] X (antigo Twitter)
echo [4] TikTok Web / Studio
echo.
echo =================================================================
set "opt=1"
set /p opt="Escolha a plataforma [1, 2, 3 ou 4] (Padrao 1): "

if "%opt%"=="2" goto :login_insta
if "%opt%"=="3" goto :login_x
if "%opt%"=="4" goto :login_tiktok
goto :login_threads

:login_insta
echo.
echo Conectando conta do Instagram...
python "%~dp0instagram_poster.py" --login
goto :fim

:login_x
echo.
echo Conectando conta do X (Twitter)...
python "%~dp0x_poster.py" --login
goto :fim

:login_tiktok
echo.
echo Conectando conta do TikTok...
python "%~dp0tiktok_poster.py" --login
goto :fim

:login_threads
echo.
echo Conectando conta do Threads (Instagram)...
python "%~dp0threads_poster.py" --login
goto :fim

:fim
echo.
echo =================================================================
echo Processo finalizado! A sessao foi salva com seguranca.
echo O assistente agora podera publicar 100%% em segundo plano.
echo =================================================================
pause
