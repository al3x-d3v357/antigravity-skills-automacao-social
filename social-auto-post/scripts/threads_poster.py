import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SESSIONS_DIR = Path(os.path.expanduser("~/.social_sessions"))
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = SESSIONS_DIR / "session_threads.json"
HISTORY_FILE = SESSIONS_DIR / "threads_posts_history.json"

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def record_post_history(text: str, media_paths: List[str], success: bool, details: str = ""):
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": "Threads (Meta / Instagram)",
        "text": text,
        "media": media_paths,
        "success": success,
        "details": details
    }
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def interactive_login():
    """Abre o navegador visível para o usuário autenticar na conta do Threads / Instagram e salva a sessão."""
    print("=" * 72)
    print("  [SOCIAL AUTO-POST] Configuração de Login - THREADS (Instagram)")
    print("=" * 72)
    print("1. O navegador será aberto na página de login do Threads (threads.net).")
    print("2. Faça o login com sua conta do Instagram / Threads normalmente.")
    print("3. Quando já estiver logado e na página principal do feed do Threads,")
    print("   volte aqui neste terminal e pressione a tecla ENTER para salvar a sessão.")
    print("=" * 72)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        log("Navegando para https://www.threads.net/login...")
        page.goto("https://www.threads.net/login")

        print("\n>>> Aguardando você fazer login no navegador aberto... <<<")
        input(">>> Pressione ENTER AQUI após concluir o login e estar no Feed do Threads... <<<\n")

        # Salva o estado da sessão (cookies, tokens e storage)
        context.storage_state(path=str(SESSION_FILE))
        log(f"SUCESSO! Credenciais e sessão do Threads salvas com segurança em: {SESSION_FILE}")
        browser.close()

def post_thread(text: str, media_paths: Optional[List[str]] = None, headless: bool = True) -> bool:
    """Publica um post no Threads com texto e mídias opcionais em segundo plano."""
    if not SESSION_FILE.exists():
        log("ERRO: Nenhuma sessão encontrada para o Threads!")
        log("Execute primeiro o comando de login: python threads_poster.py --login")
        return False

    media_paths = media_paths or []
    valid_medias = []
    for m in media_paths:
        p = Path(m)
        if p.exists():
            valid_medias.append(str(p.resolve()))
        else:
            log(f"AVISO: Arquivo de mídia não encontrado: {m}")

    log(f"Iniciando publicação no Threads... (Headless: {headless})")
    log(f"Texto do post: {text[:80]}..." if len(text) > 80 else f"Texto do post: {text}")
    if valid_medias:
        log(f"Mídias anexadas ({len(valid_medias)}): {valid_medias}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            storage_state=str(SESSION_FILE),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        try:
            log("Acessando https://www.threads.net...")
            page.goto("https://www.threads.net", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3500)

            # Verifica se foi redirecionado para a página de login
            if "login" in page.url:
                log("ERRO: A sessão expirou ou não está mais válida no Threads. Execute 'python threads_poster.py --login' novamente.")
                record_post_history(text, valid_medias, False, "Sessão expirada")
                browser.close()
                return False

            # Localiza o gatilho para abrir o modal de nova thread
            # No Threads Web: botão Criar / Start a thread / Iniciar uma thread
            create_btn = None
            selectors = [
                '[aria-label="New thread"]',
                '[aria-label="Nova thread"]',
                'svg[aria-label="New thread"]',
                'svg[aria-label="Nova thread"]',
                'svg[aria-label="Criar"]',
                'svg[aria-label="Create"]',
                '[aria-label="Criar"]',
                '[aria-label="Create"]',
                'div[role="button"]:has-text("Iniciar uma thread")',
                'div[role="button"]:has-text("Start a thread")',
                'span:has-text("Iniciar uma thread")',
                'span:has-text("Start a thread")'
            ]
            for sel in selectors:
                loc = page.locator(sel).first
                if loc.is_visible():
                    create_btn = loc
                    break

            if create_btn:
                log("Abrindo formulário de criação de thread...")
                create_btn.click()
                page.wait_for_timeout(1000)
            else:
                log("Tentando focar diretamente no editor...")

            # Localiza o editor ativo (o último, dentro do popup de criação)
            editors = page.locator('div[contenteditable="true"]').all()
            if not editors:
                log("ERRO: Não foi possível localizar a caixa de texto do Threads.")
                record_post_history(text, valid_medias, False, "Editor não encontrado")
                browser.close()
                return False

            active_editor = editors[-1]
            log("Inserindo o texto e legendas...")
            active_editor.click()
            page.wait_for_timeout(300)
            page.keyboard.insert_text(text)
            page.wait_for_timeout(1000)

            # Anexa arquivos de mídia se houver
            if valid_medias:
                log(f"Fazendo upload de {len(valid_medias)} arquivo(s) de mídia...")
                file_inputs = page.locator('input[type="file"]').all()
                if not file_inputs:
                    attach_icon = page.locator('svg[aria-label="Anexar mídia"], svg[aria-label="Attach media"], [aria-label="Anexar mídia"], [aria-label="Attach media"]').first
                    if attach_icon.is_visible():
                        attach_icon.click()
                        page.wait_for_timeout(500)
                    file_inputs = page.locator('input[type="file"]').all()

                if file_inputs:
                    file_inputs[-1].set_input_files(valid_medias)
                    log("Aguardando upload e renderização da mídia pelo Threads...")
                    page.wait_for_timeout(4000)

            # Aguarda o botão Post do popup estar disponível e habilitado
            is_video = any(m.lower().endswith(('.mp4', '.mov', '.webm', '.mkv')) for m in valid_medias)
            wait_sec = 60 if is_video else 20
            log("Aguardando liberação do botão Postar do popup...")

            for _ in range(wait_sec):
                btn_state = page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('div[role="button"], button')).filter(e => {
                        const t = (e.innerText || '').trim();
                        return (t === 'Post' || t === 'Postar');
                    });
                    if (btns.length === 0) return null;
                    const target = btns[btns.length - 1];
                    return {
                        disabled: target.getAttribute('aria-disabled'),
                        y: target.getBoundingClientRect().y
                    };
                }""")
                if btn_state and btn_state.get("disabled") != "true" and btn_state.get("y", 0) > 200:
                    break
                page.wait_for_timeout(1000)

            log("Enviando post para o Threads...")
            clicked = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('div[role="button"], button')).filter(e => {
                    const t = (e.innerText || '').trim();
                    return (t === 'Post' || t === 'Postar');
                });
                if (btns.length > 0) {
                    btns[btns.length - 1].click();
                    return true;
                }
                return false;
            }""")

            if not clicked:
                log("ERRO: Não foi possível clicar no botão Postar do popup!")
                record_post_history(text, valid_medias, False, "Botão Postar não clicado")
                browser.close()
                return False

            # Monitora o processamento do toast ('Posting...' até 'Posted' ou sumir)
            log("Aguardando processamento e confirmação dos servidores da Meta...")
            for sec in range(90):
                page.wait_for_timeout(1000)
                status = page.evaluate("""() => {
                    const body = document.body.innerText;
                    const hasPosting = body.includes('Posting...') || body.includes('Publicando...');
                    const hasPosted = body.includes('Posted') || body.includes('Publicado') || body.includes('View');
                    return { posting: hasPosting, posted: hasPosted };
                }""")
                if status.get("posted"):
                    log("Confirmação recebida: 'Posted'!")
                    break
                if not status.get("posting") and sec > 8:
                    break

            page.wait_for_timeout(3000)
            log("SUCESSO: Post publicado com êxito no Threads!")
            record_post_history(text, valid_medias, True, "Publicado com sucesso no Threads")

            # Salva o estado atualizado da sessão
            context.storage_state(path=str(SESSION_FILE))
            browser.close()
            return True

        except Exception as e:
            log(f"ERRO durante a publicação no Threads: {str(e)}")
            record_post_history(text, valid_medias, False, str(e))
            try:
                page.screenshot(path=str(SESSIONS_DIR / "threads_post_error.png"))
                log(f"Screenshot do erro salvo em: {SESSIONS_DIR / 'threads_post_error.png'}")
            except Exception:
                pass
            browser.close()
            return False

def main():
    parser = argparse.ArgumentParser(description="Social Auto-Post - Automação de Postagens no THREADS (Instagram)")
    parser.add_argument("--login", action="store_true", help="Abre o navegador para autenticar e salvar sua conta do Threads")
    parser.add_argument("--post", type=str, help="Texto ou legenda da postagem")
    parser.add_argument("--hashtags", type=str, default="", help="Hashtags adicionais separadas por espaço (ex: '#b3d #blender')")
    parser.add_argument("--media", nargs="+", help="Caminhos de imagens ou vídeos para anexar ao post")
    parser.add_argument("--visible", action="store_true", help="Roda o navegador visível para acompanhar")
    parser.add_argument("--history", action="store_true", help="Exibe o histórico de postagens realizadas no Threads")

    args = parser.parse_args()

    if args.login:
        interactive_login()
        return

    if args.history:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                hist = json.load(f)
            print(f"\n--- HISTÓRICO DE POSTAGENS THREADS ({len(hist)}) ---")
            for h in hist[-5:]:
                print(f"[{h['timestamp']}] Sucesso: {h['success']} | Mídia: {len(h.get('media', []))} arquivos")
                print(f"Texto: {h['text'][:100]}...\n")
        else:
            print("Nenhum histórico encontrado para o Threads.")
        return

    if args.post:
        full_text = args.post
        if args.hashtags:
            full_text = f"{full_text}\n\n{args.hashtags}".strip()

        success = post_thread(
            text=full_text,
            media_paths=args.media,
            headless=not args.visible
        )
        if success:
            print("\n[OK] Publicação realizada com sucesso no Threads!")
        else:
            print("\n[FALHA] Não foi possível publicar no Threads. Verifique o log acima.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
