"""Módulo compatível com versões anteriores para extração de nomes."""

from __future__ import annotations

from .core.local_extractor import _extract_from_text_stream
from .core.name_extractor import extract_page_record

__all__ = ["extract_name_from_text", "extract_page_record"]


def extract_name_from_text(text: str) -> str | None:
    """Extrai nome do texto (compatibilidade com testes e scripts anteriores)."""
    nome, _ = _extract_from_text_stream(text)
    return nome
