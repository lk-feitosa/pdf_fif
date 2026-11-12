"""Detecção automática de mês e ano de referência de folhas de frequência."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import pymupdf
from unidecode import unidecode

logger = logging.getLogger(__name__)

MONTH_NAME_TO_NUM = {
    "janeiro": "01",
    "jan": "01",
    "fevereiro": "02",
    "fev": "02",
    "marco": "03",
    "março": "03",
    "mar": "03",
    "abril": "04",
    "abr": "04",
    "maio": "05",
    "mai": "05",
    "junho": "06",
    "jun": "06",
    "julho": "07",
    "jul": "07",
    "agosto": "08",
    "ago": "08",
    "setembro": "09",
    "set": "09",
    "outubro": "10",
    "out": "10",
    "novembro": "11",
    "nov": "11",
    "dezembro": "12",
    "dez": "12",
}

MONTH_REGEX_STR = "|".join(sorted(MONTH_NAME_TO_NUM.keys(), key=lambda s: -len(s)))


def extract_period_from_text(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrai (ano, mes) a partir de uma string de texto."""
    if not text:
        return None, None

    cleaned_text = unidecode(text).lower()
    detected_year: Optional[str] = None
    detected_month: Optional[str] = None

    # 1. Padrão: Nome do mês seguido de ano (ex: "SETEMBRO / 2026", "outubro de 2026")
    m_month_year = re.search(
        rf"\b({MONTH_REGEX_STR})\b[^\w\n]*(?:de\s+)?(202\d)\b",
        cleaned_text,
    )
    if m_month_year:
        m_name = m_month_year.group(1)
        detected_month = MONTH_NAME_TO_NUM.get(m_name)
        detected_year = m_month_year.group(2)
        return detected_year, detected_month

    # 2. Padrão: Ano seguido de nome do mês (ex: "2026 - SETEMBRO")
    m_year_month = re.search(
        rf"\b(202\d)\b[^\w\n]*(?:de\s+)?({MONTH_REGEX_STR})\b",
        cleaned_text,
    )
    if m_year_month:
        detected_year = m_year_month.group(1)
        m_name = m_year_month.group(2)
        detected_month = MONTH_NAME_TO_NUM.get(m_name)
        return detected_year, detected_month

    # 3. Padrão: MÊS/ANO: MM/AAAA ou MM/AA (ex: "MÊS/ANO 10/2026" ou "09/2026")
    m_slash = re.search(
        r"(?:mes|periodo|referencia|ref)?[^\w\n]*:?\s*([0-1]?\d)\s*/\s*(202\d)\b",
        cleaned_text,
    )
    if m_slash:
        m_num = int(m_slash.group(1))
        if 1 <= m_num <= 12:
            detected_month = f"{m_num:02d}"
            detected_year = m_slash.group(2)
            return detected_year, detected_month

    # 4. Padrão de datas completas (ex: "01/10/2026", "31/09/2026")
    dates = re.findall(r"\b\d{2}/([0-1]\d)/(202\d)\b", cleaned_text)
    if dates:
        # Pega a primeira data válida
        for m_str, y_str in dates:
            m_val = int(m_str)
            if 1 <= m_val <= 12:
                detected_month = f"{m_val:02d}"
                detected_year = y_str
                return detected_year, detected_month

    # 5. Busca apenas pelo nome do mês
    m_name_only = re.search(rf"\b({MONTH_REGEX_STR})\b", cleaned_text)
    if m_name_only:
        detected_month = MONTH_NAME_TO_NUM.get(m_name_only.group(1))

    # 6. Busca apenas pelo ano
    m_year_only = re.search(r"\b(202\d)\b", cleaned_text)
    if m_year_only:
        detected_year = m_year_only.group(1)

    return detected_year, detected_month


def extract_period_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Tenta identificar ano e mês a partir do nome do arquivo (ex: '10.pdf', 'setembro.pdf', '2026_10.pdf')."""
    if not filename:
        return None, None

    stem = Path(filename).stem
    cleaned_stem = unidecode(stem).lower()

    # Se o nome do arquivo for exatamente o número do mês (ex: '10.pdf', '09.pdf', '7.pdf')
    if re.fullmatch(r"0?[1-9]|1[0-2]", cleaned_stem):
        return None, f"{int(cleaned_stem):02d}"

    # Padrão 'YYYY_MM' ou 'YYYY-MM' (ex: '2026_10', '2026-09')
    m_ym = re.search(r"\b(202\d)[-_](0?[1-9]|1[0-2])\b", cleaned_stem)
    if m_ym:
        return m_ym.group(1), f"{int(m_ym.group(2)):02d}"

    # Padrão 'MM_YYYY' ou 'MM-YYYY' (ex: '10_2026', '09-2026')
    m_my = re.search(r"\b(0?[1-9]|1[0-2])[-_](202\d)\b", cleaned_stem)
    if m_my:
        return m_my.group(2), f"{int(m_my.group(1)):02d}"

    # Verifica nomes de mês no nome do arquivo
    year, month = extract_period_from_text(cleaned_stem)
    return year, month


def detect_document_period(
    pdf_path: Optional[Path] = None,
    filename: Optional[str] = None,
    gemini_period: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Identifica o ano e mês de referência do documento com fallback inteligente.
    Retorna sempre (ano, mes) com 2 dígitos no mês (ex: ('2026', '10')).
    """
    detected_year: Optional[str] = None
    detected_month: Optional[str] = None

    # 1. Se Gemini já extraiu o período na análise
    if gemini_period:
        y, m = extract_period_from_text(gemini_period)
        if y:
            detected_year = y
        if m:
            detected_month = m

    # 2. Se tivermos o arquivo PDF, analisa o cabeçalho da primeira página
    if (not detected_year or not detected_month) and pdf_path and pdf_path.exists():
        try:
            doc = pymupdf.open(pdf_path)
            if len(doc) > 0:
                first_page = doc[0]

                # Tenta texto vetorial embutido
                vec_text = first_page.get_text("text")
                if vec_text and len(vec_text.strip()) > 20:
                    y, m = extract_period_from_text(vec_text)
                    if not detected_year and y:
                        detected_year = y
                    if not detected_month and m:
                        detected_month = m

                # Se ainda não encontrou mês, tenta OCR no cabeçalho superior (onde fica MÊS/ANO)
                if not detected_month:
                    try:
                        import pytesseract
                        from PIL import Image

                        rect = first_page.rect
                        top_header = pymupdf.Rect(0, 0, rect.width, rect.height * 0.35)
                        pix = first_page.get_pixmap(clip=top_header, dpi=200)
                        img = Image.open(BytesIO(pix.tobytes("png")))
                        ocr_header = pytesseract.image_to_string(img, lang="por")
                        y, m = extract_period_from_text(ocr_header)
                        if not detected_year and y:
                            detected_year = y
                        if not detected_month and m:
                            detected_month = m
                    except Exception as ocr_err:
                        logger.debug(f"OCR de cabeçalho ignorado ou falhou: {ocr_err}")

            doc.close()
        except Exception as exc:
            logger.warning(f"Erro ao ler cabeçalho do PDF para detecção de período: {exc}")

    # 3. Tenta pelo nome do arquivo (ex: '10.pdf' ou 'setembro.pdf')
    file_label = filename or (pdf_path.name if pdf_path else None)
    if file_label:
        y_f, m_f = extract_period_from_filename(file_label)
        if not detected_year and y_f:
            detected_year = y_f
        if not detected_month and m_f:
            detected_month = m_f

    # 4. Fallback dinâmico para a data atual do sistema (em vez de um mês fixo)
    now = datetime.now()
    final_year = detected_year or str(now.year)
    final_month = detected_month or f"{now.month:02d}"

    return final_year, final_month

