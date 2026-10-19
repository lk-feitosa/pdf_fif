#!/usr/bin/env python3
"""Bot Telegram para separar PDFs de frequência."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .naming import default_template, normalize_template
from .pdf_splitter import create_zip_from_results, split_pdf

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HELP_TEXT = """
📄 *PDF FIF — Separador de Frequência*

Envie um PDF com várias folhas de frequência e receba os arquivos separados por pessoa.

*Comandos:*
/start — Mostra esta ajuda
/config — Ver configuração atual
/ano 2026 — Define o ano nos nomes
/mes 08 — Define o mês nos nomes
/formato `2026_08_*nome*.pdf` — Define o padrão do nome

*Placeholders:*
`*nome*` ou `{primeiro_nome}` — primeiro nome
`*nome_completo*` ou `{nome}` — nome completo
`*sobrenome*` `{ano}` `{mes}` `{pagina}`

*Como usar:*
1. Configure ano, mês e formato (opcional)
2. Envie o PDF como documento
3. Receba um ZIP com os PDFs separados

*Exemplo de nome gerado:*
`2026_08_joao.pdf`
""".strip()


def _user_config(context: ContextTypes.DEFAULT_TYPE) -> dict:
    if "config" not in context.user_data:
        context.user_data["config"] = {
            "template": default_template(),
            "ano": None,
            "mes": None,
        }
    return context.user_data["config"]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = _user_config(context)
    text = (
        "⚙️ *Configuração atual:*\n\n"
        f"Ano: `{cfg['ano'] or 'automático (atual)'}`\n"
        f"Mês: `{cfg['mes'] or 'automático (atual)'}`\n"
        f"Formato: `{cfg['template']}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_ano(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /ano 2026")
        return
    cfg = _user_config(context)
    cfg["ano"] = context.args[0]
    await update.message.reply_text(f"✓ Ano definido: {cfg['ano']}")


async def cmd_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /mes 08")
        return
    cfg = _user_config(context)
    cfg["mes"] = context.args[0]
    await update.message.reply_text(f"✓ Mês definido: {cfg['mes']}")


async def cmd_formato(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Uso: /formato 2026_08_{primeiro_nome}.pdf\n\n"
            "Placeholders: {ano} {mes} {nome} {primeiro_nome} {sobrenome} {pagina}"
        )
        return
    cfg = _user_config(context)
    cfg["template"] = normalize_template(" ".join(context.args))
    await update.message.reply_text(f"✓ Formato definido:\n`{cfg['template']}`", parse_mode="Markdown")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    document = message.document

    if not document.file_name or not document.file_name.lower().endswith(".pdf"):
        await message.reply_text("Envie um arquivo PDF (.pdf).")
        return

    cfg = _user_config(context)
    status = await message.reply_text("⏳ Processando PDF...")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        input_pdf = tmp_path / document.file_name
        output_dir = tmp_path / "saida"
        zip_path = tmp_path / "frequencias_separadas.zip"

        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(input_pdf)

        try:
            summary = split_pdf(
                input_pdf,
                output_dir,
                template=cfg["template"],
                ano=cfg["ano"],
                mes=cfg["mes"],
            )
        except Exception as exc:
            logger.exception("Erro ao processar PDF")
            await status.edit_text(f"❌ Erro ao processar: {exc}")
            return

        if not summary.results:
            await status.edit_text("❌ Nenhuma página encontrada no PDF.")
            return

        create_zip_from_results(summary.results, zip_path)

        lines = [f"✅ *{len(summary.results)} PDF(s) gerado(s):*\n"]
        for item in summary.results:
            lines.append(f"• `{item.filename}` — {item.person_name}")

        if summary.warnings:
            lines.append(f"\n⚠️ {len(summary.warnings)} aviso(s) (nome não detectado em alguma página).")

        await status.edit_text("\n".join(lines), parse_mode="Markdown")

        with zip_path.open("rb") as f:
            await message.reply_document(
                document=f,
                filename=zip_path.name,
                caption="📦 PDFs separados por pessoa",
            )


def _build_application(token: str) -> Application:
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        httpx_kwargs={"trust_env": False},
    )
    return Application.builder().token(token).request(request).build()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "seu_token_aqui":
        raise SystemExit(
            "Defina TELEGRAM_BOT_TOKEN no arquivo .env\n"
            "Copie .env.example para .env e coloque seu token do @BotFather."
        )

    try:
        app = _build_application(token)
    except Exception as exc:
        raise SystemExit(f"Erro ao iniciar bot: {exc}") from exc
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("config", cmd_config))
    app.add_handler(CommandHandler("ano", cmd_ano))
    app.add_handler(CommandHandler("mes", cmd_mes))
    app.add_handler(CommandHandler("formato", cmd_formato))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))

    logger.info("Bot iniciado. Aguardando mensagens...")
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as exc:
        msg = str(exc)
        if "Proxy" in msg or "403" in msg:
            raise SystemExit(
                "Erro de rede/proxy ao conectar ao Telegram.\n"
                "Tente desativar VPN/proxy ou rode:\n"
                "  NO_PROXY='*' python run_bot.py"
            ) from exc
        raise


if __name__ == "__main__":
    main()
