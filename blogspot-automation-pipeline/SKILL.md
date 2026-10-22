---
name: blogspot-automation-pipeline
description: >-
  Pipeline autônomo para publicação, formatação e gestão de artigos técnicos e tutoriais de Arte 3D/IA no Blogspot (Blogger). Localiza e anexa renders 3D existentes de D:\GitHub\arts3d, captura prints automáticos de ferramentas/sites web via Playwright e formata conteúdos de alta retenção com ZERO emojis.
---

# Blogspot Automation Pipeline - Artigos Técnicos & Arte 3D

Esta skill automatiza a esteira completa de criação, curadoria visual e publicação de artigos no blog **Arthur Connect** ([arthurconnetc7.blogspot.com](https://arthurconnetc7.blogspot.com/)) de forma autônoma e em segundo plano via Playwright.

---

## 🎯 Diretrizes Obrigatórias de Publicação

1. **PROIBIDO O USO DE EMOJIS (Regra Absoluta do Alex):**
   - Nunca insira nenhum tipo de emoji no título, subtítulos ou corpo do texto das postagens.
2. **Tom Autêntico de Desenvolvedor e Artista 3D:**
   - Linguagem prática, direta, focada em pipelines reais de produção, sem clichês corporativos ou frases de marketing vazias.
3. **Curadoria Visual Autônoma:**
   - **Renders de Projetos Autorais:** Buscar renders de alta qualidade diretamente em `D:\GitHub\arts3d` (`personagens`, `armas_e_props`, `veiculos`, `torres`).
   - **Prints de Sites e Ferramentas:** Capturar automaticamente telas e interfaces dos sites referenciados (ex: geradores de IA 3D, documentações, páginas de ferramentas).
4. **Formatação de Alta Retenção no Blogger:**
   - Títulos técnicos diretos.
   - Sumário e etapas numeradas claras (Conceito -> Geração -> Retopologia -> Blender/Engine).
   - Trechos de código ou blocos técnicos destacados.
   - Links diretos com `rel="noopener"` e `target="_blank"`.

---

## 🛠️ Scripts & Ferramentas Disponíveis

Localização dos scripts: `C:\Users\alexa\.gemini\config\skills\blogspot-automation-pipeline\scripts\`

### 1. Capturar Print de Site ou Ferramenta Web
Acessa a URL desejada em modo headless e gera screenshot limpo em alta resolução:
```powershell
python capture_site_screen.py --url "https://hy3d.tencent.ai/" --output "D:\GitHub\arts3d\scratch\tencent_hy3d_screen.png"
```

### 2. Buscar Renders em Projetos Autorais (arts3d)
Filtra imagens de showcase, preview e specs por termo ou categoria:
```powershell
# Buscar por personagem específico:
python fetch_project_render.py --query "noah"

# Listar melhores renders de armas e props:
python fetch_project_render.py --category "armas_e_props"
```

### 3. Publicar ou Salvar Rascunho no Blogspot
Publica artigos completos com suporte nativo a HTML rico, CodeMirror e marcadores:
```powershell
# Publicar post diretamente a partir de um arquivo HTML:
python blogspot_poster.py --title "Título do Artigo" --file "caminho\artigo.html" --labels "ia-3d, tutorial, blender3d"

# Salvar como rascunho para revisão posterior:
python blogspot_poster.py --title "Rascunho Técnico" --file "caminho\artigo.html" --draft
```

---

## 📋 Resumo das Regras

| Critério | Instrução Estrita |
| :--- | :--- |
| **Emojis** | **ZERO emojis.** Banido totalmente de todas as postagens. |
| **Imagens** | Renders de `D:\GitHub\arts3d` + prints capturados via `capture_site_screen.py`. |
| **Editor** | Inserção direta via CodeMirror nativo e salvamento com confirmação de modal. |
| **Sessão** | Salva em `~/.social_sessions/session_blogspot.json`. |
