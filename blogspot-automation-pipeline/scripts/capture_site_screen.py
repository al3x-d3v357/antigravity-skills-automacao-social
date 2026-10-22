"""
Captura print/screenshot em alta resolucao de sites ou ferramentas web
para ilustrar artigos e postagens no Blogspot de forma 100% autonoma.
"""
import sys
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def capture_screenshot(url: str, output_path: str, width: int = 1920, height: int = 1080) -> bool:
    print(f"Iniciando captura de tela de: {url}")
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": width, "height": height},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                locale="pt-BR"
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # Remove possiveis banners ou cookies flutuantes chatos se houver
            try:
                page.evaluate("""() => {
                    const selectors = ['#onetrust-banner-sdk', '.cookie-banner', '[aria-label*="cookie"]', '.modal-backdrop'];
                    selectors.forEach(sel => {
                        const el = document.querySelector(sel);
                        if (el) el.remove();
                    });
                }""")
            except Exception:
                pass
                
            page.screenshot(path=str(out), full_page=False)
            print(f"SUCESSO: Screenshot salva em: {out}")
            browser.close()
            return True
        except Exception as e:
            print(f"ERRO ao capturar screenshot: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Capturador de Prints de Sites para o Blogspot")
    parser.add_argument("--url", type=str, required=True, help="URL da pagina para capturar")
    parser.add_argument("--output", type=str, required=True, help="Caminho onde salvar o print (.png)")
    parser.add_argument("--width", type=int, default=1920, help="Largura da viewport (Padrao: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Altura da viewport (Padrao: 1080)")
    
    args = parser.parse_args()
    capture_screenshot(args.url, args.output, args.width, args.height)

if __name__ == "__main__":
    main()
