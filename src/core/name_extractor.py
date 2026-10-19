"""Orquestrador unificado de extração de dados e nomes de folhas de frequência."""

from __future__ import annotations

import logging
from typing import Optional

import pymupdf

from .gemini_extractor import extract_page_gemini, is_gemini_available
from .local_extractor import extract_page_local
from .models import PageRecord

logger = logging.getLogger(__name__)


def extract_page_record(
    page: pymupdf.Page,
    page_num: int,
    *,
    api_key: Optional[str] = None,
    use_gemini: bool = True,
) -> PageRecord:
    """
    Analisa uma página e retorna um PageRecord completo.
    Estratégia: Gemini Vision AI (se ativo) -> OCR Local Inteligente -> Fallback
    """
    # 1. Tenta Gemini se habilitado
    if use_gemini and is_gemini_available(api_key):
        try:
            nome, matr, cargo, periodo = extract_page_gemini(page, api_key=api_key)
            if nome:
                return PageRecord(
                    page_num=page_num,
                    nome=nome,
                    matricula=matr,
                    cargo=cargo,
                    periodo=periodo,
                    source="gemini",
                    confidence=0.98,
                )
        except Exception as exc:
            logger.warning(f"Falha na extração com Gemini na pág. {page_num}: {exc}")

    # 2. Fallback para extrator local inteligente
    try:
        nome, matr, cargo = extract_page_local(page)
        if nome:
            return PageRecord(
                page_num=page_num,
                nome=nome,
                matricula=matr,
                cargo=cargo,
                source="local",
                confidence=0.90,
            )
    except Exception as exc:
        logger.warning(f"Falha no OCR local na pág. {page_num}: {exc}")

    # 3. Fallback genérico se nada for detectado
    return PageRecord(
        page_num=page_num,
        nome=f"pagina_{page_num:03d}",
        matricula=None,
        cargo=None,
        source="fallback",
        confidence=0.20,
    )
