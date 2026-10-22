import sys
import argparse
import threads_poster
import instagram_poster
import x_poster
import tiktok_poster

def main():
    parser = argparse.ArgumentParser(description="Social Auto-Post - Publicador Multi-Plataforma (Threads, Instagram, X, TikTok)")
    parser.add_argument("--platform", choices=["threads", "instagram", "insta", "x", "twitter", "tiktok"], default="threads", help="Plataforma de destino: threads, instagram, x ou tiktok (Padrão: threads)")
    parser.add_argument("--login", action="store_true", help="Abre o navegador para autenticar a plataforma escolhida")
    parser.add_argument("--post", type=str, help="Texto ou legenda da postagem (SEM emojis)")
    parser.add_argument("--hashtags", type=str, default="", help="Hashtags contextuais separadas por espaço")
    parser.add_argument("--media", nargs="+", help="Caminhos de imagens ou vídeos renderizados")
    parser.add_argument("--video", type=str, help="Caminho do arquivo de vídeo (específico para TikTok)")
    parser.add_argument("--visible", action="store_true", help="Executa o navegador de forma visível")
    parser.add_argument("--history", action="store_true", help="Mostra histórico da plataforma")

    args = parser.parse_args()
    platform = args.platform.lower()

    if platform in ["instagram", "insta"]:
        if args.login:
            instagram_poster.interactive_login()
        elif args.history:
            instagram_poster.show_history()
        elif args.post:
            full_text = args.post
            if args.hashtags:
                full_text = f"{full_text}\n\n{args.hashtags}".strip()
            instagram_poster.post_instagram(full_text, args.media, headless=not args.visible)
        else:
            parser.print_help()

    elif platform in ["x", "twitter"]:
        if args.login:
            x_poster.interactive_login()
        elif args.history:
            x_poster.show_history()
        elif args.post:
            full_text = args.post
            if args.hashtags:
                full_text = f"{full_text}\n\n{args.hashtags}".strip()
            x_poster.post_x(full_text, args.media, headless=not args.visible)
        else:
            parser.print_help()

    elif platform == "tiktok":
        if args.login:
            tiktok_poster.interactive_login()
        elif args.history:
            tiktok_poster.show_history()
        elif args.post or args.video or (args.media and len(args.media) > 0):
            video_file = args.video if args.video else (args.media[0] if args.media else None)
            if not video_file:
                print("ERRO: O TikTok requer um arquivo de vídeo (--video ou --media).")
                return
            full_text = args.post or ""
            if args.hashtags:
                full_text = f"{full_text}\n\n{args.hashtags}".strip() if full_text else args.hashtags.strip()
            tiktok_poster.post_tiktok(full_text, video_file, headless=not args.visible)
        else:
            parser.print_help()

    else:
        # Padrão Threads (Instagram)
        if args.login:
            threads_poster.interactive_login()
        elif args.history:
            threads_poster.show_history()
        elif args.post:
            full_text = args.post
            if args.hashtags:
                full_text = f"{full_text}\n\n{args.hashtags}".strip()
            threads_poster.post_thread(full_text, args.media, headless=not args.visible)
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
