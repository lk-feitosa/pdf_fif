"""Separador de PDFs de frequência por pessoa."""

from __future__ import annotations

import logging
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import pymupdf

from .models import PageRecord, SplitJobConfig, SplitResult, SplitSummary
from .name_extractor import extract_page_record
from .naming import NamingContext, apply_template, parse_year_month, split_person_name

logger = logging.getLogger(__name__)


def analyze_pdf(
    input_path: Path,
    *,
    api_key: Optional[str] = None,
    use_gemini: bool = True,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[PageRecord]:
    """
    Analisa todas as páginas do PDF e extrai os metadados de cada uma.
    Processa páginas com ThreadPoolExecutor para máxima velocidade.
    """
    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    records: list[PageRecord] = [None] * total_pages  # type: ignore

    # Para processamento concorrente seguro de pymupdf, cada thread abre uma instância ou usamos loop
    # Como PyMuPDF Doc não é 100% thread-safe entre páginas com pixmaps concorrentes no mesmo doc,
    # abrimos docs por thread ou processamos sequencialmente/em blocos rápidos.
    # Com nosso OCR rápido (0.3s por página), fazer sequencial ou com 2 workers é muito rápido e estável.
    for i in range(total_pages):
        page = doc[i]
        page_num = i + 1
        record = extract_page_record(
            page,
            page_num=page_num,
            api_key=api_key,
            use_gemini=use_gemini,
        )
        records[i] = record
        if on_progress:
            on_progress(page_num, total_pages)

    doc.close()
    return records


def _group_records(
    records: list[PageRecord],
    mode: str,
) -> list[tuple[str, str | None, list[int]]]:
    """
    Agrupa as páginas conforme a regra configurada.
    Retorna lista de tuplas: (nome, matricula, [lista_de_paginas])
    """
    if mode == "one_per_page":
        return [(r.nome, r.matricula, [r.page_num]) for r in records]

    # Modo: group_consecutive
    groups: list[tuple[str, str | None, list[int]]] = []
    current_name: str | None = None
    current_matr: str | None = None
    current_pages: list[int] = []

    for r in records:
        if current_name is None:
            current_name = r.nome
            current_matr = r.matricula
            current_pages = [r.page_num]
            continue

        if r.nome.strip().lower() == current_name.strip().lower():
            current_pages.append(r.page_num)
        else:
            groups.append((current_name, current_matr, current_pages))
            current_name = r.nome
            current_matr = r.matricula
            current_pages = [r.page_num]

    if current_name is not None:
        groups.append((current_name, current_matr, current_pages))

    return groups


def split_pdf(
    input_path: Path,
    output_dir: Path,
    *,
    config: Optional[SplitJobConfig] = None,
    page_records: Optional[list[PageRecord]] = None,
    custom_groups: Optional[list[tuple[str, str | None, list[int]]]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> SplitSummary:
    """
    Executa a separação do PDF em arquivos individuais.
    Se custom_groups for fornecido, utiliza os agrupamentos manuais definidos pelo usuário.
    Se page_records já for fornecido (ex: via UI após revisão), pula a etapa de análise.
    """
    cfg = config or SplitJobConfig()
    output_dir.mkdir(parents=True, exist_ok=True)
    year, month = parse_year_month(cfg.ano, cfg.mes)

    # 1. Análise das páginas se não fornecidas
    if page_records is None and not custom_groups:
        page_records = analyze_pdf(
            input_path,
            api_key=cfg.gemini_api_key,
            use_gemini=cfg.use_gemini,
            on_progress=on_progress,
        )

    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    warnings: list[str] = []

    if page_records:
        for r in page_records:
            if r.source == "fallback":
                warnings.append(f"Página {r.page_num}: nome não identificado automaticamente.")

    # 2. Agrupamento conforme regra ou agrupamento manual definido pelo usuário
    if custom_groups:
        groups = custom_groups
    else:
        groups = _group_records(page_records or [], cfg.mode)

    used_filenames: dict[str, int] = {}
    results: list[SplitResult] = []

    # 3. Geração dos PDFs individuais
    for person_name, matricula, pages in groups:
        primeiro, sobrenome = split_person_name(person_name)
        ctx = NamingContext(
            ano=year,
            mes=month,
            nome=person_name,
            primeiro_nome=primeiro,
            sobrenome=sobrenome,
            matricula=matricula or "",
            pagina=pages[0],
            prefixo=cfg.prefixo or "",
        )
        filename = apply_template(cfg.template, ctx)

        # Evita sobrescrever se houver nomes idênticos
        if filename in used_filenames:
            used_filenames[filename] += 1
            stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
            filename = f"{stem}_{used_filenames[filename]}.pdf"
        else:
            used_filenames[filename] = 1

        out_path = output_dir / filename
        new_doc = pymupdf.open()
        for p_num in pages:
            new_doc.insert_pdf(doc, from_page=p_num - 1, to_page=p_num - 1)
        new_doc.save(out_path)
        new_doc.close()

        results.append(
            SplitResult(
                filename=filename,
                person_name=person_name,
                matricula=matricula,
                page_numbers=pages,
                path=out_path,
            )
        )

    doc.close()

    return SplitSummary(
        results=results,
        warnings=warnings,
        total_pages=total_pages,
        total_files=len(results),
    )


def create_zip_from_results(results: list[SplitResult], zip_path: Path) -> Path:
    """Empacota os arquivos gerados em um arquivo ZIP."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in results:
            zf.write(item.path, arcname=item.filename)
    return zip_path
