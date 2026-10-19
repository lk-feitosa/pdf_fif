#!/usr/bin/env bash
# Roda o PDF FIF usando o Python do projeto (venv)
set -e
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Ambiente não instalado. Rode primeiro:"
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if ! .venv/bin/python -c "import unidecode" 2>/dev/null; then
  echo "Instalando dependências..."
  .venv/bin/pip install -r requirements.txt -q
fi

exec .venv/bin/python main.py "$@"
