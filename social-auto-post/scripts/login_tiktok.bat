@echo off
setlocal
chcp 65001 >nul
title Conectar TikTok - Social Auto-Post
color 0b

echo =================================================================
echo   [TIKTOK] Conectar Conta do TikTok
echo =================================================================
echo.
echo Abrindo navegador para conectar sua conta do TikTok...
echo.

python "%~dp0tiktok_poster.py" --login

echo.
echo =================================================================
pause
