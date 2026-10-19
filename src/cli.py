#!/usr/bin/env python3
"""CLI para separar PDFs de frequência localmente."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .naming import default_template
from .pdf_splitter import split_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Separa PDF de frequência em arquivos individuais por pessoa.",
    )
    parser.add_argument(
        "entrada",
        type=Path,
        help="Arquivo PDF ou pasta contendo PDFs",
    )
    parser.add_argument(
        "-o",
        "--saida",
        type=Path,
        default=Path("saida"),
        help="Pasta de destino (padrão: ./saida)",
    )
    parser.add_argument(
        "-t",
        "--template",
        default=default_template(),
        help=(
            "Modelo do nome do arquivo. Placeholders: {ano} {mes} {nome} "
            "{primeiro_nome} {sobrenome} {pagina}. "
            'Exemplo: "2026_08_{primeiro_nome}.pdf"'
        ),
    )
    parser.add_argument("--ano", help="Ano para o nome do arquivo (ex: 2026)")
    parser.add_argument("--mes", help="Mês para o nome do arquivo (ex: 08)")
    parser.add_argument(
        "-p",
        "--prefixo",
        help="Prefixo a adicionar antes do nome (ex: '2026_07_' ou 'FIF_')",
    )
    return parser


def _collect_pdfs(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            raise SystemExit(f"Arquivo não é PDF: {path}")
        return [path]
    if path.is_dir():
        pdfs = sorted(path.glob("*.pdf"))
        if not pdfs:
            raise SystemExit(f"Nenhum PDF encontrado em: {path}")
        return pdfs
    raise SystemExit(f"Caminho não encontrado: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    pdfs = _collect_pdfs(args.entrada)
    total_files = 0

    for pdf_path in pdfs:
        out_dir = args.saida / pdf_path.stem if len(pdfs) > 1 else args.saida
        print(f"\nProcessando: {pdf_path.name}")
        summary = split_pdf(
            pdf_path,
            out_dir,
            template=args.template,
            prefixo=args.prefixo,
            ano=args.ano,
            mes=args.mes,
        )

        for warning in summary.warnings:
            print(f"  ⚠ {warning}")

        for item in summary.results:
            pages = ", ".join(str(p) for p in item.page_numbers)
            print(f"  ✓ {item.filename}  ({item.person_name}, págs. {pages})")
            total_files += 1

        print(f"  → {len(summary.results)} arquivo(s) em {out_dir}")

    print(f"\nConcluído: {total_files} PDF(s) gerado(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
