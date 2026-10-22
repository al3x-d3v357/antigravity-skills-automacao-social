#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "================================================================="
echo "  [CURRICULO AUTO-APPLY] Configuração de Login de Sessão"
echo "================================================================="
echo "1 - Conectar conta do LinkedIn"
echo "2 - Conectar conta da Inklua (Portal de Vagas PcD)"
echo "3 - Conectar conta do PCD Online (pcd.com.br)"
echo "4 - Conectar conta do InfoJobs (Candidato PcD)"
echo "5 - Conectar conta do Indeed"
echo "================================================================="
read -p "Escolha a plataforma [1-5] (Padrão 1): " opt

case "$opt" in
    2) python3 "$DIR/browser_engine.py" --login inklua ;;
    3) python3 "$DIR/browser_engine.py" --login pcd_online ;;
    4) python3 "$DIR/browser_engine.py" --login infojobs ;;
    5) python3 "$DIR/browser_engine.py" --login indeed ;;
    *) python3 "$DIR/browser_engine.py" --login linkedin ;;
esac
