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
SESSION_FILE = SESSIONS_DIR / "session_tiktok.json"
HISTORY_FILE = SESSIONS_DIR / "tiktok_posts_history.json"

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def record_post_history(text: str, video_path: str, success: bool, details: str = ""):
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": "TikTok",
        "text": text,
        "video": video_path,
        "success": success,
        "details": details
    }
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def launch_browser(p, headless: bool = False):
    common_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars",
        "--disable-dev-shm-usage"
    ]
    try:
        return p.chromium.launch(
            channel="chrome",
            headless=headless,
            args=common_args
        )
    except Exception:
        return p.chromium.launch(
            headless=headless,
            args=common_args
        )

def interactive_login():
    """Abre o navegador visível para autenticar na conta do TikTok e salva a sessão."""
    print("=" * 72)
    print("  [SOCIAL AUTO-POST] Configuração de Login - TIKTOK")
    print("=" * 72)
    print("1. O navegador será aberto na página de login do TikTok.")
    print("2. Faça o login na sua conta do TikTok (@al3x_d3v357).")
    print("3. Quando já estiver logado e na página inicial ou no TikTok Studio,")
    print("   volte aqui neste terminal e pressione a tecla ENTER para salvar a sessão.")
    print("=" * 72)

    with sync_playwright() as p:
        browser = launch_browser(p, headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        log("Navegando para https://www.tiktok.com/login...")
        page.goto("https://www.tiktok.com/login")

        print("\n>>> Aguardando você fazer login no navegador aberto... <<<")
        input(">>> Pressione ENTER AQUI após concluir o login e estar no TikTok... <<<\n")

        context.storage_state(path=str(SESSION_FILE))
        log(f"SUCESSO! Sessão autenticada do TikTok salva em: {SESSION_FILE}")
        browser.close()

def post_tiktok(text: str, video_path: str, headless: bool = True) -> bool:
    """Publica um vídeo no TikTok com legenda e hashtags."""
    if not SESSION_FILE.exists():
        log("ERRO: Nenhuma sessão encontrada para o TikTok!")
        log("Execute primeiro o comando de login: python tiktok_poster.py --login")
        return False

    v_path = Path(video_path)
    if not v_path.exists():
        log(f"ERRO: Arquivo de vídeo não encontrado: {video_path}")
        return False

    abs_video_path = str(v_path.resolve())
    log(f"Iniciando publicação no TikTok... (Headless: {headless})")
    log(f"Legenda: {text[:80]}..." if len(text) > 80 else f"Legenda: {text}")
    log(f"Arquivo de vídeo: {abs_video_path}")

    with sync_playwright() as p:
        browser = launch_browser(p, headless=headless)
        context = browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            target_url = "https://www.tiktok.com/tiktokstudio/upload"
            log(f"Acessando painel de upload: {target_url}...")
            page.goto(target_url, timeout=60000)
            page.wait_for_timeout(4000)

            if "login" in page.url.lower():
                log("ALERTA: Sessão expirada ou não autenticada no TikTok.")
                record_post_history(text, abs_video_path, False, "Sessao expirada")
                browser.close()
                return False

            # Envia o vídeo
            file_input = page.locator('input[type="file"]').first
            log("Enviando arquivo de vídeo...")
            file_input.set_input_files(abs_video_path)
            page.wait_for_timeout(6000)

            # Fechar possíveis popups de tutorial / onboarding (ex: 'Entendi')
            entendi_btn = page.locator('button:has-text("Entendi"), button:has-text("Got it")')
            if entendi_btn.count():
                for i in range(entendi_btn.count()):
                    try:
                        if entendi_btn.nth(i).is_visible():
                            entendi_btn.nth(i).click()
                            page.wait_for_timeout(500)
                    except Exception:
                        pass

            # Rolar ao topo e preencher legenda
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)

            caption_box = page.locator('div[contenteditable="true"], .public-DraftEditor-content, textarea, div[role="combobox"]').first
            if caption_box.is_visible(timeout=5000):
                log("Preenchendo legenda e hashtags...")
                caption_box.click(force=True)
                page.wait_for_timeout(200)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.wait_for_timeout(200)
                for line in text.split("\n"):
                    page.keyboard.type(line, delay=8)
                    page.keyboard.press("Shift+Enter")
                    page.wait_for_timeout(100)

            # Rolar para baixo até o botão de publicação
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

            publish_btn = page.locator('button:has-text("Publicar"), button:has-text("Post")').first
            for _ in range(25):
                if not publish_btn.get_attribute("disabled"):
                    log("Vídeo processado e pronto para publicação!")
                    break
                page.wait_for_timeout(2000)

            log("Clicando no botão de publicação...")
            publish_btn.click()
            page.wait_for_timeout(2500)

            # Verifica se apareceu popup de confirmação (ex: "Publicar agora")
            pub_agora_btn = page.locator('button:has-text("Publicar agora")').first
            if pub_agora_btn.is_visible(timeout=3000):
                log("Confirmando publicação imediata...")
                pub_agora_btn.click()
                page.wait_for_timeout(6000)

            log("SUCESSO: Post publicado no TikTok!")
            record_post_history(text, abs_video_path, True)

            # Garantir visibilidade pública
            try:
                page.goto('https://www.tiktok.com/tiktokstudio/content', timeout=60000)
                page.wait_for_timeout(4000)
                priv_dropdown = page.locator('div:has-text("Somente"), span:has-text("Somente"), button:has-text("Somente")').first
                if priv_dropdown.is_visible(timeout=3000):
                    priv_dropdown.click()
                    page.wait_for_timeout(800)
                    todos_opt = page.locator('div[role="option"]:has-text("Todos"), li:has-text("Todos"), span:has-text("Todos")').first
                    if todos_opt.is_visible(timeout=2000):
                        todos_opt.click()
                        page.wait_for_timeout(1500)
            except Exception:
                pass

            browser.close()
            return True

        except Exception as e:
            err_msg = str(e)
            log(f"FALHA ao publicar no TikTok: {err_msg}")
            screenshot_path = str(SESSIONS_DIR / "tiktok_post_error.png")
            try:
                page.screenshot(path=screenshot_path)
            except Exception:
                pass
            record_post_history(text, abs_video_path, False, err_msg)
            browser.close()
            return False

def show_history():
    if not HISTORY_FILE.exists():
        print("Nenhum histórico encontrado para o TikTok.")
        return
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)
    print("\n--- HISTÓRICO DE POSTAGENS NO TIKTOK ---")
    for p in posts[-5:]:
        status = "SUCESSO" if p.get("success") else "FALHA"
        print(f"[{p.get('timestamp')}] {status}: {p.get('video')} | {p.get('text')[:50]}...")
    print("----------------------------------------\n")

def main():
    parser = argparse.ArgumentParser(description="TikTok Auto-Poster")
    parser.add_argument("--login", action="store_true", help="Login interativo no TikTok para salvar sessão")
    parser.add_argument("--video", type=str, help="Caminho do arquivo de vídeo (.mp4, .mov, etc.)")
    parser.add_argument("--post", "--caption", dest="post", type=str, help="Texto da legenda (SEM emojis)")
    parser.add_argument("--hashtags", type=str, default="", help="Hashtags separadas por espaço (ex: #gamedev #godot #b3d)")
    parser.add_argument("--visible", action="store_true", help="Executa com navegador visível")
    parser.add_argument("--history", action="store_true", help="Mostra histórico de postagens")

    args = parser.parse_args()

    if args.login:
        interactive_login()
    elif args.history:
        show_history()
    elif args.video:
        text = args.post or ""
        if args.hashtags:
            text = f"{text}\n\n{args.hashtags}".strip() if text else args.hashtags.strip()
        post_tiktok(text, args.video, headless=not args.visible)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
