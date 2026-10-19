"""Teste básico com PDF sintético."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.name_extractor import extract_name_from_text
from src.pdf_splitter import split_pdf


def _make_sample_pdf(path: Path) -> None:
    doc = pymupdf.open()
    people = [
        ("Nome: MARIA DA SILVA SANTOS\nFolha de Frequência - Agosto/2026", "Maria"),
        ("Funcionário: JOÃO PEREIRA LIMA\nMatrícula: 12345", "João"),
        ("Servidor: ANA CAROLINA SOUZA\nCPF: 000.000.000-00", "Ana"),
    ]
    for text, _ in people:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    doc.save(path)
    doc.close()


def test_extract_names() -> None:
    assert extract_name_from_text("Nome: MARIA DA SILVA\nCargo: Analista") == "Maria Da Silva"
    assert extract_name_from_text("Funcionário: JOÃO PEREIRA") == "João Pereira"


def test_normalize_template() -> None:
    from src.naming import normalize_template

    assert normalize_template("2026_08_*nome*.pdf") == "2026_08_{primeiro_nome}.pdf"
    assert normalize_template("*nome_completo*.pdf") == "{nome}.pdf"


def test_split_pdf() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "sample.pdf"
        out_dir = Path(tmp) / "out"
        _make_sample_pdf(pdf_path)

        summary = split_pdf(
            pdf_path,
            out_dir,
            template="2026_08_{primeiro_nome}.pdf",
            ano="2026",
            mes="08",
        )

        assert len(summary.results) == 3
        names = {r.filename for r in summary.results}
        assert "2026_08_maria.pdf" in names
        assert "2026_08_joao.pdf" in names
        assert "2026_08_ana.pdf" in names


if __name__ == "__main__":
    test_extract_names()
    test_normalize_template()
    test_split_pdf()
    print("OK — todos os testes passaram.")
