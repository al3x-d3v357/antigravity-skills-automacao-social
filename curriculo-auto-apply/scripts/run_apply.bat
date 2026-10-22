@echo off
title Curriculo Auto-Apply - Busca e Candidatura Estrategica
echo =================================================================
echo   [CURRICULO AUTO-APPLY] Busca e Candidatura Estrategica
echo =================================================================
echo Escolha a Frente Profissional:
echo 1 - Frente 1: Mobile & Android (Kotlin / Jetpack Compose / Jr / Estagio)
echo 2 - Frente 2: Games & Front-End / UI (Unity / C# / UI-UX)
echo 3 - Frente 3: Dados, Operacoes & QA / Suporte Tecnico
echo 4 - Digitar termo customizado
echo 5 - Ver historico e estatisticas de candidaturas
echo =================================================================
set /p opt_frente="Escolha a opcao [1-5] (Padrao 1): "

if "%opt_frente%"=="5" (
    python "%~dp0auto_apply.py" --summary
    pause
    exit /b
)

if "%opt_frente%"=="2" (
    set query=Desenvolvedor Unity
) else if "%opt_frente%"=="3" (
    set query=Analista de QA
) else if "%opt_frente%"=="4" (
    set /p query="Digite o termo ou tecnologia desejada: "
) else (
    set query=Desenvolvedor Android
)

echo.
echo Escolha o Portal de Vagas:
echo 1 - InfoJobs (Conectado)
echo 2 - LinkedIn (Remoto)
echo 3 - Inklua (Portal PcD Remoto)
echo 4 - PCD Online (Home Office)
set /p opt_portal="Escolha o portal [1-4] (Padrao 1): "

if "%opt_portal%"=="2" (
    set plat=linkedin
) else if "%opt_portal%"=="3" (
    set plat=inklua
) else if "%opt_portal%"=="4" (
    set plat=pcd_online
) else (
    set plat=infojobs
)

echo.
echo Modo de Operacao:
echo 1 - Apenas listar oportunidades (Sem submissao)
echo 2 - Simular candidaturas (Dry-Run seguro com inspecao)
echo 3 - Enviar candidaturas REAIS em segundo plano
set /p opt_mode="Escolha o modo [1-3] (Padrao 1): "

if "%opt_mode%"=="2" (
    python "%~dp0auto_apply.py" -q "%query%" -p %plat% --submit
) else if "%opt_mode%"=="3" (
    python "%~dp0auto_apply.py" -q "%query%" -p %plat% --submit --live
) else (
    python "%~dp0auto_apply.py" -q "%query%" -p %plat%
)

pause
