import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

sys.stdout.reconfigure(encoding='utf-8')

SESSIONS_DIR = Path(os.path.expanduser("~/.social_sessions"))
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = SESSIONS_DIR / "session_blogspot.json"
HISTORY_FILE = SESSIONS_DIR / "blogspot_posts_history.json"
CONFIG_FILE = Path(__file__).parent / "config.json"

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def record_post_history(title: str, text: str, media_paths: List[str], success: bool, details: str = ""):
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": "Blogspot (Blogger)",
        "title": title,
        "text": text[:300] + ("..." if len(text) > 300 else ""),
        "media": media_paths,
        "success": success,
        "details": details
    }
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def show_history():
    if not HISTORY_FILE.exists():
        log("Nenhum historico de publicacoes no Blogspot encontrado.")
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        print("=" * 72)
        print(f"  HISTORICO DE PUBLICACOES NO BLOGSPOT ({len(history)} registros)")
        print("=" * 72)
        for i, post in enumerate(reversed(history[-10:]), 1):
            status = "[SUCESSO]" if post.get("success") else "[FALHA]"
            print(f"{i}. {post.get('timestamp')} | {status} - {post.get('title')}")
            if post.get("details"):
                print(f"   Detalhes: {post.get('details')}")
        print("=" * 72)
    except Exception as e:
        log(f"Erro ao ler historico: {e}")

def interactive_login():
    """Abre o navegador visivel para autenticar a conta Google no Blogspot (Blogger) e salva a sessao."""
    print("=" * 72)
    print("  [SOCIAL AUTO-POST] Configuracao de Login - BLOGSPOT (Blogger)")
    print("=" * 72)
    print("1. O navegador sera aberto na pagina do Blogger (blogger.com).")
    print("2. Faca login na sua conta Google vinculada ao seu blog.")
    print("3. Quando estiver na tela de gerenciamento de postagens do seu blog,")
    print("   volte aqui neste terminal e pressione a tecla ENTER para salvar a sessao.")
    print("=" * 72)

    with sync_playwright() as p:
        # Prioriza Chrome instalado para evitar bloqueios de bot no login do Google
        try:
            browser = p.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception:
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        log("Navegando para https://www.blogger.com/ ...")
        page.goto("https://www.blogger.com/")

        print("\n>>> Aguardando voce fazer login na sua conta do Blogger no navegador aberto... <<<")
        input(">>> Pressione ENTER AQUI apos concluir o login e estar no painel do seu blog... <<<\n")

        # Salva o estado da sessao (cookies, storage, autenticacao Google)
        context.storage_state(path=str(SESSION_FILE))
        current_url = page.url
        log(f"SUCESSO! Credenciais e sessao do Blogspot salvas em: {SESSION_FILE}")
        log(f"URL detectada: {current_url}")

        browser.close()
        return True

def post_blogspot(
    title: str,
    content: str,
    labels: Optional[str] = None,
    media_paths: Optional[List[str]] = None,
    draft: bool = False,
    headless: bool = True
) -> bool:
    """Publica uma postagem no Blogspot (Blogger) de forma autonoma."""
    if not SESSION_FILE.exists():
        log("ERRO: Nenhuma sessao encontrada para o Blogspot!")
        log("Execute primeiro a configuracao de login: python blogspot_poster.py --login")
        return False

    if not title:
        title = "Nova Atualizacao"

    log(f"Iniciando publicacao no Blogspot... (Headless: {headless})")
    log(f"Titulo: '{title}'")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                channel="chrome",
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception:
            browser = p.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"]
            )

        context = browser.new_context(
            storage_state=str(SESSION_FILE),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 900}
        )
        page = context.new_page()

        try:
            blog_id = None
            if CONFIG_FILE.exists():
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        blog_id = cfg.get("blogspot", {}).get("blog_id")
                except Exception:
                    pass

            if blog_id:
                log(f"Acessando editor de nova postagem do blog {blog_id}...")
                page.goto(f"https://www.blogger.com/blog/post/edit/{blog_id}/new", wait_until="networkidle", timeout=45000)
            else:
                log("Acessando painel do Blogger...")
                page.goto("https://www.blogger.com/", wait_until="networkidle", timeout=45000)
            time.sleep(3)

            # Verifica se caiu na tela de login
            if "accounts.google.com" in page.url or "blogger.com/about" in page.url:
                log("ERRO: A sessao do Blogspot expirou ou nao esta autenticada.")
                log("Por favor, execute o login novamente: python blogspot_poster.py --login")
                record_post_history(title, content, media_paths or [], False, "Sessao expirada")
                browser.close()
                return False

            # Se ainda nao estiver na pagina de edicao, clica no botao de Nova Postagem
            if "/post/edit" not in page.url:
                log("Clicando em 'Criar nova postagem'...")
                btn = page.locator("div[aria-label='Criar nova postagem']:visible, a[aria-label*='Criar nova postagem']:visible").first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                else:
                    # Fallback para clique geral
                    page.locator("[aria-label*='Criar nova postagem'], [aria-label*='Nova postagem']").first.click()
                
                try:
                    page.wait_for_url("**/post/edit/**", timeout=25000)
                except Exception:
                    pass

            time.sleep(3)
            page.wait_for_load_state("domcontentloaded")

            # 1. Preenche o Titulo da postagem
            log("Preenchendo titulo...")
            title_input = page.locator("input.whsOnd[type='text'], input[aria-label*='Título'], input[placeholder*='Título']").first
            if title_input.count() > 0 and title_input.is_visible():
                title_input.click()
                title_input.fill(title)
            else:
                log("Tentando focar primeiro campo de texto para o titulo...")
                page.locator("input[type='text']").first.fill(title)

            time.sleep(1)

            # 2. Preenche o Conteudo / Corpo da postagem
            log("Preenchendo corpo da postagem...")
            editor_found = False

            # Prioridade 1: CodeMirror (modo nativo de alta fidelidade do Blogger)
            try:
                cm_result = page.evaluate("""(html) => {
                    const cmEl = document.querySelector('.CodeMirror');
                    if (cmEl && cmEl.CodeMirror) {
                        cmEl.CodeMirror.setValue(html);
                        cmEl.CodeMirror.save();
                        return true;
                    }
                    return false;
                }""", content)
                if cm_result:
                    editor_found = True
                    log("Conteudo HTML inserido com sucesso via CodeMirror nativo.")
            except Exception as e:
                log(f"Aviso no preenchimento via CodeMirror: {e}")

            if not editor_found:
                try:
                    editor_frame = page.frame_locator("iframe.editable")
                    editor_body = editor_frame.locator("body")
                    if editor_body.count() > 0:
                        editor_body.first.evaluate("(body, html) => { body.innerHTML = html; }", content)
                        editor_found = True
                        log("Conteudo HTML inserido com sucesso via iframe.editable.")
                except Exception as e:
                    log(f"Aviso no preenchimento via iframe.editable: {e}")

            if not editor_found:
                # Tenta localizar por frames iterativos
                for frame in page.frames:
                    try:
                        body_elem = frame.query_selector("body[contenteditable='true']")
                        if body_elem:
                            frame.evaluate("(elem, html) => { elem.innerHTML = html; }", [body_elem, content])
                            editor_found = True
                            log("Conteudo inserido via frame iterativo.")
                            break
                    except Exception:
                        pass

            if not editor_found:
                ce = page.locator("div[contenteditable='true']:visible").first
                if ce.count() > 0:
                    ce.evaluate("(elem, html) => { elem.innerHTML = html; }", content)
                    editor_found = True
                    log("Conteudo inserido via div contenteditable principal.")

            time.sleep(2)

            # 3. Marcadores / Labels (se fornecido)
            if labels:
                log(f"Configurando marcadores: {labels}")
                try:
                    clean_labels = ", ".join([l.strip().lstrip("#") for l in labels.replace(" ", ",").split(",") if l.strip()])
                    labels_inp = page.locator("textarea[aria-label*='Separar com vírgulas'], textarea[aria-label*='Marcador']").first
                    if labels_inp.count() > 0:
                        labels_inp.click()
                        labels_inp.fill(clean_labels)
                        page.keyboard.press("Enter")
                    else:
                        label_btn = page.locator("div[data-name='labels'], div[aria-label*='Marcador']").first
                        if label_btn.count() > 0 and label_btn.is_visible():
                            label_btn.click()
                            time.sleep(1)
                            page.locator("textarea[aria-label*='Separar com vírgulas']").first.fill(clean_labels)
                            page.keyboard.press("Enter")
                except Exception as e:
                    log(f"Aviso ao preencher marcadores: {e}")

            time.sleep(2)

            # 4. Publicar ou Salvar Rascunho
            if draft:
                log("Salvando como rascunho...")
                back_btn = page.locator("div[aria-label*='Voltar']:visible, a[aria-label*='Voltar']:visible").first
                if back_btn.count() > 0:
                    back_btn.click()
                time.sleep(3)
                log("SUCESSO: Postagem salva como rascunho no Blogspot.")
                record_post_history(title, content, media_paths or [], True, "Salvo como rascunho")
                browser.close()
                return True

            log("Publicando postagem no Blogspot...")
            pub_btn = page.locator("div[role='button']:has-text('Publicar'), div[aria-label='Publicar']:visible").first
            if pub_btn.count() > 0 and pub_btn.is_visible():
                pub_btn.click()
                time.sleep(2)

                # Modal de confirmacao: "CONFIRMAR" / "Confirmar"
                confirm_btn = page.locator("div[role='button']:has-text('CONFIRMAR'), span:has-text('CONFIRMAR'), div[role='dialog'] button:has-text('Confirmar')").first
                if confirm_btn.count() > 0:
                    confirm_btn.evaluate("el => el.click()")
                    log("Confirmacao de publicacao enviada via evaluate.")

                time.sleep(4)
                log(f"SUCESSO! Postagem '{title}' publicada no Blogspot.")
                record_post_history(title, content, media_paths or [], True, "Publicado com sucesso")
                browser.close()
                return True
            else:
                log("ERRO: Nao foi possivel encontrar o botao 'Publicar'.")
                record_post_history(title, content, media_paths or [], False, "Botao publicar nao encontrado")
                browser.close()
                return False

        except Exception as e:
            log(f"ERRO durante publicacao no Blogspot: {e}")
            record_post_history(title, content, media_paths or [], False, str(e))
            browser.close()
            return False

def main():
    parser = argparse.ArgumentParser(description="Publicador Autonomo para Blogspot (Blogger)")
    parser.add_argument("--login", action="store_true", help="Abre o navegador para autenticar conta do Blogspot/Google")
    parser.add_argument("--title", type=str, default="", help="Titulo da postagem no blog")
    parser.add_argument("--post", "--content", dest="content", type=str, help="Texto ou corpo da postagem")
    parser.add_argument("--file", type=str, help="Caminho de arquivo de texto (.txt ou .md) para usar como conteudo")
    parser.add_argument("--labels", "--tags", "--hashtags", dest="labels", type=str, help="Marcadores / Tags separados por virgula ou espaco")
    parser.add_argument("--media", nargs="+", help="Caminhos de imagens")
    parser.add_argument("--draft", action="store_true", help="Salva como rascunho sem publicar")
    parser.add_argument("--visible", action="store_true", help="Executa o navegador visivelmente (debug)")
    parser.add_argument("--history", action="store_true", help="Exibe o historico de postagens do Blogspot")

    args = parser.parse_args()

    if args.login:
        interactive_login()
        return

    if args.history:
        show_history()
        return

    content = args.content or ""
    if args.file and Path(args.file).exists():
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

    if content or args.title:
        title = args.title or "Atualizacao de Desenvolvimento"
        post_blogspot(
            title=title,
            content=content,
            labels=args.labels,
            media_paths=args.media,
            draft=args.draft,
            headless=not args.visible
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
