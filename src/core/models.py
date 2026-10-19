"""Modelos de dados para o processamento de FIFs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PageRecord:
    page_num: int  # 1-indexed
    nome: str
    matricula: str | None = None
    cargo: str | None = None
    periodo: str | None = None
    source: str = "local"  # "gemini", "local", "manual"
    confidence: float = 1.0


@dataclass
class SplitJobConfig:
    template: str = "{ano}_{mes}_{nome}.pdf"
    prefixo: str | None = None
    ano: str | None = None
    mes: str | None = None
    mode: str = "one_per_page"  # "one_per_page" ou "group_consecutive"
    gemini_api_key: str | None = None
    use_gemini: bool = True


@dataclass
class SplitResult:
    filename: str
    person_name: str
    matricula: str | None
    page_numbers: list[int]
    path: Path


@dataclass
class SplitSummary:
    results: list[SplitResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_pages: int = 0
    total_files: int = 0
    zip_path: Path | None = None
