import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Garante path de imports locais
sys.path.append(str(Path(__file__).parent))

from browser_engine import JobBrowserEngine, get_session_path
from tracker import ApplicationsTracker, load_config

# Inicializa o servidor FastMCP
mcp = FastMCP("curriculo-apply")

@mcp.tool()
async def vagas_buscar(
    termo: str = "Desenvolvedor de Jogos",
    plataforma: str = "infojobs",
    apenas_remotas: bool = False,
    limite: int = 5
) -> List[Dict[str, Any]]:
    """
    Pesquisa vagas de emprego em segundo plano ('por trás dos panos' via Playwright headless).
    
    Args:
        termo: Cargo ou tecnologia (ex: 'Desenvolvedor de Jogos', 'Unity Developer', 'Technical Artist', 'Python').
        plataforma: Portal ('infojobs', 'linkedin', 'inklua', 'pcd_online' ou 'gupy').
        apenas_remotas: Se True, filtra apenas vagas Home Office / Remotas.
        limite: Quantidade máxima de vagas a retornar (padrão: 5).
        
    Returns:
        Lista de vagas com título, empresa, link, modalidade e indicador de duplicidade.
    """
    engine = JobBrowserEngine(headless=True)
    plat = plataforma.lower()
    if plat == "infojobs":
        return await engine.search_infojobs_jobs(keywords=termo, home_office_only=apenas_remotas, limit=limite)
    elif plat == "inklua":
        return await engine.search_inklua_jobs(keywords=termo, home_office_only=apenas_remotas, limit=limite)
    elif plat == "pcd_online":
        return await engine.search_pcd_online_jobs(keywords=termo, home_office_only=apenas_remotas, limit=limite)
    else:
        return await engine.search_linkedin_jobs(
            keywords=termo,
            remote=apenas_remotas,
            limit=limite
        )

@mcp.tool()
async def vagas_candidatar(
    url_vaga: str,
    simulacao: bool = True,
    curriculo_pdf_custom: Optional[str] = None
) -> Dict[str, Any]:
    """
    Realiza a candidatura e envio de currículo em segundo plano ('por trás dos panos') no InfoJobs ou LinkedIn.
    
    Args:
        url_vaga: URL completa da vaga para candidatura (InfoJobs ou LinkedIn).
        simulacao: Se True (recomendado), inspeciona os botões e valida o formulário sem submeter definitivamente.
        curriculo_pdf_custom: Caminho opcional para PDF específico do currículo.
        
    Returns:
        Dicionário com o resultado da candidatura e status registrado.
    """
    engine = JobBrowserEngine(headless=True)
    if "infojobs.com.br" in url_vaga:
        return await engine.apply_infojobs_job(
            job_url=url_vaga,
            resume_pdf_path=curriculo_pdf_custom,
            dry_run=simulacao
        )
    else:
        return await engine.apply_linkedin_job(
            job_url=url_vaga,
            resume_pdf_path=curriculo_pdf_custom,
            dry_run=simulacao
        )

@mcp.tool()
async def vagas_historico() -> Dict[str, Any]:
    """
    Retorna o resumo do histórico de candidaturas enviadas, métricas por plataforma e status.
    Evita envios repetidos.
    """
    tracker = ApplicationsTracker()
    return tracker.get_summary()

@mcp.tool()
async def vagas_status_sessao(plataforma: str = "infojobs") -> Dict[str, Any]:
    """
    Verifica se a sessão do usuário (cookies/storage_state) está salva e configurada para automação headless.
    
    Args:
        plataforma: Nome da plataforma ('infojobs', 'linkedin', 'inklua', 'pcd_online', 'gupy' ou 'indeed').
    """
    session_file = get_session_path(plataforma)
    existe = session_file.exists()
    return {
        "plataforma": plataforma,
        "sessao_salva": existe,
        "caminho_arquivo": str(session_file),
        "orientacao": "Pronto para operação em segundo plano!" if existe else f"Execute 'login.bat' para conectar sua conta {plataforma} uma única vez."
    }

if __name__ == "__main__":
    mcp.run()
