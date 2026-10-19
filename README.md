# PDF FIF — Separador Inteligente de Folhas de Frequência 🚀

Aplicação moderna para processamento de folhas de frequência/ponto individuais (FIF). Recebe um arquivo PDF contendo múltiplas páginas, identifica o nome do servidor/colaborador de cada folha via **IA Google Gemini Vision** ou **OCR Local Inteligente**, e gera automaticamente arquivos PDF individuais já nomeados e organizados em ZIP.

---

## ✨ Principais Recursos

- 🌐 **Interface Web Moderna e Interativa (SPA)**:
  - Drag-and-drop de arquivos PDF (suporta arquivos pesados e dezenas de páginas).
  - Miniaturas visuais em alta definição de cada página do documento.
  - Conferência e edição inline dos nomes detectados antes de salvar.
  - Construtor interativo de padrões de nomenclatura com tags dinâmicas e preview em tempo real.
  - Download em lote compactado em arquivo `.ZIP` ou download individual de cada folha.
- 🤖 **Motor Híbrido de Reconhecimento**:
  - **Google Gemini Vision AI (`gemini-2.5-flash`)**: Reconhecimento visual com 100% de precisão para documentos manuscritos, escaneados, carimbados ou em layouts complexos.
  - **OCR Local Inteligente (PyMuPDF + Tesseract direcionado)**: 100% offline e gratuito. Foca nas zonas de identificação (cabeçalho e rodapé), eliminando ruídos de tabelas e assinaturas.
- ⚙️ **Regras Flexíveis de Separação**:
  - *1 folha por pessoa*: Cada página vira um arquivo separado.
  - *Agrupar páginas consecutivas*: Agrupa folhas de quem possui 2 ou mais páginas na mesma frequência.
- 💬 **Interfaces Múltiplas**:
  - Web UI no navegador (`http://localhost:8000`)
  - Terminal interativo (`python main.py --terminal`)
  - Linha de comando direta / CLI (`python main.py upload/arquivo.pdf`)
  - Bot do Telegram (`python main.py bot`)

---

## 🚀 Como Iniciar

### 1. Iniciar a Interface Web (Recomendado)

Basta executar o script de inicialização:

```bash
./run.sh
```

Ou diretamente com o Python do ambiente virtual:

```bash
source .venv/bin/activate
python main.py
```

O sistema abrirá automaticamente a interface em: **`http://localhost:8000`**

---

## 🔑 Configuração da API do Google Gemini (Opcional)

A IA do Gemini é opcional. Se não configurada, o sistema usa o **OCR Local Inteligente** automaticamente.

Para ativar o Gemini:
1. Obtenha uma chave gratuita no [Google AI Studio](https://aistudio.google.com/).
2. Insira no arquivo `.env`:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. *Ou configure direto na Web UI*, clicando no botão **⚙️ Configurações** no topo da página.

---

## 🏷️ Padrões de Nomenclatura dos Arquivos

Você pode personalizar o nome dos arquivos de saída com as seguintes tags:

| Tag | Descrição | Exemplo |
|---|---|---|
| `{nome}` | Nome completo formatado | `alvaro_nunes_prestes` |
| `{primeiro_nome}` | Primeiro nome | `alvaro` |
| `{sobrenome}` | Sobrenome principal | `prestes` |
| `{matricula}` | Matrícula funcional (se detectada) | `7971` |
| `{ano}` | Ano da folha (informado ou atual) | `2026` |
| `{mes}` | Mês da folha (2 dígitos) | `09` |
| `{pagina}` | Número da página original | `001` |

**Exemplo de template:**
`{ano}_{mes}_{matricula}_{nome}.pdf` → `2026_09_7971_alvaro_nunes_prestes.pdf`

---

## 💻 Outros Modos de Uso

### Modo Linha de Comando (CLI)

```bash
# Processar um PDF específico
python main.py upload/setembro.pdf -o saida/ --ano 2026 --mes 09 -t "{ano}_{mes}_{nome}.pdf"

# Processar pasta inteira
python main.py upload/ -o saida/
```

### Modo Terminal Interativo

```bash
python main.py --terminal
```

### Bot do Telegram

1. Configure `TELEGRAM_BOT_TOKEN` no `.env`.
2. Inicie o bot:
   ```bash
   python main.py bot
   ```
3. Envie o PDF no chat do bot para receber o `.ZIP` com as folhas separadas.

---

## 🧪 Executar Testes

```bash
python tests/test_split.py
```
