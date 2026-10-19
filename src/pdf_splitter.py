"""Módulo compatível com versões anteriores para separação de PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .core.models import PageRecord, SplitJobConfig, SplitResult, SplitSummary
from .core.pdf_splitter import (
    analyze_pdf,
    create_zip_from_results,
    split_pdf as core_split_pdf,
)

__all__ = ["SplitResult", "SplitSummary", "split_pdf", "create_zip_from_results", "analyze_pdf"]


def split_pdf(
    input_path: Path,
    output_dir: Path,
    *,
    template: str = "{ano}_{mes}_{nome}.pdf",
    prefixo: Optional[str] = None,
    ano: Optional[str] = None,
    mes: Optional[str] = None,
    mode: str = "one_per_page",
    config: Optional[SplitJobConfig] = None,
    page_records: Optional[list[PageRecord]] = None,
) -> SplitSummary:
    """Wrapper compatível com chamadas anteriores."""
    if config is None:
        config = SplitJobConfig(
            template=template,
            prefixo=prefixo,
            ano=ano,
            mes=mes,
            mode=mode,
        )
    return core_split_pdf(input_path, output_dir, config=config, page_records=page_records)
