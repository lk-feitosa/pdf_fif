"""Módulo compatível com versões anteriores para manipulação de nomes e templates."""

from __future__ import annotations

from .core.naming import (
    NamingContext,
    USER_PLACEHOLDERS,
    apply_template,
    default_template,
    normalize_template,
    parse_year_month,
    slugify,
    split_person_name,
)

__all__ = [
    "NamingContext",
    "USER_PLACEHOLDERS",
    "apply_template",
    "default_template",
    "normalize_template",
    "parse_year_month",
    "slugify",
    "split_person_name",
]
