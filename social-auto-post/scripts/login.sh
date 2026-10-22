#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "================================================================="
echo "  [SOCIAL AUTO-POST] Configuração de Login de Sessão"
echo "================================================================="
echo ""
echo "Escolha qual plataforma deseja conectar:"
echo ""
echo "[1] Threads (Instagram) [Recomendado]"
echo "[2] Instagram Web"
echo "[3] X (antigo Twitter)"
echo "[4] TikTok Web / Studio"
echo ""
echo "================================================================="
read -p "Escolha a plataforma [1, 2, 3 ou 4] (Padrão 1): " opt

case "$opt" in
    2) python3 "$DIR/instagram_poster.py" --login ;;
    3) python3 "$DIR/x_poster.py" --login ;;
    4) python3 "$DIR/tiktok_poster.py" --login ;;
    *) python3 "$DIR/threads_poster.py" --login ;;
esac
