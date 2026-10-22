import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, BrowserContext, Page
from tracker import ApplicationsTracker, load_config

SESSIONS_DIR = Path(os.path.expanduser("~/.job_sessions"))
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def get_session_path(platform: str) -> Path:
    clean_name = platform.lower().replace("-", "_").replace(" ", "_")
    return SESSIONS_DIR / f"session_{clean_name}.json"

class JobBrowserEngine:
    """
    Motor Playwright silencioso ('por trás dos panos') para busca e candidatura automática
    em vagas de emprego PcD e TI (Inklua, InfoJobs, LinkedIn, PCD Online).
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.config = load_config()
        self.tracker = ApplicationsTracker()

    async def interactive_login(self, platform: str = "infojobs"):
        """Abre o navegador visível para autenticação interativa e salva os cookies/sessão."""
        session_file = get_session_path(platform)
        print("=" * 68)
        print(f" [CURRÍCULO AUTO-APPLY] Login Interativo: {platform.upper()}")
        print("=" * 68)
        
        url_map = {
            "linkedin": "https://www.linkedin.com/login",
            "inklua": "https://inklua.com/autenticacao/entrar",
            "pcd_online": "https://www.pcd.com.br/candidato",
            "infojobs": "https://www.infojobs.com.br/candidate/",
            "gupy": "https://login.gupy.io/",
            "indeed": "https://secure.indeed.com/auth"
        }
        target_url = url_map.get(platform.lower(), "https://www.infojobs.com.br/candidate/")

        print(f"1. Abrindo navegador em: {target_url}")
        print("2. Faça o login na sua conta normalmente.")
        print("3. Quando estiver autenticado na página inicial, volte aqui e pressione ENTER.")
        print("=" * 68)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(target_url)
            input("\n>>> Pressione ENTER no terminal APÓS concluir o login no navegador... <<<\n")

            await context.storage_state(path=str(session_file))
            print(f"\n[SUCESSO] Sessão salva em: {session_file}")
            await browser.close()

    async def get_context(self, p, platform: str) -> tuple[Any, BrowserContext, Page]:
        session_file = get_session_path(platform)
        browser = await p.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

        if session_file.exists():
            context = await browser.new_context(
                storage_state=str(session_file),
                user_agent=user_agent
            )
        else:
            context = await browser.new_context(user_agent=user_agent)

        page = await context.new_page()
        return browser, context, page

    async def search_inklua_jobs(
        self,
        keywords: str = "",
        home_office_only: bool = True,
        limit: int = 120
    ) -> List[Dict[str, Any]]:
        """Pesquisa vagas no portal especializado Inklua PcD com paginação inteligente e captura instantânea."""
        async with async_playwright() as p:
            browser, context, page = await self.get_context(p, "inklua")
            results = []
            try:
                base_url = "https://inklua.com/encontre-vagas-pcd"
                await page.add_init_script("""
                    window.__opened_urls = new Set();
                    window.open = function(url) {
                        window.__opened_urls.add(url);
                        return null;
                    };
                """)

                await page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(2500)

                # Fecha cookie banner se presente
                cb = page.locator("button:has-text('Concordar e fechar'), button:has-text('Aceitar')").first
                if await cb.count() > 0:
                    try:
                        await cb.click(force=True)
                        await page.wait_for_timeout(800)
                    except Exception:
                        pass

                # Se home_office_only, marca filtros de Remoto e Hibrido
                if home_office_only:
                    remoto_lbl = page.locator("label:has-text('Remoto')").first
                    if await remoto_lbl.count() > 0:
                        await remoto_lbl.click()
                        await page.wait_for_timeout(500)
                    hibrido_lbl = page.locator("label:has-text('Híbrido')").first
                    if await hibrido_lbl.count() > 0:
                        await hibrido_lbl.click()
                        await page.wait_for_timeout(500)

                    filtrar_btn = page.locator("button:has-text('Filtrar')").first
                    if await filtrar_btn.count() > 0:
                        await filtrar_btn.click()
                        await page.wait_for_timeout(2500)

                # Paginação com coleta rápida
                max_pages = max(1, (limit // 12) + 2)
                for p_num in range(max_pages):
                    await page.evaluate("""() => {
                        const btns = Array.from(document.querySelectorAll("button")).filter(b => b.textContent.includes("Ver detalhes"));
                        btns.forEach(b => b.click());
                    }""")

                    curr_size = await page.evaluate("() => window.__opened_urls.size")
                    if curr_size >= limit:
                        break

                    next_btn = page.locator("button[aria-label*='xima p'], button[aria-label*='Próxima página']").first
                    if await next_btn.count() > 0 and await next_btn.is_visible():
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                    else:
                        break

                raw_urls = await page.evaluate("() => Array.from(window.__opened_urls)")
                for r_url in raw_urls:
                    if len(results) >= limit:
                        break
                    full_link = f"https://inklua.com/{r_url.lstrip('/')}"
                    slug_parts = r_url.strip("/").split("/")
                    title_guess = slug_parts[1].replace("-", " ").title() if len(slug_parts) >= 2 else "Vaga Inklua PcD"
                    is_applied = self.tracker.is_already_applied(full_link)

                    results.append({
                        "titulo": title_guess,
                        "empresa": "Empresa Parceira Inklua",
                        "link": full_link,
                        "ja_candidatado": is_applied,
                        "plataforma": "Inklua",
                        "modalidade": "Home Office / Híbrido" if home_office_only else "PcD Geral"
                    })

                return results
            finally:
                await browser.close()

    async def apply_inklua_job(
        self,
        job_url: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Acessa a vaga no Inklua e clica em 'Gostei' para efetuar a candidatura."""
        if self.tracker.is_already_applied(job_url):
            return {
                "sucesso": False,
                "mensagem": "Vaga já foi candidatada anteriormente no Inklua! Envio cancelado para evitar duplicidade.",
                "url": job_url
            }

        async with async_playwright() as p:
            browser, context, page = await self.get_context(p, "inklua")
            try:
                await page.goto(job_url, wait_until="networkidle", timeout=45000)
                await page.wait_for_timeout(2000)

                title = (await page.title()).replace("Vaga PcD:", "").replace("| Inklua", "").strip()
                company = "Empresa Parceira Inklua"

                # Localiza o botão 'Gostei' (ação oficial de candidatura na Inklua)
                gostei_btn = page.locator("button:has-text('Gostei')").first

                if await gostei_btn.count() == 0:
                    return {
                        "sucesso": False,
                        "mensagem": "Botão 'Gostei' não encontrado ou candidatura já submetida anteriormente.",
                        "url": job_url,
                        "vaga": title
                    }

                btn_text = (await gostei_btn.inner_text()).strip()
                if "já deu um gostei" in btn_text.lower():
                    self.tracker.record_application(
                        job_title=title,
                        company=company,
                        platform="Inklua",
                        job_url=job_url,
                        status="Enviado",
                        notes="Identificada como já aplicada no portal Inklua",
                        resume_used=self.config.get("arquivos", {}).get("curriculo_padrao_pdf", "")
                    )
                    return {
                        "sucesso": False,
                        "mensagem": "Candidatura já havia sido submetida no Inklua anteriormente.",
                        "url": job_url,
                        "vaga": title
                    }

                if dry_run:
                    return {
                        "sucesso": True,
                        "modo": "DRY RUN (Simulação)",
                        "mensagem": f"Vaga identificada no Inklua: '{title}'. Botão 'Gostei' disponível para candidatura.",
                        "url": job_url
                    }

                # Clica em Gostei
                await gostei_btn.click()
                await page.wait_for_timeout(2500)

                # Registra no tracker
                self.tracker.record_application(
                    job_title=title,
                    company=company,
                    platform="Inklua",
                    job_url=job_url,
                    status="Enviado",
                    notes="Candidatura Inklua PcD (Gostei) em segundo plano",
                    resume_used=self.config.get("arquivos", {}).get("curriculo_padrao_pdf", "")
                )

                return {
                    "sucesso": True,
                    "mensagem": f"Candidatura enviada com sucesso no Inklua para '{title}'!",
                    "url": job_url,
                    "vaga": title
                }
            except Exception as e:
                return {
                    "sucesso": False,
                    "erro": str(e),
                    "url": job_url
                }
            finally:
                await browser.close()

    async def search_infojobs_jobs(
        self,
        keywords: str = "Desenvolvedor",
        home_office_only: bool = False,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Pesquisa vagas no portal InfoJobs com suporte a múltiplas páginas e limite configurável."""
        async with async_playwright() as p:
            browser, context, page = await self.get_context(p, "infojobs")
            results = []
            seen_hrefs = set()
            try:
                eh_pcd = self.config.get("candidato", {}).get("eh_pcd", False)
                encoded = keywords.replace(" ", "%20")
                base_url = "https://www.infojobs.com.br/vagas-de-emprego-pcd.aspx" if eh_pcd else "https://www.infojobs.com.br/vagas-de-emprego.aspx"

                current_page = 1
                max_pages = max(1, (limit // 15) + 2)

                while len(results) < limit and current_page <= max_pages:
                    url = f"{base_url}?palabra={encoded}" if current_page == 1 else f"{base_url}?palabra={encoded}&page={current_page}"
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(2000)

                    links = await page.locator("a[href*='/vaga-de-']").all()
                    if not links:
                        break

                    found_in_page = 0
                    for link_el in links:
                        if len(results) >= limit:
                            break
                        try:
                            href = await link_el.get_attribute("href")
                            if not href or href in seen_hrefs:
                                continue
                            seen_hrefs.add(href)

                            full_url = href if href.startswith("http") else f"https://www.infojobs.com.br{href}"
                            raw_text = (await link_el.inner_text()).strip()
                            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                            
                            title = lines[0] if lines else "Vaga InfoJobs"
                            company = lines[1] if len(lines) > 1 else "Empresa Confidencial"

                            if home_office_only:
                                lower_txt = raw_text.lower()
                                if not ("remoto" in lower_txt or "home office" in lower_txt):
                                    continue

                            is_applied = self.tracker.is_already_applied(full_url, title, company)

                            results.append({
                                "titulo": title,
                                "empresa": company,
                                "link": full_url,
                                "ja_candidatado": is_applied,
                                "plataforma": "InfoJobs",
                                "modalidade": "Home Office / Remoto" if ("remoto" in raw_text.lower() or "home office" in raw_text.lower()) else "Presencial / A combinar"
                            })
                            found_in_page += 1
                        except Exception:
                            continue

                    if found_in_page == 0:
                        break
                    current_page += 1

                return results
            finally:
                await browser.close()

    async def apply_infojobs_job(
        self,
        job_url: str,
        resume_pdf_path: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Abre uma vaga no InfoJobs headlessly e realiza a candidatura."""
        arquivos = self.config.get("arquivos", {})
        pdf_path = resume_pdf_path or arquivos.get("curriculo_padrao_pdf", "")

        if self.tracker.is_already_applied(job_url):
            return {
                "sucesso": False,
                "mensagem": "Vaga já foi candidatada anteriormente! Envio cancelado para evitar duplicidade.",
                "url": job_url
            }

        async with async_playwright() as p:
            browser, context, page = await self.get_context(p, "infojobs")
            try:
                await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(2500)

                title = "Vaga InfoJobs"
                company = "Empresa"
                try:
                    title_el = page.locator("h1, .js_titleVacancy").first
                    if await title_el.count() > 0:
                        title = (await title_el.inner_text()).strip()
                    comp_el = page.locator(".js_companyName, [data-component='CompanyName']").first
                    if await comp_el.count() > 0:
                        company = (await comp_el.inner_text()).strip()
                except Exception:
                    pass

                apply_btn = page.locator("a.js_btApplyVacancy, a:has-text('CANDIDATAR-ME'), button:has-text('CANDIDATAR-ME'), a:has-text('Candidatar-me'), [data-component='ApplyButton']").first

                if await apply_btn.count() == 0:
                    return {
                        "sucesso": False,
                        "mensagem": "Botão de candidatura não encontrado ou já candidatado.",
                        "url": job_url,
                        "vaga": title,
                        "empresa": company
                    }

                if dry_run:
                    return {
                        "sucesso": True,
                        "modo": "DRY RUN (Simulação)",
                        "mensagem": f"Vaga identificada no InfoJobs: '{title}' na empresa '{company}'. Botão 'CANDIDATAR-ME' disponível.",
                        "url": job_url,
                        "vaga": title,
                        "empresa": company
                    }

                await apply_btn.click()
                await page.wait_for_timeout(3000)

                file_inputs = page.locator("input[type='file']")
                if await file_inputs.count() > 0 and os.path.exists(pdf_path):
                    try:
                        await file_inputs.first.set_input_files(pdf_path)
                        await page.wait_for_timeout(1500)
                    except Exception:
                        pass

                confirm_btn = page.locator("button:has-text('Confirmar'), button:has-text('Finalizar'), button:has-text('Continuar')").first
                if await confirm_btn.count() > 0:
                    await confirm_btn.click()
                    await page.wait_for_timeout(2000)

                self.tracker.record_application(
                    job_title=title,
                    company=company,
                    platform="InfoJobs",
                    job_url=job_url,
                    status="Enviado",
                    notes="Candidatura automática InfoJobs em segundo plano",
                    resume_used=pdf_path
                )

                return {
                    "sucesso": True,
                    "mensagem": f"Candidatura enviada com sucesso no InfoJobs para '{title}' na empresa '{company}'!",
                    "url": job_url,
                    "vaga": title,
                    "empresa": company
                }
            except Exception as e:
                return {
                    "sucesso": False,
                    "erro": str(e),
                    "url": job_url
                }
            finally:
                await browser.close()

    async def search_linkedin_jobs(
        self,
        keywords: str = "Unity Developer",
        location: str = "Brasil",
        remote: bool = True,
        apenas_pcd: bool = False,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        async with async_playwright() as p:
            browser, context, page = await self.get_context(p, "linkedin")
            results = []
            try:
                search_query = f"{keywords} PcD" if apenas_pcd else keywords
                f_WT = "&f_WT=2" if remote else ""
                encoded_kw = search_query.replace(" ", "%20")
                encoded_loc = location.replace(" ", "%20")
                url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}&location={encoded_loc}{f_WT}&f_AL=true"

                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3000)

                cards = await page.locator(".job-card-container, .jobs-search-results__list-item").all()
                for idx, card in enumerate(cards):
                    if len(results) >= limit:
                        break
                    try:
                        title_el = card.locator(".job-card-list__title, .artdeco-entity-lockup__title a, a[data-control-id]").first
                        company_el = card.locator(".job-card-container__primary-description, .artdeco-entity-lockup__subtitle").first
                        link_el = card.locator("a[href*='/jobs/view/']").first

                        title = (await title_el.inner_text()).strip() if await title_el.count() > 0 else "Vaga"
                        company = (await company_el.inner_text()).strip() if await company_el.count() > 0 else "Empresa Confidencial"
                        link = await link_el.get_attribute("href") if await link_el.count() > 0 else ""

                        if link and not link.startswith("http"):
                            link = f"https://www.linkedin.com{link}"

                        is_applied = self.tracker.is_already_applied(link, title, company)

                        results.append({
                            "titulo": title,
                            "empresa": company,
                            "link": link,
                            "ja_candidatado": is_applied,
                            "plataforma": "LinkedIn",
                            "modalidade": "Home Office / Remoto" if remote else "Presencial/Híbrido",
                            "candidatura_simplificada": True
                        })
                    except Exception:
                        continue

                return results
            finally:
                await browser.close()

    async def apply_linkedin_job(
        self,
        job_url: str,
        resume_pdf_path: Optional[str] = None,
        laudo_pdf_path: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        candidato = self.config.get("candidato", {})
        arquivos = self.config.get("arquivos", {})
        pdf_path = resume_pdf_path or arquivos.get("curriculo_padrao_pdf", "")
        laudo_path = laudo_pdf_path or arquivos.get("laudo_medico_pdf", "")

        if self.tracker.is_already_applied(job_url):
            return {
                "sucesso": False,
                "mensagem": "Vaga já foi candidatada anteriormente! Envio cancelado para evitar duplicidade.",
                "url": job_url
            }

        async with async_playwright() as p:
            browser, context, page = await self.get_context(p, "linkedin")
            try:
                await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3000)

                title = "Vaga"
                company = "Empresa"
                try:
                    title_elem = page.locator("h1, .job-details-jobs-unified-top-card__job-title").first
                    if await title_elem.count() > 0:
                        title = (await title_elem.inner_text()).strip()
                    comp_elem = page.locator(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name").first
                    if await comp_elem.count() > 0:
                        company = (await comp_elem.inner_text()).strip()
                except Exception:
                    pass

                apply_button = page.locator("button.jobs-apply-button, button:has-text('Candidatura simplificada'), button:has-text('Easy Apply')").first
                
                if await apply_button.count() == 0:
                    return {
                        "sucesso": False,
                        "mensagem": "Botão de candidatura simplificada não encontrado nesta vaga.",
                        "url": job_url,
                        "vaga": title,
                        "empresa": company
                    }

                if dry_run:
                    return {
                        "sucesso": True,
                        "modo": "DRY RUN (Simulação)",
                        "mensagem": f"Vaga identificada: '{title}' na empresa '{company}'. Candidatura simplificada disponível.",
                        "url": job_url
                    }

                await apply_button.click()
                await page.wait_for_timeout(2000)

                max_steps = 7
                for step in range(max_steps):
                    file_inputs = page.locator("input[type='file']")
                    if await file_inputs.count() > 0:
                        for f_idx in range(await file_inputs.count()):
                            input_el = file_inputs.nth(f_idx)
                            label_txt = (await input_el.evaluate("el => el.parentElement ? el.parentElement.innerText : ''")).lower()
                            
                            if any(k in label_txt for k in ["laudo", "médico", "medico", "pcd", "cid"]):
                                if os.path.exists(laudo_path):
                                    await input_el.set_input_files(laudo_path)
                                    await page.wait_for_timeout(1000)
                            elif os.path.exists(pdf_path):
                                await input_el.set_input_files(pdf_path)
                                await page.wait_for_timeout(1000)

                    phone_input = page.locator("input[id*='phoneNumber'], input[name*='phone']").first
                    if await phone_input.count() > 0:
                        val = await phone_input.input_value()
                        if not val and candidato.get("telefone"):
                            await phone_input.fill(candidato.get("telefone"))

                    submit_btn = page.locator("button:has-text('Enviar candidatura'), button:has-text('Submit application')").first
                    if await submit_btn.count() > 0:
                        await submit_btn.click()
                        await page.wait_for_timeout(3000)
                        
                        self.tracker.record_application(
                            job_title=title,
                            company=company,
                            platform="LinkedIn",
                            job_url=job_url,
                            status="Enviado",
                            notes="Candidatura Simplificada automática em segundo plano",
                            resume_used=pdf_path
                        )
                        return {
                            "sucesso": True,
                            "mensagem": f"Currículo enviado com sucesso para '{title}' na empresa '{company}'!",
                            "url": job_url
                        }

                    next_btn = page.locator("button:has-text('Avançar'), button:has-text('Next'), button:has-text('Revisar'), button:has-text('Review')").first
                    if await next_btn.count() > 0:
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                    else:
                        break

                return {
                    "sucesso": False,
                    "mensagem": "Formulário continha etapas ou perguntas específicas que exigem revisão.",
                    "url": job_url,
                    "vaga": title,
                    "empresa": company
                }
            except Exception as e:
                return {
                    "sucesso": False,
                    "erro": str(e),
                    "url": job_url
                }
            finally:
                await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor de Automação de Currículo Headless")
    parser.add_argument("--login", type=str, choices=["linkedin", "inklua", "pcd_online", "infojobs", "gupy", "indeed"], help="Login interativo")
    parser.add_argument("--search", type=str, help="Termo de pesquisa de vagas")
    parser.add_argument("--platform", type=str, default="infojobs", choices=["infojobs", "inklua", "linkedin", "pcd_online", "gupy"])
    parser.add_argument("--limit", type=int, default=30, help="Limite de vagas")
    parser.add_argument("--apply", type=str, help="URL da vaga para se candidatar")
    parser.add_argument("--dry-run", action="store_true", help="Simula a candidatura sem envio")

    args = parser.parse_args()
    engine = JobBrowserEngine(headless=True)

    if args.login:
        asyncio.run(engine.interactive_login(args.login))
    elif args.search:
        if args.platform == "inklua":
            res = asyncio.run(engine.search_inklua_jobs(limit=args.limit))
        elif args.platform == "infojobs":
            res = asyncio.run(engine.search_infojobs_jobs(keywords=args.search, limit=args.limit))
        else:
            res = asyncio.run(engine.search_linkedin_jobs(keywords=args.search, limit=args.limit))
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.apply:
        if "inklua.com" in args.apply:
            res = asyncio.run(engine.apply_inklua_job(args.apply, dry_run=args.dry_run))
        elif "infojobs.com.br" in args.apply:
            res = asyncio.run(engine.apply_infojobs_job(args.apply, dry_run=args.dry_run))
        else:
            res = asyncio.run(engine.apply_linkedin_job(args.apply, dry_run=args.dry_run))
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
