#!/usr/bin/env python3
"""Ponto de entrada do projeto PDF FIF."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.cli import main as cli_main  # noqa: E402
    from src.interactive import run_interactive  # noqa: E402
    from src.web.app import run_web  # noqa: E402
except ModuleNotFoundError as exc:
    missing = exc.name or "dependência"
    raise SystemExit(
        f"Módulo '{missing}' não encontrado.\n\n"
        "Ative o ambiente virtual e instale as dependências:\n"
        "  source .venv/bin/activate\n"
        "  pip install -r requirements.txt\n\n"
        "Ou use o script que faz isso automaticamente:\n"
        "  ./run.sh"
    ) from exc


def main() -> int:
    args = sys.argv[1:]

    # Se chamado com argumento 'bot'
    if args and args[0] in ("bot", "--bot"):
        from src.bot import main as bot_main
        bot_main()
        return 0

    # Se chamado com argumento 'terminal' ou '--terminal'
    if args and args[0] in ("terminal", "--terminal", "-i", "--interactive"):
        return run_interactive()

    # Se chamado com argumento 'web' ou '--web'
    if args and args[0] in ("web", "--web"):
        run_web()
        return 0

    # Se chamado com argumentos de arquivo ou opções do CLI (ex: arquivo.pdf, -o, -t)
    if args:
        return cli_main(args)

    # Chamado sem argumentos: inicia a interface Web moderna
    run_web()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
