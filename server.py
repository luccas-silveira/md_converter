from pathlib import Path
import tempfile
import traceback
import logging

from flask import Flask, request, send_file, abort, jsonify

from md_to_pdf import md_to_pdf

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(APP_ROOT), static_url_path="")


@app.route("/")
def index():
    # Serve the frontend
    return app.send_static_file("front.html")


@app.route("/convert-md", methods=["POST"])
def convert_md():
    try:
        logger.info("=== INICIO DA CONVERSÃO ===")
        
        uploaded = request.files.get("file")
        if not uploaded:
            logger.error("Nenhum arquivo enviado")
            abort(400, "Nenhum arquivo enviado")

        filename = Path(uploaded.filename or "document.md").name
        logger.info(f"Arquivo recebido: {filename}")
        
        if not filename.lower().endswith(".md"):
            # Permitimos ainda assim, tratando como markdown
            filename = f"{filename}.md"
            logger.info(f"Arquivo renomeado para: {filename}")

        css_text = request.form.get("css") or None

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
        
        with tempfile.TemporaryDirectory() as tmpdir:
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
                logo_name = Path(logo_file.filename).name
                logo_path = tmpdir_path / logo_name
                logo_file.save(logo_path)
                logger.info(f"Logo salva em: {logo_path}")

            pdf_out = tmpdir_path / (Path(filename).stem + ".pdf")
            logger.info(f"PDF será salvo em: {pdf_out}")
            
            # Verificar se arquivos necessários existem no APP_ROOT
            logo_zoi = APP_ROOT / "logo_zoi.png"
            capa_mockup = APP_ROOT / "capa mockup.jpg"
            logger.info(f"Logo ZOI existe: {logo_zoi.exists()}")
            logger.info(f"Capa mockup existe: {capa_mockup.exists()}")
            logger.info(f"APP_ROOT: {APP_ROOT}")
            logger.info(f"Arquivos em APP_ROOT: {list(APP_ROOT.glob('*'))}")

            # Use o diretório do projeto como base para resolver fonts/ e logo_zoi.png
            logger.info("Iniciando conversão MD -> PDF")
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
            
            # Verificar se o PDF foi criado
            if not pdf_out.exists():
                raise Exception(f"PDF não foi criado em {pdf_out}")
                
            logger.info(f"Tamanho do PDF: {pdf_out.stat().st_size} bytes")

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
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Erro 500: {e}")
    return jsonify({"error": "Erro interno do servidor"}), 500


if __name__ == "__main__":
    # Flask dev server
    app.run(host="127.0.0.1", port=5000, debug=True)
