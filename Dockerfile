FROM python:3.11-slim

# Instala dependências do sistema e Tesseract com idioma português
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria pastas necessárias
RUN mkdir -p upload saida saida/.web_sessions

# Porta padrão (Render e Railway injetam a variável PORT)
ENV PORT=8000
EXPOSE 8000

# Executa o servidor FastAPI
CMD ["sh", "-c", "uvicorn src.web.app:app --host 0.0.0.0 --port ${PORT}"]

