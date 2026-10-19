# PDF FIF — Início Rápido

Guia de instalação, build e uso do separador de folhas de frequência.

---

## Pré-requisitos

- Python 3.10 ou superior
- pip
- **Tesseract OCR** (para ler PDFs escaneados)
- (Opcional) Conta no Telegram para usar o bot

### Instalação do Tesseract

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tesseract tesseract-langpack-por
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install tesseract-ocr libtesseract-dev tesseract-ocr-por
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Baixe o instalador em: https://github.com/UB-Mannheim/tesseract/wiki

---

## Instalação

```bash
cd /home/lk-codex/Documentos/PROJETOS/pdf_fif

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Verificar instalação

```bash
python tests/test_split.py
```

Se aparecer `OK — todos os testes passaram.`, está tudo certo.

---

## Recursos OCR para PDFs Escaneados

O sistema agora detecta automaticamente PDFs escaneados (imagens) e aplica **OCR com Tesseract** para extrair o nome da pessoa, mesmo que o PDF não tenha texto digital.

**Como funciona:**
1. ✅ **PDF com texto digital** → extração rápida (modo normal)
2. 📷 **PDF escaneado** → renderiza como imagem → OCR → extrai nome
3. **Idioma:** Português (PT) configurado automaticamente

Não precisa fazer nada especial — o sistema detecta e processa automaticamente!

## Uso no PC (modo fácil)

**Importante:** use o script `run.sh` (já ativa o ambiente correto) ou ative o venv antes de rodar `python main.py`.

```bash
source .venv/bin/activate   # se for usar python main.py direto
```

### Passo a passo

1. **Copie o PDF** para a pasta `upload/`
2. **Rode o programa:**

```bash
./run.sh
```

(Alternativa: `source .venv/bin/activate` e depois `python main.py`)

3. O terminal pergunta o padrão do nome. Digite algo como:

```
2026_08_*nome*.pdf
```

O `*nome*` será substituído pelo nome de cada pessoa detectada no PDF.

4. Os arquivos separados aparecem em `saida/`

**Exemplo completo:**

```
Qual padrão para o PDF de saída? 2026_08_*nome*.pdf

  ✓ 2026_08_maria.pdf  (Maria Da Silva, págs. 1)
  ✓ 2026_08_joao.pdf   (João Pereira, págs. 2)

Concluído: 2 PDF(s) em .../pdf_fif/saida
```

### Placeholders no padrão

| Você digita | Vira | Exemplo |
|-------------|------|---------|
| `*nome*` | primeiro nome | `joao` |
| `*nome_completo*` | nome completo | `joaosilva` |
| `*sobrenome*` | último sobrenome | `silva` |
| `*ano*` | ano atual | `2026` |
| `*mes*` | mês atual | `08` |

Também funciona o formato avançado: `{primeiro_nome}`, `{nome}`, `{ano}`, etc.

---

## Uso avançado (CLI)

Para quem prefere passar tudo na linha de comando:

```bash
python main.py upload/frequencias.pdf -t "2026_08_*nome*.pdf" -o ./saida
```

---

## Bot Telegram

### 1. Criar o bot

1. Abra o [@BotFather](https://t.me/BotFather) no Telegram
2. Envie `/newbot` e siga as instruções
3. Copie o token gerado

### 2. Configurar

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
```

### 3. Iniciar o bot

```bash
source .venv/bin/activate
python run_bot.py
```

O bot ficará rodando aguardando mensagens. Para parar: `Ctrl+C`.

### 4. Comandos no Telegram

| Comando | Descrição |
|---------|-----------|
| `/start` | Ajuda |
| `/config` | Ver configuração atual |
| `/ano 2026` | Define o ano nos nomes |
| `/mes 08` | Define o mês nos nomes |
| `/formato 2026_08_{primeiro_nome}.pdf` | Define o padrão do nome |

### 5. Enviar o PDF

1. Configure ano, mês e formato (se quiser)
2. Envie o PDF como **documento** (não como foto)
3. Aguarde o processamento
4. Receba um **ZIP** com os PDFs separados por pessoa

---

## Fluxo resumido

```
PDF com várias frequências
        ↓
  Lê texto de cada página
        ↓
  Detecta o nome de cada pessoa
        ↓
  Gera 1 PDF por pessoa
        ↓
  Nomeia conforme o template
        ↓
  Salva na pasta / envia ZIP no Telegram
```

---

## Problemas comuns

### Nome não detectado em alguma página

O sistema usa padrões como `Nome:`, `Funcionário:`, `Servidor:`. Se o seu PDF usa outro campo, edite `src/name_extractor.py` (lista `NAME_PATTERNS`).

### Bot não inicia / erro de proxy

Se aparecer `ProxyError` ou `403 Forbidden`:

```bash
NO_PROXY='*' python run_bot.py
```

Ou desative VPN/proxy do sistema. O bot foi ajustado para ignorar proxy automático, mas alguns ambientes ainda bloqueiam.

- Confira se o `.env` existe e tem `TELEGRAM_BOT_TOKEN` válido (do @BotFather)
- Verifique se o ambiente virtual está ativo (`source .venv/bin/activate`)

### Erro ao instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Estrutura do projeto

```
pdf_fif/
├── main.py          # Rode sem args: modo fácil (upload/ → saida/)
├── run_bot.py       # Bot Telegram
├── upload/          # Coloque o PDF aqui
├── saida/           # PDFs separados saem aqui
├── start.md         # Este guia
├── requirements.txt
├── .env.example
└── src/
    ├── pdf_splitter.py    # Separa o PDF
    ├── name_extractor.py  # Detecta nomes
    └── naming.py          # Template de nomes
```
