"""Aplicação Web FastAPI para o PDF FIF."""

from __future__ import annotations

import io
import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymupdf
from dotenv import load_dotenv, set_key
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.gemini_extractor import is_gemini_available
from ..core.models import PageRecord, SplitJobConfig
from ..core.pdf_splitter import analyze_pdf, create_zip_from_results, split_pdf

load_dotenv()
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).parent / "static"
SESSIONS_DIR = ROOT_DIR / "saida" / ".web_sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_BASE_DIR = ROOT_DIR / "saida"
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PDF FIF Web", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache de sessões em memória
# session_id -> { "pdf_path": Path, "total_pages": int, "pages": list[PageRecord], "out_dir": Path, "zip_path": Path }
SESSIONS: Dict[str, Dict[str, Any]] = {}


class PageUpdateModel(BaseModel):
    page_num: int
    nome: str
    matricula: Optional[str] = None
    cargo: Optional[str] = None


class FileGroupModel(BaseModel):
    person_name: str
    page_numbers: List[int]
    matricula: Optional[str] = None
    cargo: Optional[str] = None


class SplitRequestModel(BaseModel):
    template: str = "{prefixo}{nome}.pdf"
    prefixo: Optional[str] = None
    ano: Optional[str] = None
    mes: Optional[str] = None
    mode: str = "one_per_page"
    pages: Optional[List[PageUpdateModel]] = None
    groups: Optional[List[FileGroupModel]] = None


class SettingsModel(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = "gemini-2.5-flash"


@app.get("/api/status")
def get_status():
    """Retorna o status do sistema e motores de extração."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    has_gemini = is_gemini_available(api_key)
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else ("Configurada" if has_gemini else "Não configurada")

    has_tesseract = shutil.which("tesseract") is not None

    return {
        "gemini": {
            "available": has_gemini,
            "masked_key": masked_key,
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        },
        "ocr_local": {
            "tesseract": has_tesseract,
            "status": "Pronto (OCR Direcionado e Texto Vetorial)",
        },
        "output_dir": str(OUTPUT_BASE_DIR.resolve()),
    }


@app.post("/api/settings")
def update_settings(settings: SettingsModel):
    """Atualiza as configurações (ex: chave da API Gemini)."""
    env_file = ROOT_DIR / ".env"
    if not env_file.exists():
        env_file.touch()

    if settings.gemini_api_key is not None:
        key = settings.gemini_api_key.strip()
        os.environ["GEMINI_API_KEY"] = key
        set_key(str(env_file), "GEMINI_API_KEY", key)

    if settings.gemini_model is not None:
        model = settings.gemini_model.strip()
        os.environ["GEMINI_MODEL"] = model
        set_key(str(env_file), "GEMINI_MODEL", model)

    return {"status": "ok", "message": "Configurações salvas com sucesso!"}


@app.get("/api/available-uploads")
def list_available_uploads():
    """Lista arquivos PDF disponíveis na pasta upload/."""
    upload_dir = ROOT_DIR / "upload"
    if not upload_dir.exists():
        return {"files": []}
    files = [f.name for f in sorted(upload_dir.glob("*.pdf"))]
    return {"files": files}


@app.post("/api/load-upload/{filename}")
def load_from_upload(filename: str):
    """Cria uma sessão diretamente a partir de um PDF da pasta upload/."""
    upload_dir = ROOT_DIR / "upload"
    source_pdf = upload_dir / filename

    if not source_pdf.exists() or source_pdf.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado na pasta upload/.")

    session_id = str(uuid.uuid4())[:8]
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    dest_pdf = session_dir / filename
    shutil.copy2(source_pdf, dest_pdf)

    try:
        doc = pymupdf.open(dest_pdf)
        total_pages = len(doc)
        doc.close()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Arquivo PDF inválido: {exc}")

    SESSIONS[session_id] = {
        "pdf_path": dest_pdf,
        "filename": filename,
        "total_pages": total_pages,
        "session_dir": session_dir,
        "pages": [],
    }

    return {
        "session_id": session_id,
        "filename": filename,
        "total_pages": total_pages,
    }


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Recebe um PDF e cria uma sessão."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    session_id = str(uuid.uuid4())[:8]
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = session_dir / file.filename
    content = await file.read()
    pdf_path.write_bytes(content)

    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        doc.close()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Arquivo PDF inválido: {exc}")

    SESSIONS[session_id] = {
        "pdf_path": pdf_path,
        "filename": file.filename,
        "total_pages": total_pages,
        "session_dir": session_dir,
        "pages": [],
    }

    return {
        "session_id": session_id,
        "filename": file.filename,
        "total_pages": total_pages,
    }


@app.post("/api/analyze/{session_id}")
def analyze_session(session_id: str, use_gemini: bool = True):
    """Analisa as páginas do PDF da sessão e detecta os nomes."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    pdf_path: Path = session["pdf_path"]
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        records = analyze_pdf(
            pdf_path,
            api_key=api_key,
            use_gemini=use_gemini,
        )
        session["pages"] = records

        return {
            "session_id": session_id,
            "total_pages": len(records),
            "pages": [
                {
                    "page_num": r.page_num,
                    "nome": r.nome,
                    "matricula": r.matricula,
                    "cargo": r.cargo,
                    "source": r.source,
                    "confidence": r.confidence,
                }
                for r in records
            ],
        }
    except Exception as exc:
        logger.exception("Erro ao analisar PDF")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {exc}")


@app.get("/api/thumbnail/{session_id}/{page_num}")
def get_thumbnail(session_id: str, page_num: int):
    """Gera miniatura visual de uma página do PDF."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    pdf_path: Path = session["pdf_path"]
    thumb_path = session["session_dir"] / f"thumb_{page_num}.png"

    if thumb_path.exists():
        return FileResponse(thumb_path, media_type="image/png")

    try:
        doc = pymupdf.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            doc.close()
            raise HTTPException(status_code=404, detail="Página inválida.")

        page = doc[page_num - 1]
        # 100 DPI é ideal para miniatura nítida e leve
        pix = page.get_pixmap(dpi=100)
        pix.save(thumb_path)
        doc.close()

        return FileResponse(thumb_path, media_type="image/png")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao renderizar miniatura: {exc}")


@app.post("/api/split/{session_id}")
def split_session(session_id: str, payload: SplitRequestModel):
    """Executa a separação das páginas e gera os arquivos PDF e ZIP."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    pdf_path: Path = session["pdf_path"]
    session_dir: Path = session["session_dir"]
    out_dir = OUTPUT_BASE_DIR / f"{pdf_path.stem}_{session_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prepara os PageRecords atualizados (caso o usuário tenha editado algum nome na UI)
    page_records = []
    if payload.pages:
        for p in payload.pages:
            page_records.append(
                PageRecord(
                    page_num=p.page_num,
                    nome=p.nome.strip(),
                    matricula=p.matricula,
                    cargo=p.cargo,
                    source="manual",
                )
            )
    else:
        page_records = session.get("pages")

    # Se o usuário enviou agrupamentos manuais de páginas (custom groups)
    custom_groups = None
    if payload.groups:
        custom_groups = [
            (g.person_name.strip(), g.matricula, g.page_numbers)
            for g in payload.groups
            if g.page_numbers
        ]

    config = SplitJobConfig(
        template=payload.template,
        prefixo=payload.prefixo,
        ano=payload.ano,
        mes=payload.mes,
        mode=payload.mode,
    )

    try:
        summary = split_pdf(
            pdf_path,
            out_dir,
            config=config,
            page_records=page_records,
            custom_groups=custom_groups,
        )

        zip_path = out_dir / f"{pdf_path.stem}_separados.zip"
        create_zip_from_results(summary.results, zip_path)

        session["out_dir"] = out_dir
        session["zip_path"] = zip_path
        session["results"] = summary.results

        return {
            "session_id": session_id,
            "total_files": len(summary.results),
            "output_directory": str(out_dir.resolve()),
            "zip_url": f"/api/download/zip/{session_id}",
            "files": [
                {
                    "filename": r.filename,
                    "person_name": r.person_name,
                    "matricula": r.matricula,
                    "page_numbers": r.page_numbers,
                    "download_url": f"/api/download/file/{session_id}/{r.filename}",
                }
                for r in summary.results
            ],
            "warnings": summary.warnings,
        }
    except Exception as exc:
        logger.exception("Erro ao separar PDF")
        raise HTTPException(status_code=500, detail=f"Erro ao separar arquivos: {exc}")


@app.get("/api/download/zip/{session_id}")
def download_zip(session_id: str):
    """Baixa o ZIP com todos os PDFs separados."""
    session = SESSIONS.get(session_id)
    if not session or "zip_path" not in session:
        raise HTTPException(status_code=404, detail="Arquivo ZIP não encontrado.")

    zip_path: Path = session["zip_path"]
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_path.name,
    )


@app.get("/api/download/file/{session_id}/{filename}")
def download_single_file(session_id: str, filename: str):
    """Baixa um PDF individual."""
    session = SESSIONS.get(session_id)
    if not session or "out_dir" not in session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    file_path = session["out_dir"] / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
    )


# Monta arquivos estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>PDF FIF Web iniciado. Arquivo index.html ainda não gerado.</h1>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


def run_web(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """Inicia o servidor web uvicorn e abre o navegador."""
    import uvicorn
    import webbrowser

    resolved_port = int(os.getenv("WEB_PORT", str(port)))
    url = f"http://{host}:{resolved_port}"

    print("\n" + "=" * 60)
    print("  🚀 PDF FIF — Interface Web Moderna Iniciada!")
    print(f"  🌐 Acesse no seu navegador: {url}")
    print("  Pressione Ctrl+C para encerrar o servidor.")
    print("=" * 60 + "\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(app, host=host, port=resolved_port, log_level="info")

