"""
Localizador inteligente de renderizacoes e imagens de projetos 3D autorais
localizados no repositorio D:\GitHub\arts3d para ilustrar artigos do blog.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict

sys.stdout.reconfigure(encoding='utf-8')

ARTS3D_DIR = Path(r"D:\GitHub\arts3d")

def find_project_renders(query: str = "", category: str = "") -> List[Dict[str, str]]:
    results = []
    if not ARTS3D_DIR.exists():
        print(f"AVISO: Diretorio {ARTS3D_DIR} nao encontrado.")
        return results

    search_dir = ARTS3D_DIR
    if category:
        cat_dir = ARTS3D_DIR / category
        if cat_dir.exists():
            search_dir = cat_dir

    valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    query_lower = query.lower()

    # Procura imagens
    for root, dirs, files in os.walk(search_dir):
        # Ignora pastas de frames individuais muito volumosas
        if "frames_flat" in root or "frames_gray" in root or "turntable_frames" in root:
            continue
            
        for file in files:
            p = Path(root) / file
            if p.suffix.lower() in valid_extensions:
                rel_path = str(p.relative_to(ARTS3D_DIR))
                full_str = str(p).lower()
                
                # Se houver query, filtra
                if query_lower and (query_lower not in full_str):
                    continue
                    
                # Prioriza previews, renders ainda e specs
                score = 0
                if "preview" in full_str:
                    score += 50
                if "specs" in full_str:
                    score += 40
                if "render" in full_str:
                    score += 30
                if "still" in full_str:
                    score += 20
                if "hero" in full_str:
                    score += 25
                    
                results.append({
                    "name": file,
                    "rel_path": rel_path,
                    "full_path": str(p),
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "score": score
                })

    # Ordena pelo score decrescente
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def main():
    parser = argparse.ArgumentParser(description="Localizador de Renders 3D para o Blog")
    parser.add_argument("--query", type=str, default="", help="Termo de busca (ex: noah, waguri, escudo, car)")
    parser.add_argument("--category", type=str, default="", help="Categoria (personagens, armas_e_props, veiculos, torres)")
    parser.add_argument("--limit", type=int, default=10, help="Limite de resultados (Padrao: 10)")

    args = parser.parse_args()
    renders = find_project_renders(args.query, args.category)

    print("=" * 72)
    print(f"  RENDERS ENCONTRADOS EM ARTS3D ({len(renders)} resultados)")
    print(f"  Filtros: Query='{args.query}' | Categoria='{args.category}'")
    print("=" * 72)
    for i, r in enumerate(renders[:args.limit], 1):
        print(f"{i}. [{r['score']} pts | {r['size_kb']} KB] {r['rel_path']}")
        print(f"   Caminho: {r['full_path']}")
    print("=" * 72)

if __name__ == "__main__":
    main()
