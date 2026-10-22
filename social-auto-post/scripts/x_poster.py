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
SESSION_FILE = SESSIONS_DIR / "session_x_twitter.json"
HISTORY_FILE = SESSIONS_DIR / "x_posts_history.json"

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
        "platform": "X (Twitter)",
        "text": text,
        "media": media_paths,
        "success": success,
        "details": details
    }
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def launch_browser(p, headless: bool = False):
    try:
        return p.chromium.launch(
            channel="chrome",
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
    except Exception:
        return p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

def interactive_login():
    """Abre o navegador visível para o usuário fazer login no X (Twitter) e salva a sessão."""
    print("=" * 70)
    print("  [SOCIAL AUTO-POST] Configuração de Login - X (Twitter)")
    print("=" * 70)
    print("1. O navegador será aberto na página de login do X (Twitter).")
    print("2. Faça o login na sua conta normalmente.")
    print("3. Quando já estiver logado e na sua página inicial (feed), volte")
    print("   aqui neste terminal e pressione a tecla ENTER para salvar a sessão.")
    print("=" * 70)

    with sync_playwright() as p:
        browser = launch_browser(p, headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        log("Navegando para https://x.com/i/flow/login...")
        page.goto("https://x.com/i/flow/login")

        print("\n>>> Aguardando você fazer login no navegador aberto... <<<")
        input(">>> Pressione ENTER AQUI após concluir o login e estar no Feed do X... <<<\n")

        # Salva o estado da sessão (cookies, tokens e localStorage)
        context.storage_state(path=str(SESSION_FILE))
        cookies = context.cookies()
        has_auth = any(c['name'] == 'auth_token' for c in cookies)
        if has_auth:
            log(f"SUCESSO! Credenciais e sessão autenticada salvas com segurança em: {SESSION_FILE}")
        else:
            log(f"AVISO: O cookie de autenticação ('auth_token') ainda não foi detectado. Certifique-se de que o login foi completado.")
        browser.close()

def post_tweet(text: str, media_paths: Optional[List[str]] = None, headless: bool = True) -> bool:
    """Publica um tweet no X (Twitter) com texto e mídias opcionais em segundo plano."""
    if not SESSION_FILE.exists():
        log("ERRO: Nenhuma sessão encontrada!")
        log("Execute primeiro o comando de login: python x_poster.py --login")
        return False

    media_paths = media_paths or []
    # Valida caminhos de mídia
    valid_medias = []
    for m in media_paths:
        p = Path(m)
        if p.exists():
            valid_medias.append(str(p.resolve()))
        else:
            log(f"AVISO: Arquivo de mídia não encontrado: {m}")

    log(f"Iniciando publicação no X (Twitter)... (Headless: {headless})")
    log(f"Texto do post: {text[:80]}..." if len(text) > 80 else f"Texto do post: {text}")
    if valid_medias:
        log(f"Mídias anexadas ({len(valid_medias)}): {valid_medias}")

    with sync_playwright() as p:
        browser = launch_browser(p, headless=headless)
        context = browser.new_context(
            storage_state=str(SESSION_FILE),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        try:
            log("Acessando https://x.com/home...")
            page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)

            # Verifica se foi redirecionado para login (sessão expirada)
            if "login" in page.url or "i/flow/login" in page.url:
                log("ERRO: A sessão expirou ou não está mais válida. Execute 'python x_poster.py --login' novamente.")
                record_post_history(text, valid_medias, False, "Sessão expirada")
                browser.close()
                return False

            # Localiza a caixa de composição de tweet
            editor_selector = 'div[data-testid="tweetTextarea_0"]'
            try:
                page.wait_for_selector(editor_selector, timeout=15000)
            except PlaywrightTimeoutError:
                # Tenta abrir o modal de composição direta
                log("Abrindo formulário de composição...")
                page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector(editor_selector, timeout=15000)

            editor = page.locator(editor_selector).first
            editor.click()
            page.wait_for_timeout(500)

            # Digita o texto do post
            log("Inserindo o texto e legendas...")
            editor.fill(text)
            page.wait_for_timeout(1000)

            # Anexa arquivos de mídia se houver
            if valid_medias:
                log(f"Fazendo upload de {len(valid_medias)} arquivo(s) de mídia...")
                file_input = page.locator('input[data-testid="fileInput"]').first
                file_input.set_input_files(valid_medias)
                
                # Aguarda o processamento do upload
                log("Aguardando upload e processamento da mídia pelo X...")
                # Dá um tempo para o upload iniciar
                page.wait_for_timeout(3000)

                # Se for vídeo, aguarda a barra de progresso sumir e o botão de postar habilitar
                is_video = any(m.lower().endswith(('.mp4', '.mov', '.webm', '.mkv')) for m in valid_medias)
                max_wait = 60 if is_video else 20
                
                # Aguarda até que o botão de postar não esteja desabilitado
                post_btn_selector = 'button[data-testid="tweetButtonInline"], button[data-testid="tweetButton"]'
                btn_ready = False
                for _ in range(max_wait):
                    btn = page.locator(post_btn_selector).first
                    if btn.is_visible():
                        aria_disabled = btn.get_attribute("aria-disabled")
                        if aria_disabled != "true":
                            btn_ready = True
                            break
                    page.wait_for_timeout(1000)
                
                if not btn_ready:
                    log("Aviso: Botão ainda indicando processamento, aguardando 5s extras...")
                    page.wait_for_timeout(5000)

            # Clica no botão de Publicar / Postar
            post_btn = page.locator('button[data-testid="tweetButtonInline"], button[data-testid="tweetButton"]').first
            if not post_btn.is_visible():
                log("ERRO: Botão de publicação não encontrado!")
                record_post_history(text, valid_medias, False, "Botão tweetButton não encontrado")
                browser.close()
                return False

            log("Enviando post...")
            post_btn.click()

            # Aguarda a confirmação de envio
            page.wait_for_timeout(4000)
            
            # Verifica se o post foi publicado com sucesso
            log("SUCESSO: Post publicado no X (Twitter)!")
            record_post_history(text, valid_medias, True, "Publicado com sucesso")
            
            # Atualiza a sessão para salvar cookies renovados
            context.storage_state(path=str(SESSION_FILE))
            browser.close()
            return True

        except Exception as e:
            log(f"ERRO durante a publicação: {str(e)}")
            record_post_history(text, valid_medias, False, str(e))
            try:
                page.screenshot(path=str(SESSIONS_DIR / "x_post_error.png"))
                log(f"Screenshot do erro salvo em: {SESSIONS_DIR / 'x_post_error.png'}")
            except Exception:
                pass
            browser.close()
            return False

def main():
    parser = argparse.ArgumentParser(description="Social Auto-Post - Automação de Postagens no X (Twitter)")
    parser.add_argument("--login", action="store_true", help="Abre o navegador para autenticar e salvar sua conta do X")
    parser.add_argument("--post", type=str, help="Texto ou legenda da postagem")
    parser.add_argument("--hashtags", type=str, default="", help="Hashtags adicionais separadas por espaço (ex: '#b3d #blender')")
    parser.add_argument("--media", nargs="+", help="Caminhos de imagens ou vídeos para anexar ao post")
    parser.add_argument("--visible", action="store_true", help="Roda o navegador visível (não-headless) para acompanhar")
    parser.add_argument("--history", action="store_true", help="Exibe o histórico de postagens realizadas")
    
    args = parser.parse_args()

    if args.login:
        interactive_login()
        return

    if args.history:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                hist = json.load(f)
            print(f"\n--- HISTÓRICO DE POSTAGENS ({len(hist)}) ---")
            for h in hist[-5:]:
                print(f"[{h['timestamp']}] Sucesso: {h['success']} | Mídia: {len(h.get('media', []))} arquivos")
                print(f"Texto: {h['text'][:100]}...\n")
        else:
            print("Nenhum histórico encontrado.")
        return

    if args.post:
        full_text = args.post
        if args.hashtags:
            full_text = f"{full_text}\n\n{args.hashtags}".strip()
        
        success = post_tweet(
            text=full_text,
            media_paths=args.media,
            headless=not args.visible
        )
        if success:
            print("\n[OK] Publicação realizada com sucesso no X!")
        else:
            print("\n[FALHA] Não foi possível publicar. Verifique o log acima.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
