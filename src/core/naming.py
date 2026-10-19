"""Utilitários para nomes de arquivo e formatação de templates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from unidecode import unidecode


@dataclass(frozen=True)
class NamingContext:
    ano: str
    mes: str
    nome: str
    primeiro_nome: str
    sobrenome: str
    matricula: str
    pagina: int
    prefixo: str = ""


def slugify(text: str, *, lowercase: bool = True, sep: str = "_") -> str:
    """Remove acentos e caracteres inválidos, substituindo espaços por separador."""
    if not text:
        return ""
    normalized = unidecode(text.strip())
    # Mantém apenas letras, números, hífens e sublinhados
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    normalized = re.sub(r"[\s_]+", sep, normalized)
    return normalized.lower() if lowercase else normalized


def split_person_name(full_name: str) -> tuple[str, str]:
    """Retorna (primeiro_nome, ultimo_sobrenome)."""
    parts = [p for p in re.split(r"\s+", full_name.strip()) if p]
    if not parts:
        return "desconhecido", "desconhecido"
    if len(parts) == 1:
        return parts[0], parts[0]

    first = parts[0]
    last = parts[-1]
    # Se a última parte for muito curta (lixo), tenta a anterior
    for part in reversed(parts[1:]):
        if len(part) >= 2 and re.match(r"^[A-Za-zÀ-ÿ]+$", part):
            last = part
            break

    return first, last


USER_PLACEHOLDERS = {
    "*prefixo*": "{prefixo}",
    "*nome*": "{primeiro_nome}",
    "*primeiro_nome*": "{primeiro_nome}",
    "*nome_completo*": "{nome}",
    "*nome_sobrenome*": "{primeiro_nome}_{sobrenome}",
    "*sobrenome*": "{sobrenome}",
    "*matricula*": "{matricula}",
    "*ano*": "{ano}",
    "*mes*": "{mes}",
    "*pagina*": "{pagina}",
}


def normalize_template(template: str) -> str:
    """Converte padrão amigável (*nome*) para placeholders internos ({primeiro_nome})."""
    result = template.strip()
    for user_token, internal in USER_PLACEHOLDERS.items():
        result = result.replace(user_token, internal)
    return result


def apply_template(template: str, context: NamingContext) -> str:
    """Substitui placeholders no template gerando um nome de arquivo seguro."""
    normalized_tmpl = normalize_template(template)

    values = {
        "prefixo": context.prefixo,
        "ano": context.ano,
        "mes": context.mes,
        "nome": slugify(context.nome),
        "primeiro_nome": slugify(context.primeiro_nome),
        "sobrenome": slugify(context.sobrenome),
        "matricula": slugify(context.matricula) if context.matricula else "",
        "pagina": f"{context.pagina:03d}",
    }

    result = normalized_tmpl
    for key, value in values.items():
        result = result.replace(f"{{{key}}}", value)

    # Se um prefixo foi passado explicitamente e o resultado ainda não o contém
    if context.prefixo and not result.startswith(context.prefixo):
        result = f"{context.prefixo}{result}"

    # Limpa possíveis duplos separadores (ex: __ gerado se matricula for vazia)
    result = re.sub(r"_{2,}", "_", result)
    result = re.sub(r"-[_-]+", "-", result)
    result = re.sub(r"[<>:\"/\\|?*]", "", result)
    result = result.strip(" ._-")

    if not result.lower().endswith(".pdf"):
        result += ".pdf"

    return result


def default_template() -> str:
    return "{ano}_{mes}_{nome}.pdf"


def parse_year_month(ano: str | None = None, mes: str | None = None) -> tuple[str, str]:
    now = datetime.now()
    year = str(ano).strip() if ano else str(now.year)
    month = str(mes).strip() if mes else f"{now.month:02d}"
    if len(month) == 1:
        month = f"0{month}"
    return year, month
