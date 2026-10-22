---
name: ong-triagem-cadastro
description: >-
  Processamento inteligente e automatizado de triagem de cadastros da ONG One by One a partir de conversas do WhatsApp. Gera identificação, linha tabulada/CSV para Google Sheets, especificações técnicas de cadeira, mensagens operacionais, payload JSON para API e renomeação padronizada de documentos utilizando as categorias oficiais do sistema.
---

# ONG Triagem e Cadastro Skill (One by One)

Esta skill é ativada sempre que o usuário enviar o histórico/exportação de conversa do WhatsApp (ou arquivo `chat.md`) referente ao atendimento e solicitação de cadastro/cadeira de rodas para uma criança/assistido na **ONG One by One**.

---

## 🎯 Objetivo Principal

Analisar os dados da conversa, calcular a idade exata da criança, estruturar todas as informações para inserção na planilha de controle, gerar os textos operacionais de atendimento, formatar o JSON de integração da API e **renomear os arquivos da pasta local utilizando as categorias oficiais do sistema (sem incluir o nome da criança/família nos nomes dos arquivos)**.

---

## 📋 Estrutura da Resposta Padrão

Sempre que acionada, a IA deve estruturar o retorno rigorosamente nas seguintes seções:

### 1. Identificação Principal
* **Nome da Criança:** Nome completo da criança
* **Nome do Responsável:** Nome completo do responsável principal (mãe/pai/tutor)
* **Telefone / Contato:** Telefones informados no formato `+55 (XX) XXXXX-XXXX`
* **Nome para Salvar no Contato:** `[Nome do Responsável] - Resp: [Nome da Criança]` (ou `[Nome da Criança] mae [Nome da Mãe]`)

---

### 2. Encaminhamento na Planilha
* **Planilha / Aba Indicada:** Ex: `CONTROLE FILA ATUAL` (para cadeiras sob medida/carrinho postural) ou `SOMENTE CADASTRO ONG 2026` (cursos/projetos).
* **Status da Documentação:** `OK (Completo)` ou `Pendente (especificar pendências)`
* **Link da Planilha:** Link oficial da planilha Google Sheets.
* **Linha Horizontal para Copiar e Colar (com Tabulação):** Linha formatada com colunas separadas por `\t` pronta para colar diretamente na planilha.
* **Linha Pronta em CSV (Separada por Ponto e Vírgula):** Linha delimitada por `;`.

---

### 3. Especificações Técnicas da Cadeira
Extrair com precisão da prescrição médica (SARAH / Orthotec / etc.):
* **Modelo:** Ex: *Cadeira manual em X c/ Tilt (Carrinho Postural Cub com fechamento duplo em X)* ou *Não demandado (somente cursos/projetos)*
* **Largura do Assento (LA):** Ex: *35 cm* ou *Não disponível*
* **Profundidade (P):** Ex: *35 cm* ou *Não disponível*
* **Altura do Encosto (AE):** Ex: *50 cm* ou *Não disponível*
* **Tilt:** *Presente* / *Não informado* / *Não aplicável*
* **Medida do Quadril:** Informar ou *Não disponível*

---

### 4. Mensagens Operacionais

#### Mensagem Resumida do Caso (Direto ao Ponto):
Resumo clínico e administrativo conciso contendo:
* Idade da criança e diagnóstico/CIDs (ex: Paralisia Cerebral G80, TEA F84.0, etc.).
* Detalhes da prescrição técnica e modelo solicitado (ou demanda exclusiva por projetos/cursos).
* Status da documentação e validação de termos (ex: Termo de autorização de imagem, comprovantes).
* Justificativa da aba selecionada na planilha.

#### Mensagem para WhatsApp:
Mensagem empática e profissional para envio ao responsável:
> *"Oi! Aqui é o Alex da ONG One by One. 💙 Documentação revisada e nome incluído na fila/lista. O cadastro de [Nome da Criança] foi concluído com sucesso! Só aguardar o contato da nossa equipe."*

---

### 5. Tabela de Conferência e Renomeação de Documentos

> [!IMPORTANT]
> **REGRA FUNDAMENTAL DE NOMENCLATURA:** Utilizar **rigorosamente as categorias oficiais do sistema** (com sufixos numéricos `1`, `2`, etc. quando houver múltiplas páginas/arquivos), sem sufixar o nome da criança ou do responsável.
> A IA deve executar a renomeação direta dos arquivos locais na pasta.

#### Categorias Oficiais do Sistema:
| Categoria Oficial | Padrão do Nome do Arquivo | Exemplos / Variações |
| :--- | :--- | :--- |
| **Carta** | `Carta.jpeg` / `Carta.txt` | `Carta 1.jpeg`, `Carta 2.jpeg` |
| **Carteira de Vacinação** | `Carteira de Vacinação 1.jpeg` | `Carteira de Vacinação 2.jpeg`, `Carteira de Vacinação 3.jpeg` |
| **Carteirinha do SUS** | `Carteirinha do SUS.jpeg` (ou `.pdf`) | `Carteirinha do SUS 1.jpeg` |
| **Certidão de Nascimento** | `Certidão de Nascimento.jpeg` (ou `.pdf`) | `Certidão de Nascimento.pdf` |
| **CNH do responsável** | `CNH do responsável.jpeg` (ou `.pdf`) | `CNH do responsável 1.jpeg`, `CNH do responsável 2.jpeg` |
| **CPF do Assistido** | `CPF do Assistido.jpeg` (ou `.pdf`) | `CPF do Assistido.pdf` |
| **CPF do responsável** | `CPF do responsável.jpeg` (ou `.pdf`) | `CPF do responsável.pdf` |
| **CPF do assistido/ responsável** | `CPF do assistido responsável.jpeg` | `CPF do assistido responsável.pdf` |
| **Comprovante de escolaridade** | `Comprovante de escolaridade 1.jpeg` | `Comprovante de escolaridade 2.jpeg` |
| **Comprovante de Renda** | `Comprovante de Renda 1.jpeg` | `Comprovante de Renda 2.jpeg`, `Comprovante de Renda 3.jpeg` |
| **Comprovante de residência** | `Comprovante de residência.jpeg` (ou `.pdf`) | `Comprovante de residência.pdf` |
| **Documentação 1** | `Documentação 1.jpeg` (ou `.pdf`) | `Documentação 1.pdf` |
| **Documentação 2** | `Documentação 2.jpeg` (ou `.pdf`) | `Documentação 2.pdf` |
| **Documento parente beneficiado** | `Documento parente beneficiado.jpeg` | `Documento parente beneficiado 1.jpeg` |
| **Ficha antiga** | `Ficha antiga.jpeg` (ou `.pdf`) | `Ficha antiga.pdf` |
| **Foto** | `Foto 1.jfif` / `Foto 1.jpeg` *(Rosto)* | `Foto 2.jfif` / `Foto 2.jpeg` *(Corpo Inteiro)* |
| **Laudo médico (com CID)** | `Laudo médico (com CID).jpeg` (ou `.pdf`) | `Laudo médico 1.jpeg`, `Laudo médico 2.jpeg` |
| **Prescrição da Cadeira** | `Prescrição da Cadeira.jpeg` (ou `.pdf`) | `Prescrição da Cadeira.pdf` |
| **RG do Assistido** | `RG do Assistido 1.jpeg` *(Frente)* | `RG do Assistido 2.jpeg` *(Verso)* |
| **RG do responsável** | `RG do responsável 1.jpeg` *(Frente)* | `RG do responsável 2.jpeg` *(Verso)* |
| **Termo de autorização de imagem** | `Termo de autorização de imagem.jpeg` | `Termo de autorização de imagem.pdf` |
| **Termo de responsabilidade** | `Termo de responsabilidade.jpeg` | `Termo de responsabilidade.pdf` |

---

### 6. JSON para Integração via API (`POST /api/cadastro-familia`)

Payload JSON estruturado com todos os dados da família, criança, laudos e endereços.

---

## ⚡ Ações Práticas Automatizadas

Ao processar uma solicitação no ambiente local:
1. **Identificar os arquivos na pasta do caso** (ex: imagens do WhatsApp, PDFs de laudos e termos).
2. **Executar a renomeação direta dos arquivos locais** para as categorias oficiais do sistema (ex: `RG do Assistido 1.jpeg`, `Comprovante de residência.jpeg`, etc.).
3. **Gerar o arquivo `Carta.txt`** com o texto do relato da mãe/assistido enviado no chat.
4. Apresentar a resposta completa e links clicáveis para os arquivos renomeados no formato `[Nome](file:///...)`.