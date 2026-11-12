<div align="center">
  <img src="src/web/static/logo.png" alt="PDF FIF Logo" width="88" style="border-radius: 16px; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
  <h1>PDF FIF</h1>
  <p><strong>Separador Automático de Folhas Individuais de Frequência</strong></p>
  <p>Aplicação para processar documentos de frequência digitalizados, identificar servidores com OCR local e gerar arquivos individuais padronizados.</p>

  <p>
    <a href="https://render.com/deploy?repo=https://github.com/lk-feitosa/pdf_fif">
      <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
    </a>
  </p>
</div>

---

## Sobre o projeto

O PDF FIF automatiza a separação de folhas individuais de frequência a partir de arquivos PDF digitalizados. O sistema reconhece nomes e períodos de referência, organiza os documentos e disponibiliza os resultados em um arquivo `.ZIP`.

O processamento é realizado localmente, com OCR offline, sem depender de serviços externos para a operação principal.

## Principais recursos

- Processamento de lotes de folhas de frequência em PDF
- OCR local com suporte ao português
- Identificação automática de servidor, ano e mês de referência
- Geração de arquivos individuais em PDF
- Personalização do padrão de nomenclatura dos arquivos
- Interface web, linha de comando e bot do Telegram

## Execução local

```bash
git clone https://github.com/lk-feitosa/pdf_fif.git
cd pdf_fif
./run.sh
```

A aplicação estará disponível em `http://localhost:8000`.

Também é possível executar com Docker:

```bash
docker build -t pdf-fif .
docker run -p 8000:8000 pdf-fif
```

## Deploy

O projeto pode ser publicado no Render usando o botão acima ou conectado como um novo Web Service. A configuração de deploy está definida no `Dockerfile` e no `render.yaml`.

## Nomenclatura dos arquivos

O sistema detecta automaticamente o período de referência e permite escolher diferentes formatos de saída:

| Formato | Exemplo |
|---|---|
| Primeiro e sobrenome | `2026_10_maria_silva.pdf` |
| Nome completo | `2026_10_maria_da_silva_santos.pdf` |
| Primeiro nome | `2026_10_maria.pdf` |
| Matrícula e nome | `2026_10_12345_maria_silva.pdf` |

## Configuração

O processamento local utiliza PyMuPDF e Tesseract OCR. As principais variáveis de ambiente são:

| Variável | Padrão | Descrição |
|---|:---:|---|
| `PORT` | `8000` | Porta do servidor web. |
| `GEMINI_API_KEY` | vazia | Chave opcional para recursos de IA. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Modelo opcional de visão. |
| `TELEGRAM_BOT_TOKEN` | vazia | Token opcional do bot do Telegram. |

## Estrutura do projeto

```text
├── Dockerfile             # Container com Python 3.11 e Tesseract OCR
├── render.yaml            # Configuração de deploy no Render
├── run.sh                 # Script de execução
├── requirements.txt       # Dependências da aplicação
├── src/
│   ├── core/              # OCR, extração, detecção e separação de documentos
│   ├── web/               # Servidor FastAPI e interface web
│   ├── cli.py             # Interface de linha de comando
│   ├── interactive.py     # Modo interativo no terminal
│   └── bot.py             # Bot do Telegram
├── tests/                 # Testes automatizados
├── upload/                # Arquivos de entrada
└── saida/                 # Arquivos processados
```
