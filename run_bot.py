#!/usr/bin/env python3
"""Inicia o bot Telegram."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bot import main  # noqa: E402

if __name__ == "__main__":
    main()
