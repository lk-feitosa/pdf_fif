"""Testes para o detector automático de ano e mês."""

from pathlib import Path
from src.core.period_detector import (
    detect_document_period,
    extract_period_from_filename,
    extract_period_from_text,
)


def test_extract_period_from_text():
    # Padrão Mês / Ano
    y, m = extract_period_from_text("FOLHA DE FREQUENCIA SETEMBRO / 2026")
    assert y == "2026"
    assert m == "09"

    # Outubro de 2026
    y, m = extract_period_from_text("Referência: Outubro de 2026")
    assert y == "2026"
    assert m == "10"

    # 10/2026
    y, m = extract_period_from_text("MÊS/ANO: 10/2026")
    assert y == "2026"
    assert m == "10"

    # Data completa
    y, m = extract_period_from_text("PERIODO: 01/08/2026 A 31/08/2026")
    assert y == "2026"
    assert m == "08"


def test_extract_period_from_filename():
    assert extract_period_from_filename("10.pdf") == (None, "10")
    assert extract_period_from_filename("09.pdf") == (None, "09")
    assert extract_period_from_filename("setembro.pdf") == (None, "09")
    assert extract_period_from_filename("2026_10.pdf") == ("2026", "10")
    assert extract_period_from_filename("10_2026.pdf") == ("2026", "10")

