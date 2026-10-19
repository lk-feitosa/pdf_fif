"""Extrator baseado no Google Gemini Vision API."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Tuple

import pymupdf

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def is_gemini_available(api_key: str | None = None) -> bool:
    """Verifica se há chave de API disponível para o Gemini."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    return bool(key and key.strip() and key != "sua_chave_gemini_aqui")


def extract_page_gemini(
    page: pymupdf.Page,
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> Tuple[str | None, str | None, str | None, str | None]:
    """
    Analisa a página com a API Gemini Vision.
    Retorna: (nome, matricula, cargo, periodo)
    """
    resolved_key = api_key or os.getenv("GEMINI_API_KEY")
    if not resolved_key or resolved_key == "sua_chave_gemini_aqui":
        return None, None, None, None

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("Pacote google-genai não instalado.")
        return None, None, None, None

    try:
        client = genai.Client(api_key=resolved_key)

        # Renderiza a página em imagem PNG (150 DPI é suficiente para leitura nítida e rápido upload)
        pix = page.get_pixmap(dpi=150)
        image_bytes = pix.tobytes("png")

        prompt = (
            "Você é um especialista em extração de dados de documentos e folhas de frequência/ponto (FIF) brasileiras.\n"
            "Analise esta folha de frequência e identifique:\n"
            "1. O NOME COMPLETO do servidor/funcionário/colaborador dono desta folha específica.\n"
            "2. O número de MATRÍCULA (se houver).\n"
            "3. O CARGO ou FUNÇÃO (se houver).\n"
            "4. O PERÍODO ou MÊS/ANO de referência (ex: SETEMBRO/2026).\n\n"
            "ATENÇÃO:\n"
            "- Não confunda o nome do servidor com nomes de chefias, diretores ou assinaturas de aprovação.\n"
            "- Não retorne textos como 'Intervalo para repouso', 'Poder Legislativo' ou 'Folha de Frequência'.\n"
            "- Responda APENAS em JSON válido no formato:\n"
            '{"nome": "NOME COMPLETO", "matricula": "12345", "cargo": "CARGO", "periodo": "MES/ANO"}'
        )

        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        raw_json = response.text or "{}"
        data = json.loads(raw_json)

        nome = data.get("nome")
        matricula = data.get("matricula")
        cargo = data.get("cargo")
        periodo = data.get("periodo")

        if nome:
            nome = str(nome).strip()
            # Limpa prefixos acidentais
            nome = re.sub(r"^(?:Nome\s*:\s*|Servidor\s*:\s*)", "", nome, flags=re.I).strip()
            # Formatação de caixa em português
            words = nome.split()
            formatted = []
            for i, w in enumerate(words):
                if i > 0 and w.lower() in {"e", "de", "da", "do", "das", "dos"}:
                    formatted.append(w.lower())
                else:
                    formatted.append(w.capitalize())
            nome = " ".join(formatted)

        if matricula:
            matricula = re.sub(r"[^\d]", "", str(matricula)).strip() or None

        return nome or None, matricula, cargo or None, periodo or None

    except Exception as exc:
        logger.warning(f"Erro ao consultar API do Gemini: {exc}")
        return None, None, None, None
