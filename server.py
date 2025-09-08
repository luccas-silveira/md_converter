from pathlib import Path
import tempfile

from flask import Flask, request, send_file, abort

from md_to_pdf import md_to_pdf

APP_ROOT = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(APP_ROOT), static_url_path="")


@app.route("/")
def index():
    # Serve the frontend
    return app.send_static_file("front.html")


@app.post("/convert-md")
def convert_md():
    uploaded = request.files.get("file")
    if not uploaded:
        abort(400, "Nenhum arquivo enviado")

    filename = Path(uploaded.filename or "document.md").name
    if not filename.lower().endswith(".md"):
        # Permitimos ainda assim, tratando como markdown
        filename = f"{filename}.md"

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

    logo_file = request.files.get("logo")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        md_path = tmpdir_path / filename
        uploaded.save(md_path)

        logo_path = None
        if logo_file and logo_file.filename:
            logo_name = Path(logo_file.filename).name
            logo_path = tmpdir_path / logo_name
            logo_file.save(logo_path)

        pdf_out = tmpdir_path / (Path(filename).stem + ".pdf")

        # Use o diretório do projeto como base para resolver fonts/ e logo_zoi.png
        md_to_pdf(
            str(md_path),
            str(pdf_out),
            css_style=css_text,
            logo_path=str(logo_path) if logo_path else None,
            base_dir=str(APP_ROOT),
            cover_data=cover_data,
            cover_template_path=None,
        )

        return send_file(
            pdf_out,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=Path(filename).with_suffix(".pdf").name,
        )


if __name__ == "__main__":
    # Flask dev server
    app.run(host="127.0.0.1", port=5000, debug=True)
