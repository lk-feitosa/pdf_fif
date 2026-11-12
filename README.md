<div align="center">

  <h1>📄 PDF FIF</h1>
  <p><strong>Separador Inteligente de Folhas Individuais de Frequência (FIF)</strong></p>

  <p>
    <a href="https://render.com/deploy?repo=https://github.com/lk-feitosa/pdf_fif">
      <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
    </a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
    <img src="https://img.shields.io/badge/Google%20Gemini-Vision-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini">
    <img src="https://img.shields.io/badge/Tesseract-OCR-555555?style=flat-square" alt="Tesseract">
  </p>

  <br>

  <img src="docs/preview.jpg" alt="Interface PDF FIF" width="850" style="border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 30px rgba(0,0,0,0.5);">

  <br><br>
</div>

---

## 💡 O que é?

O **PDF FIF** recebe um arquivo PDF contendo dezenas ou centenas de folhas de ponto/frequência escaneadas, identifica automaticamente o nome de cada servidor (via **OCR Local** ou **Google Gemini Vision**) e gera arquivos individuais renomeados e prontos para download em `.ZIP`.

---

## ✨ Recursos

- 🔍 **Reconhecimento Híbrido**: Google Gemini Vision (`gemini-2.5-flash`) ou Tesseract OCR Local 100% offline.
- 📅 **Detecção Automática de Período**: Reconhece automaticamente o mês e ano no cabeçalho ou no nome do arquivo (ex: `2026_10_`).
- 🏷️ **Nomenclatura Dinâmica**: Padrão inteligente (`2026_10_carlos_sardinha.pdf`) com pré-visualização em tempo real em cada card.
- 🔗 **Agrupamento Flexível**: Botão de *Juntar com próxima* caso um colaborador possua 2 ou mais páginas na mesma folha.
- 📦 **Download Rápido**: Baixe individualmente ou tudo compactado em um único `.ZIP`.
- 🌐 **Web SPA Moderna**: Interface escura estilo Linear / Vercel com zoom de miniaturas.

---

## ☁️ Deploy no Render (1 Clique)

Você pode hospedar gratuitamente no **Render**:

1. Clique no botão abaixo:

   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/lk-feitosa/pdf_fif)

2. Conecte sua conta do GitHub.
3. Defina a variável de ambiente opcional `GEMINI_API_KEY` (se for utilizar a IA do Gemini).
4. O Render detectará automaticamente o [`Dockerfile`](Dockerfile) e o [`render.yaml`](render.yaml) e subirá a aplicação.

---

## 🚀 Como Rodar Localmente

### Opção 1: Direto com Python

```bash
# Clone o repositório
git clone https://github.com/lk-feitosa/pdf_fif.git
cd pdf_fif

# Inicie o script (cria ambiente e instala dependências automaticamente)
./run.sh
```

Acesse: **`http://localhost:8000`**

### Opção 2: Com Docker

```bash
docker build -t pdf-fif .
docker run -p 8000:8000 pdf-fif
```

Acesse: **`http://localhost:8000`**

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` na raiz (ou configure no painel do Render):

| Variável | Obrigatória | Padrão | Descrição |
|---|:---:|:---:|---|
| `GEMINI_API_KEY` | Não | *vazia* | Chave da API do Google Gemini Studio (se não informada, usa OCR local). |
| `GEMINI_MODEL` | Não | `gemini-2.5-flash` | Modelo do Gemini para leitura visual. |
| `PORT` | Não | `8000` | Porta onde o servidor FastAPI responderá. |

---

## 📁 Estrutura do Projeto

```text
├── Dockerfile             # Container com Python + Tesseract OCR em português
├── render.yaml            # Configuração de Blueprint para deploy no Render
├── run.sh                 # Script de execução local rápida
├── requirements.txt       # Dependências Python (FastAPI, PyMuPDF, etc.)
├── src/
│   ├── core/              # Extração de nomes, OCR, Gemini e fatiamento do PDF
│   └── web/               # Servidor FastAPI e frontend moderno (HTML/CSS/JS)
├── upload/                # Pasta de entrada para testes
└── saida/                 # Pasta de saída dos PDFs processados
```

---

<div align="center">
  <sub>Desenvolvido com foco em produtividade e simplicidade.</sub>
</div>
