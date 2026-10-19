"""Extrator local de alta precisão usando PyMuPDF e Tesseract OCR."""

from __future__ import annotations

import re
from io import BytesIO
from typing import Tuple

import pymupdf
import pytesseract
from PIL import Image

IGNORE_WORDS = {
    "ESTADO", "TOCANTINS", "GOVERNO", "PREFEITURA", "MUNICIPIO", "MUNICÍPIO",
    "PODER", "LEGISLATIVO", "EXECUTIVO", "JUDICIARIO", "JUDICIÁRIO",
    "FOLHA", "FREQUENCIA", "FREQUÊNCIA", "PONTO", "INDIVIDUAL",
    "MATUTINO", "VESPERTINO", "NOTURNO", "ENTRADA", "SAIDA", "SAÍDA", "ASSINATURA",
    "OCORRENCIA", "OCORRÊNCIA", "INTERVALO", "REPOUSO", "ALIMENTACAO", "ALIMENTAÇÃO",
    "JUSTIFICADA", "ABONADA", "AUSENCIA", "AUSÊNCIA", "FACULTATIVO", "FERIADO",
    "SABADO", "SÁBADO", "DOMINGO", "HORAS", "HORA", "MES", "MÊS", "ANO", "DIAS",
    "DIRETORIA", "COORDENADORIA", "ANALISTA", "ASSISTENTE", "DIRETOR", "CHEFIA",
    "COORDENADOR", "SISTEMA", "SISTEMAS", "INFORMACOES", "INFORMAÇÕES",
    "CODAP", "MATRICULA", "MATRÍCULA", "CARGO", "LOTACAO", "LOTAÇÃO",
    "PERIODO", "PERÍODO", "IMEDIATA", "REFERENCIA", "REFERÊNCIA", "DEPARTAMENTO",
}

SUFFIX_STOPPERS = (
    r"(?:\s+(?:SERVIDOR|SERVIDO|CODAP|DIRETOR|ANALISTA|COORDENADOR|CHEFIA|"
    r"ASSISTENTE|ANALISE|DIRETORIA|COORDENADORIA|EFIA|DIRECAO|DIREÇÃO)\b|\n|$)"
)


def _is_plausible_name(candidate: str) -> bool:
    name = candidate.strip()
    if len(name) < 4 or len(name) > 70:
        return False
    if re.search(r"\d", name):
        return False

    words = [w for w in name.split() if len(w) >= 2]
    if len(words) < 2:
        return False

    # Verifica se contém palavras proibidas
    upper_words = [w.upper() for w in words]
    for w in upper_words:
        clean_w = re.sub(r"[^\w]", "", w)
        if clean_w in IGNORE_WORDS:
            return False

    return True


def _clean_extracted_name(raw: str) -> str:
    cleaned = raw.strip()
    # Remove ruídos comuns de OCR
    cleaned = re.sub(r"[|/\\_ºª~`^]", " ", cleaned)
    # Remove palavras de parada conhecidas no final
    cleaned = re.sub(
        r"\b(?:SERVIDOR|SERVIDO|CODAP|DIRETOR|ANALISTA|CHEFIA|COORDENADOR|ANALISE)\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    parts = []
    for p in cleaned.split():
        if (len(p) >= 2 or p.lower() in {"e", "d", "y"}) and re.match(r"^[A-Za-zÀ-ÿ'-]+$", p):
            parts.append(p)
    # Limita a 6 palavras no máximo (nomes comuns brasileiros)
    if len(parts) > 6:
        parts = parts[:6]

    return " ".join(parts).title()


def _extract_cargo(text: str) -> str | None:
    for line in text.splitlines():
        line_str = line.strip()
        if any(k in line_str.upper() for k in ["ANALISTA", "COORDENADOR", "DIRETOR", "ASSISTENTE", "TECNICO", "TÉCNICO", "GERENTE"]):
            # Limpa ruídos
            clean = re.sub(r"[|/\\_ºª~`^]", " ", line_str)
            clean = re.sub(r"\s+", " ", clean).strip()
            if 4 <= len(clean) <= 60:
                return clean.title()
    return None


def _extract_from_text_stream(text: str) -> Tuple[str | None, str | None]:
    """Tenta extrair (nome, matricula) a partir de texto."""
    if not text:
        return None, None

    # Padrão 1: Matrícula - Nome (em uma linha ou com quebra controlada)
    pat_matricula = re.compile(
        r"(\d{3,8})\s*[-–]\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÇa-záàâãéêíóôõúç\s\n]{3,80}?)"
        + SUFFIX_STOPPERS,
        re.MULTILINE | re.IGNORECASE,
    )
    match = pat_matricula.search(text)
    if match:
        matricula = match.group(1).strip()
        name_raw = match.group(2)
        candidate = _clean_extracted_name(name_raw)
        if _is_plausible_name(candidate):
            return candidate, matricula

    # Padrão 2: Linha explícita com rótulo (não cruza quebras de linha)
    pat_label = re.compile(
        r"(?:Nome(?:\s+do\s+Servidor|\s+Completo)?|Funcion[aá]rio|Servidor|Colaborador)\s*[:\-]?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n\r]{2,80})",
        re.IGNORECASE,
    )
    match = pat_label.search(text)
    if match:
        candidate = _clean_extracted_name(match.group(1))
        if _is_plausible_name(candidate):
            return candidate, None

    # Padrão 3: Qualquer linha iniciando por matrícula
    pat_line = re.compile(r"^\s*(\d{3,8})\s*[-–]\s*([^\n\r]+)", re.MULTILINE)
    match = pat_line.search(text)
    if match:
        matricula = match.group(1).strip()
        candidate = _clean_extracted_name(match.group(2))
        if _is_plausible_name(candidate):
            return candidate, matricula

    return None, None


def extract_page_local(page: pymupdf.Page) -> Tuple[str | None, str | None, str | None]:
    """
    Extrai informações da página localmente.
    Retorna: (nome, matricula, cargo)
    """
    # 1. Verifica texto vetorial embutido
    raw_text = page.get_text("text")
    if raw_text and len(raw_text.strip()) > 40:
        nome, matr = _extract_from_text_stream(raw_text)
        if nome:
            cargo = _extract_cargo(raw_text)
            return nome, matr, cargo

    # 2. Se for documento escaneado/imagem, faz OCR por regiões direcionadas
    rect = page.rect

    # Região A: Rodapé esquerdo (65% largura, 28% altura final) - ideal para FIFs estaduais/legislativas
    left_footer = pymupdf.Rect(0, rect.height * 0.72, rect.width * 0.65, rect.height)
    pix = page.get_pixmap(clip=left_footer, dpi=200)
    img_lf = Image.open(BytesIO(pix.tobytes("png")))
    ocr_lf = pytesseract.image_to_string(img_lf, lang="por")

    nome, matr = _extract_from_text_stream(ocr_lf)
    if nome:
        cargo = _extract_cargo(ocr_lf)
        return nome, matr, cargo

    # Região B: Cabeçalho superior (25% altura inicial)
    top_header = pymupdf.Rect(0, 0, rect.width, rect.height * 0.25)
    pix_h = page.get_pixmap(clip=top_header, dpi=200)
    img_h = Image.open(BytesIO(pix_h.tobytes("png")))
    ocr_h = pytesseract.image_to_string(img_h, lang="por")

    nome, matr = _extract_from_text_stream(ocr_h)
    if nome:
        cargo = _extract_cargo(ocr_h)
        return nome, matr, cargo

    # Região C: Rodapé completo
    full_footer = pymupdf.Rect(0, rect.height * 0.70, rect.width, rect.height)
    pix_ff = page.get_pixmap(clip=full_footer, dpi=200)
    img_ff = Image.open(BytesIO(pix_ff.tobytes("png")))
    ocr_ff = pytesseract.image_to_string(img_ff, lang="por")

    nome, matr = _extract_from_text_stream(ocr_ff)
    if nome:
        cargo = _extract_cargo(ocr_ff)
        return nome, matr, cargo

    return None, None, None

    return None, None, None
