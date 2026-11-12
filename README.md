<div align="center">
  <img src="src/web/static/logo.png" alt="PDF FIF Logo" width="88" style="border-radius: 16px; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
  <h1>PDF FIF</h1>
  <p><strong>Separador Automático de Folhas Individuais de Frequência</strong></p>
  <p>Processa lotes de folhas de frequência escaneadas, identifica servidores via <strong>OCR Local (100% offline)</strong> e gera arquivos individuais padronizados em <code>.ZIP</code>.</p>

  <p>
    <a href="https://render.com/deploy?repo=https://github.com/lk-feitosa/pdf_fif">
      <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
    </a>
  </p>
</div>

---

## Como Rodar Localmente

```bash
# Clone e acesse o diretório do projeto
git clone https://github.com/lk-feitosa/pdf_fif.git
cd pdf_fif

# Inicia o projeto (instala dependências e abre o servidor web)
./run.sh
```

Acesse no navegador: **`http://localhost:8000`**

*(Ou via Docker: `docker build -t pdf-fif . && docker run -p 8000:8000 pdf-fif`)*

---

## Deploy no Render

1. Clique no botão **Deploy to Render** acima (ou crie um novo **Web Service** conectado ao repositório).
2. O Render utilizará o [`Dockerfile`](Dockerfile) automaticamente.
3. Não é necessária nenhuma configuração de chave ou banco de dados — o serviço inicia pronto para uso no plano gratuito.

---

## Nomenclatura e Exemplos

O sistema detecta automaticamente o ano e o mês de referência (ex: `2026_10_`) e permite personalizar o padrão de saída com dados fictícios de exemplo:

| Formato Selecionado | Padrão Gerado (Exemplo Fictício) |
|---|---|
| Primeiro e Sobrenome | `2026_10_maria_silva.pdf` |
| Nome Completo | `2026_10_maria_da_silva_santos.pdf` |
| Primeiro Nome | `2026_10_maria.pdf` |
| Matrícula + Nome | `2026_10_12345_maria_silva.pdf` |

---

## Configurações (.env)

O sistema opera **100% offline** por padrão utilizando PyMuPDF e Tesseract OCR:

| Variável | Padrão | Descrição |
|---|:---:|---|
| `PORT` | `8000` | Porta onde o servidor responderá. |
| `GEMINI_API_KEY` | *vazia* | *(Opcional)* Chave do Google AI Studio para suporte via IA se desejar no futuro. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | *(Opcional)* Modelo de visão caso a chave seja configurada. |
| `TELEGRAM_BOT_TOKEN` | *vazia* | *(Opcional)* Token do bot do Telegram para processamento via chat. |

---

## Estrutura do Projeto

```text
├── Dockerfile             # Container com Python 3.11 + Tesseract OCR em português
├── render.yaml            # Blueprint de deploy para o Render
├── run.sh                 # Script de execução rápida
├── requirements.txt       # Dependências da aplicação
├── src/
│   ├── core/              # Extração de nomes, OCR local, detector de período e fatiamento
│   ├── web/               # Servidor FastAPI e interface web (HTML/CSS/JS)
│   ├── cli.py             # Interface de linha de comando
│   ├── interactive.py     # Modo interativo no terminal
│   └── bot.py             # Bot do Telegram
├── tests/                 # Testes unitários automatizados
├── upload/                # Pasta para entrada de testes
└── saida/                 # Pasta de saída dos arquivos gerados
```
