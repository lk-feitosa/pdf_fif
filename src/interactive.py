#!/usr/bin/env python3
"""Modo interativo: coloque o PDF em upload/ e responda no terminal."""

from __future__ import annotations

import sys
from pathlib import Path

from .naming import normalize_template
from .pdf_splitter import split_pdf

UPLOAD_DIR = Path("upload")
OUTPUT_DIR = Path("saida")


def _ensure_dirs(base: Path) -> None:
    (base / UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    (base / OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def _list_pdfs(upload_dir: Path) -> list[Path]:
    return sorted(upload_dir.glob("*.pdf"))


def _choose_pdf(pdfs: list[Path]) -> Path | None:
    if len(pdfs) == 1:
        print(f"\nPDF encontrado: {pdfs[0].name}")
        return pdfs[0]

    print("\nPDFs na pasta upload/:")
    for i, pdf in enumerate(pdfs, start=1):
        print(f"  {i}. {pdf.name}")

    while True:
        choice = input("\nQual PDF processar? (número): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(pdfs):
                return pdfs[index]
        print("Opção inválida. Tente novamente.")


def _ask_template() -> str:
    print("\nUse *nome* onde deve entrar o nome da pessoa.")
    print("Exemplos:")
    print("  2026_08_*nome*_*sobrenome*.pdf  (recomendado: evita nomes duplicados)")
    print("  2026_08_*nome*.pdf")
    print("  freq_*nome_completo*.pdf")
    print("  {ano}_{mes}_{primeiro_nome}_{sobrenome}.pdf  (formato avançado)")

    while True:
        template = input("\nQual padrão para o PDF de saída? ").strip()
        if not template:
            print("Digite um padrão, por exemplo: 2026_08_*nome*.pdf")
            continue
        normalized = normalize_template(template)
        if "{primeiro_nome}" not in normalized and "{nome}" not in normalized:
            print("O padrão precisa ter *nome* (ou *nome_completo*) para identificar cada pessoa.")
            continue
        return template


def run_interactive(base_dir: Path | None = None) -> int:
    base = base_dir or Path.cwd()
    upload_dir = base / UPLOAD_DIR
    output_dir = base / OUTPUT_DIR

    _ensure_dirs(base)

    print("=" * 50)
    print("  PDF FIF — Separador de Frequência")
    print("=" * 50)
    print(f"\n1. Coloque o PDF em: {upload_dir.resolve()}")
    print(f"2. Os arquivos sairão em: {output_dir.resolve()}")

    pdfs = _list_pdfs(upload_dir)
    if not pdfs:
        print(f"\nNenhum PDF em upload/. Copie seu arquivo para lá e rode de novo.")
        print(f"  python main.py")
        return 1

    pdf_path = _choose_pdf(pdfs)
    if pdf_path is None:
        return 1

    template = _ask_template()
    print(f"\nProcessando: {pdf_path.name}")
    print(f"Padrão: {template}")
    print("Aguarde...\n")

    try:
        summary = split_pdf(
            pdf_path,
            output_dir,
            template=template,
        )
    except Exception as exc:
        print(f"Erro ao processar: {exc}")
        return 1

    for warning in summary.warnings:
        print(f"  ⚠ {warning}")

    for item in summary.results:
        pages = ", ".join(str(p) for p in item.page_numbers)
        print(f"  ✓ {item.filename}  ({item.person_name}, págs. {pages})")

    print(f"\nConcluído: {len(summary.results)} PDF(s) em {output_dir.resolve()}")
    return 0


def main() -> int:
    return run_interactive()


if __name__ == "__main__":
    sys.exit(main())
