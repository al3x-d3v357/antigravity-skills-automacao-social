---
name: social-auto-post
description: >-
  Automação inteligente e silenciosa para publicação de conteúdos, renders 3D, vídeos turntable e devlogs no Threads, Instagram, X e TikTok em segundo plano via Playwright. Segue diretrizes estritas do Alex: linguagem casual e autêntica, ZERO emojis nas legendas, postagem individual de cada projeto com hashtags contextuais e sem obrigatoriedade de música.
---

# Social Auto-Post - Automação de Publicações (Threads, Instagram, X & TikTok)

Esta skill automatiza a publicação de artes 3D, demonstrações técnicas, vídeos de gameplay/turntable e devlogs diretamente no **Threads**, **Instagram**, **X (Twitter)** e **TikTok** de forma autônoma e em segundo plano (**"por trás dos panos"**), operando através do Playwright integrado ao ecossistema do Alex.

---

## 🎯 Diretrizes Obrigatórias de Publicação do Alex

Sempre que o Alex solicitar a postagem de qualquer projeto, jogo ou modelo 3D, o assistente **DEVE** seguir rigorosamente as regras abaixo:

1. **PROIBIDO O USO DE EMOJIS (Regra Absoluta):**
   - Nunca insira nenhum tipo de emoji no texto ou na legenda das postagens (nada de emojis nas postagens). O Alex não gosta de emojis nas postagens do perfil.

2. **Linguagem Casual e Natural:**
   - Adotar tom direto de dev/artista 3D compartilhando o progresso real de trabalho.
   - Evitar tom corporativo, clichês de marketing ou frases artificiais de robô.

3. **Hashtags Contextuais:**
   - Usar hashtags que façam sentido estrito com o que está sendo postado:
     - Software utilizado: `#b3d #blender3d #unity3d #godotengine`
     - Categoria técnica: `#3dart #3dmodel #gamedev #indiedev #lowpoly #props3d`

4. **Tratamento de Mídia e Áudio:**
   - Priorizar imagem (`.png`, `.jpg`) ou vídeo (`.mp4`, `.mov`) renderizado do projeto.
   - **Não precisa colocar música:** postar imagem ou vídeo renderizado direto.

5. **Cadência de Postagem (Um de Cada Vez):**
   - Sempre disparar **uma postagem por vez**.

---

## 🚀 Como Funciona a Automação

1. **Sessão Persistente:**
   - As contas são autenticadas via `login.bat` ou `--login`.
   - As sessões ficam salvas em:
     - Threads: `~/.social_sessions/session_threads.json`
     - Instagram: `~/.social_sessions/session_instagram.json`
     - X (Twitter): `~/.social_sessions/session_x_twitter.json`
     - TikTok: `~/.social_sessions/session_tiktok.json`

2. **Publicação Autônoma (Headless / Silenciosa):**
   - O assistente executa o script em segundo plano.
   - Todas as postagens são salvas no arquivo de histórico correspondente (`threads_posts_history.json`, `instagram_posts_history.json`, `tiktok_posts_history.json`).

---

## 🛠️ Comandos de Execução

Scripts localizados em: `C:\Users\alexa\.gemini\config\skills\social-auto-post\scripts\`

### 1. Threads
```powershell
python threads_poster.py --post "Texto casual aqui" --hashtags "#b3d #blender3d #3dart" --media "D:\caminho\render.png"
```

### 2. Instagram
```powershell
python instagram_poster.py --post "Texto casual aqui" --hashtags "#b3d #blender3d #3dart" --media "D:\caminho\render.png"
```

### 3. TikTok
```powershell
# Autenticar / Conectar conta do TikTok:
python tiktok_poster.py --login

# Publicar clipe / vídeo de gameplay no TikTok:
python tiktok_poster.py --video "D:\caminho\gameplay.mp4" --post "Ajustando física dos projéteis na Godot" --hashtags "#gamedev #godot #indiedev"
```

---

## 📋 Resumo das Regras para o Assistente

| Critério | Instrução Estrita |
| :--- | :--- |
| **Emojis** | **ZERO emojis.** Banido totalmente das postagens. |
| **Tom** | Casual, autêntico, informal de desenvolvedor/artista 3D. |
| **Hashtags** | Pertinentes ao projeto, personagem e softwares usados. |
| **Música** | Não necessária. Postar imagem ou vídeo renderizado direto. |
| **Envio** | Um por vez, aguardando conclusão entre cada um. |
