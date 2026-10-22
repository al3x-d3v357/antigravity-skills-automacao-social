@echo off
title Curriculo Auto-Apply - Login de Sessao (Portais PcD & Tech)
echo =================================================================
echo   [CURRICULO AUTO-APPLY] Configuracao de Login de Sessao
echo =================================================================
echo 1 - Conectar conta do LinkedIn
echo 2 - Conectar conta da Inklua (Portal de Vagas PcD)
echo 3 - Conectar conta do PCD Online (pcd.com.br)
echo 4 - Conectar conta do InfoJobs (Candidato PcD)
echo 5 - Conectar conta do Indeed
echo =================================================================
set /p opt="Escolha a plataforma [1-5] (Padrao 1): "

if "%opt%"=="2" (
    python "%~dp0browser_engine.py" --login inklua
) else if "%opt%"=="3" (
    python "%~dp0browser_engine.py" --login pcd_online
) else if "%opt%"=="4" (
    python "%~dp0browser_engine.py" --login infojobs
) else if "%opt%"=="5" (
    python "%~dp0browser_engine.py" --login indeed
) else (
    python "%~dp0browser_engine.py" --login linkedin
)

pause
