import sys
import os
import json
import asyncio
import argparse
from pathlib import Path
from browser_engine import JobBrowserEngine
from tracker import ApplicationsTracker, load_config

async def run_pipeline(
    termo: str = "",
    plataforma: str = "inklua",
    limite: int = 20,
    apenas_remoto: bool = True,
    auto_submit: bool = False,
    dry_run: bool = True
):
    """Executa a varredura e envio automatizado de currículos em segundo plano."""
    cfg = load_config()
    tracker = ApplicationsTracker()
    engine = JobBrowserEngine(headless=True)
    eh_pcd = cfg.get("candidato", {}).get("eh_pcd", True)

    print("=" * 68)
    print(" [CURRÍCULO AUTO-APPLY] Varredura em Segundo Plano ('Por Trás dos Panos')")
    print(f" Plataforma: {plataforma.upper()} | Limite: {limite} | Home Office: {apenas_remoto}")
    print(f" Modo: {'SIMULAÇÃO (DRY RUN)' if dry_run else 'ENVIO REAL'}")
    print("=" * 68)

    plat = plataforma.lower()
    if plat == "inklua":
        vagas = await engine.search_inklua_jobs(home_office_only=apenas_remoto, limit=limite)
    elif plat == "infojobs":
        vagas = await engine.search_infojobs_jobs(keywords=termo, home_office_only=apenas_remoto, limit=limite)
    elif plat == "pcd_online":
        vagas = await engine.search_pcd_online_jobs(keywords=termo, home_office_only=apenas_remoto, limit=limite)
    else:
        vagas = await engine.search_linkedin_jobs(keywords=termo, remote=apenas_remoto, apenas_pcd=eh_pcd, limit=limite)

    print(f"\n[+] Oportunidades encontradas: {len(vagas)}")
    novas = [v for v in vagas if not v.get("ja_candidatado")]
    print(f"[+] Oportunidades inéditas no histórico: {len(novas)}")

    if not auto_submit:
        print("\n--- Oportunidades Encontradas ---")
        for i, v in enumerate(vagas, 1):
            status_tag = "[JÁ ENVIADO]" if v.get("ja_candidatado") else "[NOVA]"
            print(f"{i}. {status_tag} {v.get('titulo')} @ {v.get('empresa')}")
            print(f"   Modalidade: {v.get('modalidade', 'A combinar')} | Link: {v.get('link')}")
        return vagas

    aplicadas = 0
    for v in novas:
        if aplicadas >= limite:
            break
        print(f"\n>> Processando candidatura: {v.get('titulo')}...")
        link = v.get("link", "")
        if "inklua.com" in link:
            res = await engine.apply_inklua_job(link, dry_run=dry_run)
        elif "infojobs.com.br" in link:
            res = await engine.apply_infojobs_job(link, dry_run=dry_run)
        else:
            res = await engine.apply_linkedin_job(link, dry_run=dry_run)
            
        print(f"   Resultado: {res.get('mensagem', res)}")
        if res.get("sucesso"):
            aplicadas += 1
        await asyncio.sleep(2)

    print("\n" + "=" * 68)
    print(f" [CONCLUÍDO] Processo finalizado! Candidaturas processadas: {aplicadas}")
    print("=" * 68)
    return vagas

async def run_batch_30(plataforma: str = "infojobs", live: bool = False, total_alvo: int = 30):
    """Executa a busca e aplicação em lote com prioridade para vagas PcD."""
    cfg = load_config()
    tracker = ApplicationsTracker()
    engine = JobBrowserEngine(headless=True)
    eh_pcd = cfg.get("candidato", {}).get("eh_pcd", True)

    if plataforma.lower() == "inklua":
        print("=" * 70)
        print(f" [CURRÍCULO AUTO-APPLY] LOTE INKLUA PCD HOME OFFICE: {total_alvo} VAGAS")
        print(f" Modo: {'ENVIO REAL' if live else 'SIMULAÇÃO (DRY RUN)'}")
        print("=" * 70)
        vagas = await engine.search_inklua_jobs(home_office_only=True, limit=total_alvo)
        all_candidates = [v for v in vagas if not tracker.is_already_applied(v.get("link", ""))]
    else:
        terms = [
            "TI", "Tecnologia", "Desenvolvedor", "Assistente de TI",
            "Suporte", "Mobile", "Analista de TI", "Estagio TI",
            "Operacoes", "Qualidade"
        ] if eh_pcd else [
            "Desenvolvedor Android", "Desenvolvedor Mobile", "Desenvolvedor Flutter",
            "Estagio Desenvolvimento Software", "Desenvolvedor de Jogos",
            "Desenvolvedor Front-End", "Desenvolvedor Unity", "Analista de QA"
        ]

        print("=" * 70)
        print(f" [CURRÍCULO AUTO-APPLY] LOTE ESTRATÉGICO: {total_alvo} VAGAS")
        print(f" Plataforma: {plataforma.upper()} | Foco PcD: {eh_pcd} | Modo: {'ENVIO REAL' if live else 'SIMULAÇÃO (DRY RUN)'}")
        print("=" * 70)

        all_candidates = []
        seen = set()

        for term in terms:
            if len(all_candidates) >= total_alvo:
                break
            print(f"[+] Buscando vagas {'PcD ' if eh_pcd else ''}por: '{term}'...")
            if plataforma.lower() == "infojobs":
                vagas = await engine.search_infojobs_jobs(keywords=term, limit=12)
            else:
                vagas = await engine.search_linkedin_jobs(keywords=term, apenas_pcd=eh_pcd, limit=12)

            for v in vagas:
                link = v.get("link", "")
                if link and link not in seen and not tracker.is_already_applied(link):
                    seen.add(link)
                    all_candidates.append(v)
                    if len(all_candidates) >= total_alvo:
                        break
            await asyncio.sleep(1)

    print(f"\n[+] Total de vagas inéditas reunidas para processamento: {len(all_candidates)}")
    print("-" * 70)

    processadas = 0
    sucessos = 0

    for idx, vaga in enumerate(all_candidates, 1):
        titulo = vaga.get("titulo", "Vaga")
        empresa = vaga.get("empresa", "Empresa")
        link = vaga.get("link", "")

        print(f"\n[{idx}/{len(all_candidates)}] Processando: {titulo} @ {empresa}")
        print(f"      Link: {link}")

        if "inklua.com" in link:
            res = await engine.apply_inklua_job(link, dry_run=not live)
        elif "infojobs.com.br" in link:
            res = await engine.apply_infojobs_job(link, dry_run=not live)
        else:
            res = await engine.apply_linkedin_job(link, dry_run=not live)

        msg = res.get("mensagem", str(res))
        status_txt = "[OK]" if res.get("sucesso") else "[AVISO]"
        print(f"      Resultado: {status_txt} {msg}")

        if res.get("sucesso"):
            sucessos += 1
        processadas += 1

        if live:
            await asyncio.sleep(3)
        else:
            await asyncio.sleep(1)

    print("\n" + "=" * 70)
    print(f" [RELATÓRIO FINAL] Lote de {processadas} vagas concluído!")
    print(f" Sucessos: {sucessos} | Modo: {'ENVIO REAL' if live else 'SIMULAÇÃO CONCLUÍDA'}")
    print("=" * 70)
    return all_candidates

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automação de Envio de Currículos")
    parser.add_argument("--query", "-q", type=str, default="", help="Termo de pesquisa de vagas")
    parser.add_argument("--platform", "-p", type=str, default="inklua", choices=["inklua", "infojobs", "linkedin", "pcd_online", "gupy"])
    parser.add_argument("--limit", "-l", type=int, default=30, help="Quantidade máxima de vagas")
    parser.add_argument("--remoto", action="store_true", default=True, help="Filtra apenas vagas remotas")
    parser.add_argument("--submit", action="store_true", help="Efetua o envio/candidatura (padrão é apenas listar)")
    parser.add_argument("--live", action="store_true", help="Desativa modo simulação (envio real)")
    parser.add_argument("--batch30", action="store_true", help="Executa o lote estratégico de vagas")
    parser.add_argument("--summary", action="store_true", help="Mostra histórico e métricas de candidaturas")

    args = parser.parse_args()

    if args.summary:
        tracker = ApplicationsTracker()
        print(json.dumps(tracker.get_summary(), indent=2, ensure_ascii=False))
    elif args.batch30:
        asyncio.run(run_batch_30(plataforma=args.platform, live=args.live, total_alvo=args.limit))
    else:
        asyncio.run(run_pipeline(
            termo=args.query,
            plataforma=args.platform,
            limite=args.limit,
            apenas_remoto=args.remoto,
            auto_submit=args.submit,
            dry_run=not args.live
        ))
