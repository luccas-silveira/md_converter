"""
Rotas para conversão de Markdown para PDF
"""

from flask import Blueprint, request, send_file, abort, jsonify, current_app
from pathlib import Path
import tempfile
import traceback
import logging
import uuid
from werkzeug.utils import secure_filename

from app.utils.md_to_pdf import md_to_pdf
from app.routes.progress import update_progress
from app.utils.file_security import sanitize_filename

conversion_bp = Blueprint('conversion', __name__)
logger = logging.getLogger(__name__)

# Get application root
APP_ROOT = Path(__file__).resolve().parent.parent.parent


@conversion_bp.route("/convert-md", methods=["POST"])
def convert_md():
    session_id = request.form.get('session_id', str(uuid.uuid4()))
    try:
        logger.info("=== INICIO DA CONVERSÃO ===")
        update_progress(session_id, 5, "Iniciando conversão...")

        uploaded = request.files.get("file")
        if not uploaded:
            logger.error("Nenhum arquivo enviado")
            abort(400, "Nenhum arquivo enviado")

        # Sanitizar nome do arquivo para prevenir path traversal
        try:
            filename = sanitize_filename(
                uploaded.filename,
                default_extension='.md',
                max_length=200
            )
        except ValueError as e:
            logger.error(f"Erro ao sanitizar filename: {e}")
            abort(400, "Nome de arquivo inválido")

        logger.info(f"Arquivo recebido (sanitizado): {filename}")
        logger.info(f"Tipo de conteúdo: {uploaded.content_type}")
        update_progress(session_id, 15, "Processando arquivo...")

        if not filename.lower().endswith(".md"):
            # Permitimos ainda assim, tratando como markdown
            filename = f"{filename}.md"
            logger.info(f"Arquivo renomeado para: {filename}")

        css_text = request.form.get("css") or None
        update_progress(session_id, 25, "Preparando configurações...")

        # Dados da capa vindos do formulário do front-end
        cover_data = {
            'topo_direito_email': request.form.get('cover_top_email', ''),
            'topo_direito_site': request.form.get('cover_top_site', ''),
            'representante_label': request.form.get('cover_rep_label', ''),
            'representante_nome': request.form.get('cover_rep_nome', ''),
            'subtitulo': request.form.get('cover_subtitulo', ''),
            'descricao': request.form.get('cover_descricao', ''),
            'preparado_nome': request.form.get('cover_prep_nome', ''),
            'preparado_email': request.form.get('cover_prep_email', ''),
            'preparado_phone': request.form.get('cover_prep_phone', ''),
            'data': request.form.get('cover_data', ''),
        }

        logger.info(f"Cover data: {cover_data}")

        logo_file = request.files.get("logo")

        # Usar diretório de upload configurável (persistente em produção)
        upload_base = current_app.config.get('UPLOAD_FOLDER', '/tmp')
        with tempfile.TemporaryDirectory(dir=upload_base) as tmpdir:
            tmpdir_path = Path(tmpdir)
            logger.info(f"Diretório temporário: {tmpdir_path}")

            md_path = tmpdir_path / filename
            uploaded.save(md_path)
            logger.info(f"Arquivo salvo em: {md_path}")

            # Verificar se o arquivo foi salvo corretamente
            if not md_path.exists():
                raise Exception(f"Falha ao salvar arquivo em {md_path}")

            with open(md_path, 'r', encoding='utf-8') as f:
                content_preview = f.read()[:200]
                logger.info(f"Conteúdo do arquivo (primeiros 200 chars): {content_preview}")

            logo_path = None
            if logo_file and logo_file.filename:
                # Sanitizar nome do arquivo do logo
                try:
                    logo_name = sanitize_filename(
                        logo_file.filename,
                        max_length=100
                    )
                except ValueError as e:
                    logger.warning(f"Logo filename inválido, ignorando logo: {e}")
                    logo_name = None

                if logo_name:
                    logo_path = tmpdir_path / logo_name
                    logo_file.save(logo_path)
                    logger.info(f"Logo salva em: {logo_path}")

            pdf_out = tmpdir_path / (Path(filename).stem + ".pdf")
            logger.info(f"PDF será salvo em: {pdf_out}")

            # Verificar se arquivos necessários existem no APP_ROOT
            logo_zoi = APP_ROOT / "assets" / "images" / "logo_zoi.png"
            capa_mockup = APP_ROOT / "assets" / "images" / "capa mockup.jpg"
            logger.info(f"Logo ZOI existe: {logo_zoi.exists()}")
            logger.info(f"Capa mockup existe: {capa_mockup.exists()}")

            # Use o diretório do projeto como base para resolver fonts/ e logo_zoi.png
            logger.info("Iniciando conversão MD -> PDF")
            update_progress(session_id, 60, "Convertendo para PDF...")
            md_to_pdf(
                str(md_path),
                str(pdf_out),
                css_style=css_text,
                logo_path=str(logo_path) if logo_path else None,
                base_dir=str(APP_ROOT),
                cover_data=cover_data,
                cover_template_path=None,
            )

            logger.info("Conversão concluída com sucesso")
            update_progress(session_id, 90, "Finalizando...")

            # Verificar se o PDF foi criado
            if not pdf_out.exists():
                raise Exception(f"PDF não foi criado em {pdf_out}")

            logger.info(f"Tamanho do PDF: {pdf_out.stat().st_size} bytes")
            update_progress(session_id, 100, "Concluído!")

            return send_file(
                pdf_out,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=Path(filename).with_suffix(".pdf").name,
            )

    except Exception as e:
        logger.error(f"ERRO DURANTE CONVERSÃO: {str(e)}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return jsonify({
            "error": "Erro interno durante a conversão"
        }), 500
