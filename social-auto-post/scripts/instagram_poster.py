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
SESSION_FILE = SESSIONS_DIR / "session_instagram.json"
HISTORY_FILE = SESSIONS_DIR / "instagram_posts_history.json"

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
        "platform": "Instagram",
        "text": text,
        "media": media_paths,
        "success": success,
        "details": details
    }
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def interactive_login():
    """Abre o navegador visível para autenticar na conta do Instagram e salva a sessão."""
    print("=" * 72)
    print("  [SOCIAL AUTO-POST] Configuração de Login - INSTAGRAM")
    print("=" * 72)
    print("1. O navegador será aberto na página de login do Instagram.")
    print("2. Faça o login com sua conta do Instagram (@al3x_d3v357).")
    print("3. Quando já estiver logado e no Feed do Instagram,")
    print("   volte aqui neste terminal e pressione a tecla ENTER para salvar a sessão.")
    print("=" * 72)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        log("Navegando para https://www.instagram.com/accounts/login/...")
        page.goto("https://www.instagram.com/accounts/login/")

        print("\n>>> Aguardando você fazer login no navegador aberto... <<<")
        input(">>> Pressione ENTER AQUI após concluir o login e estar no Feed do Instagram... <<<\n")

        # Salva o estado da sessão (cookies, tokens e storage)
        context.storage_state(path=str(SESSION_FILE))
        log(f"SUCESSO! Credenciais e sessão do Instagram salvas em: {SESSION_FILE}")
        browser.close()

def post_instagram(text: str, media_paths: Optional[List[str]] = None, headless: bool = True) -> bool:
    """Publica um post no Instagram Feed com mídia e legenda."""
    # Se ainda não houver sessão exclusiva do Instagram, mas houver do Threads (mesmo ecossistema Meta)
    active_session = SESSION_FILE
    threads_session = SESSIONS_DIR / "session_threads.json"
    if not active_session.exists() and threads_session.exists():
        log("Sessão direta do Instagram não encontrada, verificando compatibilidade...")
        active_session = threads_session

    if not active_session.exists():
        log("ERRO: Nenhuma sessão encontrada para o Instagram!")
        log("Execute primeiro o comando de login: python instagram_poster.py --login")
        return False

    media_paths = media_paths or []
    valid_medias = []
    for m in media_paths:
        p = Path(m)
        if p.exists():
            valid_medias.append(str(p.resolve()))
        else:
            log(f"AVISO: Arquivo de mídia não encontrado: {m}")

    if not valid_medias:
        log("ERRO: O Instagram requer pelo menos uma imagem ou vídeo para publicar!")
        return False

    log(f"Iniciando publicação no Instagram... (Headless: {headless})")
    log(f"Legenda: {text[:80]}..." if len(text) > 80 else f"Legenda: {text}")
    log(f"Mídias ({len(valid_medias)}): {valid_medias}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            storage_state=str(active_session),
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto("https://www.instagram.com/", timeout=45000)
            page.wait_for_timeout(3000)

            # Verifica se caiu em tela de login
            if "accounts/login" in page.url:
                log("ALERTA: Sessão expirada ou redirecionada para tela de login.")
                record_post_history(text, valid_medias, False, "Sessao expirada")
                browser.close()
                return False

            # Clica no botão "Criar" / "Novo Post" (SVG ou texto 'Criar'/'Create')
            create_btn = page.locator('svg[aria-label="Nova publicação"], svg[aria-label="New post"], a[href="#"][role="link"]:has-text("Criar"), span:has-text("Criar")').first
            if not create_btn.is_visible(timeout=5000):
                create_btn = page.locator('svg[aria-label="Criar"], svg[aria-label="Create"]').first
            
            create_btn.click()
            page.wait_for_timeout(2000)

            # Upload do arquivo via input[type="file"]
            file_input = page.locator('input[type="file"]')
            file_input.set_input_files(valid_medias[0])
            page.wait_for_timeout(4000)

            # Seleciona proporção Original / 16:9 para preservar resolução total (sem cortar para 1:1)
            try:
                crop_btn = page.locator('button:has(svg[aria-label="Selecionar corte"]), button:has(svg[aria-label="Select crop"]), svg[aria-label="Selecionar corte"], svg[aria-label="Select crop"]').first
                if crop_btn.is_visible(timeout=3000):
                    crop_btn.click()
                    page.wait_for_timeout(600)
                    orig_opt = page.locator('button:has-text("Original"), span:has-text("Original"), div[role="button"]:has-text("Original"), button:has-text("16:9"), span:has-text("16:9")').first
                    if orig_opt.is_visible(timeout=2000):
                        orig_opt.click()
                        page.wait_for_timeout(600)
            except Exception as crop_err:
                log(f"Aviso ajuste de corte: {crop_err}")

            # Avança pelas etapas (Corte -> Ajustes/Capa -> Legenda)
            for step in range(3):
                next_btn = page.locator('div[role="button"]:has-text("Avançar"), div[role="button"]:has-text("Next"), button:has-text("Avançar"), button:has-text("Next")').first
                if next_btn.is_visible(timeout=3000):
                    next_btn.click()
                    page.wait_for_timeout(2500)
                caption_area = page.locator('div[aria-label="Escreva uma legenda..."], div[aria-label="Write a caption..."], textarea[aria-label="Escreva uma legenda..."]').first
                if caption_area.is_visible(timeout=1500):
                    break

            # Preencher legenda
            caption_area = page.locator('div[aria-label="Escreva uma legenda..."], div[aria-label="Write a caption..."], textarea[aria-label="Escreva uma legenda..."]').first
            if caption_area.is_visible(timeout=5000):
                caption_area.click()
                caption_area.fill(text)
                page.wait_for_timeout(1000)

            # Botão Compartilhar / Share
            share_btn = page.locator('div[role="button"]:has-text("Compartilhar"), div[role="button"]:has-text("Share")').first
            share_btn.click()
            log("Botão de compartilhar clicado. Aguardando conclusão do envio...")

            # Aguardar confirmação "Sua publicação foi compartilhada"
            page.wait_for_selector('text="Sua publicação foi compartilhada", text="Your post has been shared"', timeout=35000)
            log("SUCESSO: Post publicado com sucesso no Instagram!")
            record_post_history(text, valid_medias, True)
            browser.close()
            return True

        except Exception as e:
            err_msg = str(e)
            log(f"FALHA ao publicar no Instagram: {err_msg}")
            screenshot_path = str(SESSIONS_DIR / "instagram_post_error.png")
            page.screenshot(path=screenshot_path)
            record_post_history(text, valid_medias, False, err_msg)
            browser.close()
            return False

def show_history():
    if not HISTORY_FILE.exists():
        print("Nenhum histórico encontrado para o Instagram.")
        return
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)
    print("\n--- HISTÓRICO DE POSTAGENS NO INSTAGRAM ---")
    for p in posts[-5:]:
        status = "SUCESSO" if p.get("success") else "FALHA"
        print(f"[{p.get('timestamp')}] {status}: {p.get('text')[:60]}...")
    print("-------------------------------------------\n")

def main():
    parser = argparse.ArgumentParser(description="Instagram Auto-Poster")
    parser.add_argument("--login", action="store_true", help="Login interativo no Instagram")
    parser.add_argument("--post", type=str, help="Texto da legenda")
    parser.add_argument("--hashtags", type=str, default="", help="Hashtags separadas por espaço")
    parser.add_argument("--media", nargs="+", help="Arquivos de imagem ou vídeo")
    parser.add_argument("--visible", action="store_true", help="Executa com navegador visível")
    parser.add_argument("--history", action="store_true", help="Histórico de postagens")

    args = parser.parse_args()

    if args.login:
        interactive_login()
    elif args.history:
        show_history()
    elif args.post:
        full_text = args.post
        if args.hashtags:
            full_text = f"{full_text}\n\n{args.hashtags}".strip()
        post_instagram(full_text, args.media, headless=not args.visible)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
