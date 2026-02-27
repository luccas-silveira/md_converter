import html
import markdown2
import os
from weasyprint import HTML
import argparse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def normalize_markdown_content(content):
    """
    Normaliza o conteúdo markdown para garantir formatação correta.

    Corrige problemas como:
    - Títulos sem linha em branco antes
    - Múltiplos títulos consecutivos
    """
    lines = content.split('\n')
    normalized_lines = []

    for i, line in enumerate(lines):
        # Se a linha atual é um título (começa com #)
        if line.strip().startswith('#'):
            # Se não é a primeira linha e a linha anterior não está vazia
            if i > 0 and lines[i-1].strip() != '':
                # Adiciona uma linha em branco antes do título
                normalized_lines.append('')
            normalized_lines.append(line)
        else:
            normalized_lines.append(line)

    return '\n'.join(normalized_lines)

def md_to_pdf(md_file_path, pdf_file_path=None, css_style=None, logo_path=None, base_dir=None, cover_data=None, cover_template_path=None):
    """
    Converte um arquivo Markdown para PDF.

    Args:
        md_file_path (str): Caminho do arquivo Markdown de entrada
        pdf_file_path (str): Caminho do arquivo PDF de saída (opcional)
        css_style (str): CSS personalizado para estilização (opcional)
        logo_path (str): Caminho para imagem da logo a exibir no rodapé (opcional). Se não informado, tenta usar 'logo_zoi.png' ao lado do .md ou no diretório base.
        base_dir (str|Path): Diretório base para recursos (imagens, fonts/). Se None, usa o diretório do arquivo .md.
        cover_data (dict): Dados para a capa (ex.: subtitulo, descricao, topo_direito_email, topo_direito_site, representante_nome, preparado_nome, preparado_email, preparado_phone, data).
        cover_template_path (str): Caminho para a imagem da capa em branco (mockup). Se None, tenta localizar automaticamente.

    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Verificar se o arquivo existe
    if not os.path.exists(md_file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {md_file_path}")

    # Definir o nome do arquivo PDF de saída se não fornecido
    if pdf_file_path is None:
        pdf_file_path = Path(md_file_path).with_suffix('.pdf')

    # Diretório base para resolução de recursos
    resolved_base_dir = Path(base_dir).resolve() if base_dir else Path(md_file_path).resolve().parent

    # Se logo não for informada, tentar logo_zoi.png ao lado do .md e no assets/images
    if logo_path is None:
        candidates = [
            Path(md_file_path).with_name('logo_zoi.png'),
            resolved_base_dir / 'assets' / 'images' / 'logo_zoi.png',
            resolved_base_dir / 'logo_zoi.png',  # fallback para compatibilidade
        ]
        for cand in candidates:
            if cand.exists():
                logo_path = str(cand)
                break

    # Ler o conteúdo do arquivo Markdown
    with open(md_file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()

    # Normalizar o conteúdo markdown (garantir quebras de linha corretas)
    md_content = normalize_markdown_content(md_content)

    # Converter Markdown para HTML com extensões úteis
    html_content = markdown2.markdown(
        md_content,
        extras=[
            'tables',           # Suporte para tabelas
            'fenced-code-blocks',  # Blocos de código com ```
            'header-ids',       # IDs automáticos para headers
            'strike',           # Texto riscado
            'task_list',        # Listas de tarefas [ ] [x]
            'footnotes',        # Notas de rodapé
            'smarty-pants',     # Tipografia inteligente
            'code-friendly',    # Melhor suporte para código
        ]
    )

    # ── CSS alinhado ao ZOI Design System ──
    # Tokens: --green-400: #b5ff81, --green-500: #90cc67, --green-900: #364c26
    #         --neutral-0: #fff, --neutral-50: #f7fff2, --neutral-100: #e7e7e7
    #         --neutral-200: #ccc, --neutral-500: #808080, --neutral-600: #5c5c5c
    #         --neutral-800: #333, --neutral-900: #141414
    default_css = """
    @page {
        size: A4;
        margin: 2cm 2.2cm;
        @bottom-left {
            content: element(footer-left);
        }
        @bottom-right {
            content: counter(page);
            color: #808080;
            font-size: 9px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
    }

    /* Página de capa (sem margens e sem rodapé) */
    @page cover {
        size: A4;
        margin: 0;
        @bottom-left { content: none; }
        @bottom-right { content: none; }
    }
    .cover-page {
        page: cover;
        position: relative;
        width: 210mm;
        height: 297mm;
        overflow: hidden;
    }
    .cover-bg {
        position: absolute;
        inset: 0;
        width: 210mm;
        height: 297mm;
        object-fit: contain;
        object-position: -5mm 0;
        display: block;
    }
    /* Bloco de contatos no topo direito */
    .cover-top-right {
        position: absolute; top: 30mm; right: 22mm; width: 75mm;
        color: #333333; font-size: 10pt; line-height: 1.35; text-align: left;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .cover-top-right .label { color: #333333; font-weight: 600; }
    /* Subtítulo abaixo do "Relatório" no mockup */
    .cover-title-sub {
        position: absolute; left: 26mm; top: 126mm; width: 120mm;
        color: #141414; font-size: 16pt; font-weight: 600; line-height: 1.2; text-align: left; margin: 0;
        font-family: 'Clash Display', -apple-system, sans-serif;
    }
    .cover-desc {
        position: absolute; left: 26mm; top: 134mm; width: 120mm;
        color: #5c5c5c; font-size: 10.5pt; line-height: 1.35; text-align: left; margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    /* Blocos na faixa verde inferior */
    .cover-prep {
        position: absolute; left: 14mm; bottom: 39mm; width: 120mm;
        color: #141414; text-align: left;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .cover-prep .name {
        display: block; margin-top: 2mm; font-size: 13pt; font-weight: 700; color: #141414;
        font-family: 'Clash Display', -apple-system, sans-serif;
    }
    .cover-prep .contact {
        margin-top: 1mm; color: #333333; font-size: 10.5pt;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .cover-date {
        position: absolute; right: 72mm; bottom: 49mm; width: 40mm;
        color: #141414; font-size: 11pt; text-align: left;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.5;
        color: #333333;
        max-width: 100%;
        margin: 0 auto;
        padding: 20px;
        font-size: 10.5pt;
    }

    /* Títulos — Clash Display, badge verde arredondado */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Clash Display', -apple-system, sans-serif;
        background-color: #b5ff81;
        color: #141414;
        display: inline-block;
        padding: 5px 14px;
        border-radius: 12px;
        border: none;
        margin-top: 28px;
        margin-bottom: 12px;
        font-weight: 500;
        line-height: 1.1;
        page-break-inside: avoid;
        page-break-after: avoid;
    }

    h1 { font-size: 1.75em; }
    h2 { font-size: 1.35em; }
    h3 { font-size: 1.15em; }
    h4 { font-size: 1em; }

    /* Garantir que conteúdo segue o título na mesma página */
    h1 + *, h2 + *, h3 + * {
        page-break-before: avoid;
    }

    p {
        margin-top: 0;
        margin-bottom: 12px;
        orphans: 3;
        widows: 3;
    }

    strong { color: #141414; }

    code {
        background-color: #f7fff2;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.88em;
        font-weight: 500;
        color: #364c26;
    }

    pre {
        background-color: #141414;
        color: #b5ff81;
        padding: 16px 20px;
        border-radius: 12px;
        overflow-x: auto;
        line-height: 1.5;
        font-size: 0.85em;
        page-break-inside: avoid;
    }

    pre code {
        background-color: transparent;
        padding: 0;
        color: inherit;
    }

    blockquote {
        border-left: 3px solid #b5ff81;
        padding: 8px 16px;
        margin: 16px 0;
        background: #f7fff2;
        border-radius: 0 8px 8px 0;
        color: #5c5c5c;
        font-style: italic;
    }

    blockquote p { margin-bottom: 4px; }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
        font-size: 0.92em;
        page-break-inside: avoid;
    }

    table th,
    table td {
        border: 1px solid #e7e7e7;
        padding: 8px 12px;
        text-align: left;
    }

    table th {
        background-color: #141414;
        color: #ffffff;
        font-weight: 600;
        font-family: 'Clash Display', -apple-system, sans-serif;
        font-size: 0.92em;
    }

    table tr:nth-child(even) {
        background-color: #f7fff2;
    }

    ul, ol {
        margin: 12px 0;
        padding-left: 2em;
    }

    li {
        margin: 4px 0;
        line-height: 1.5;
    }

    a {
        color: #364c26;
        text-decoration: underline;
        text-decoration-color: #b5ff81;
        text-underline-offset: 2px;
    }

    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 16px auto;
        border-radius: 8px;
    }

    hr {
        border: none;
        border-top: 2px solid #e7e7e7;
        margin: 28px 0;
    }

    .footnote {
        font-size: 0.85em;
        color: #808080;
    }

    .task-list-item {
        list-style-type: none;
        margin-left: -1.5em;
    }

    .task-list-item input {
        margin-right: 0.5em;
    }

    /* Rodapé com logo no canto inferior esquerdo */
    .footer-left {
        position: running(footer-left);
    }

    .footer-left img {
        height: 30px;
        margin: 0;
        padding-right: 50mm;
        display: inline-block;
    }
    """

    # Usar CSS padrão e, se houver, anexar CSS personalizado para sobrescrever o padrão
    css_to_use = f"{default_css}\n{css_style}" if css_style else default_css

    # Fonte customizada: procurar arquivos na pasta 'assets/fonts/' no diretório base
    fonts_dir = resolved_base_dir / 'assets' / 'fonts'

    def _find_font(search_dir: Path, name_candidates):
        if not search_dir.is_dir():
            return None
        exts = ['.woff2', '.woff', '.ttf', '.otf']
        files = list(search_dir.glob('*'))
        for cand in name_candidates:
            cand_lower = cand.lower()
            for f in files:
                if not f.is_file():
                    continue
                if f.suffix.lower() in exts and cand_lower in f.stem.lower():
                    return f.name
        return None

    clash_file = _find_font(fonts_dir, ['clash'])
    satoshi_file = _find_font(fonts_dir, ['satoshi'])

    fonts_css_parts = []
    if clash_file:
        fonts_css_parts.append(
            f"""
            @font-face {{
                font-family: 'Clash Display';
                src: url('assets/fonts/{clash_file}');
                font-weight: 400 700;
                font-style: normal;
            }}
            """
        )
    if satoshi_file:
        fonts_css_parts.append(
            f"""
            @font-face {{
                font-family: 'Satoshi';
                src: url('assets/fonts/{satoshi_file}');
                font-weight: 400 700;
                font-style: normal;
            }}
            """
        )

    if fonts_css_parts:
        # Clash Display nos títulos, Satoshi/system no corpo
        body_font = "'Satoshi', " if satoshi_file else ""
        fonts_css_parts.append(
            f"""
            body {{ font-family: {body_font}-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            h1, h2, h3, h4, h5, h6 {{ font-family: 'Clash Display', {body_font}-apple-system, sans-serif; }}
            """
        )
        css_to_use = f"{css_to_use}\n{''.join(fonts_css_parts)}"

    # Elemento de rodapé (logo) como running element para @page @bottom-left
    footer_logo_html = f"<div class=\"footer-left\"><img src=\"{html.escape(logo_path)}\" alt=\"logo\"></div>" if logo_path else ""

    # Construir capa, se houver template
    def _find_cover_template():
        if cover_template_path and Path(cover_template_path).exists():
            return str(cover_template_path)
        candidates = [
            resolved_base_dir / 'assets' / 'images' / 'capa mockup.jpg',
            resolved_base_dir / 'assets' / 'images' / 'capa_mockup.jpg',
            resolved_base_dir / 'assets' / 'images' / 'capa-mockup.jpg',
            resolved_base_dir / 'assets' / 'images' / 'capa.png',
            resolved_base_dir / 'assets' / 'images' / 'capa.jpg',
            # Fallbacks para compatibilidade
            resolved_base_dir / 'capa mockup.jpg',
            resolved_base_dir / 'capa_mockup.jpg',
            resolved_base_dir / 'capa-mockup.jpg',
            resolved_base_dir / 'capa.png',
            resolved_base_dir / 'capa.jpg',
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return None

    cover_template = _find_cover_template()

    cover_html = ""
    if cover_template:
        cd = cover_data or {}
        top_email = html.escape(cd.get('topo_direito_email', ''))
        top_site = html.escape(cd.get('topo_direito_site', ''))
        rep_label = ''
        rep_nome = html.escape(cd.get('representante_nome', ''))
        subtitulo = html.escape(cd.get('subtitulo', ''))
        descricao = html.escape(cd.get('descricao', ''))
        prep_nome = html.escape(cd.get('preparado_nome', ''))
        prep_email = html.escape(cd.get('preparado_email', ''))
        prep_phone = html.escape(cd.get('preparado_phone', ''))
        data_text = html.escape(cd.get('data', ''))
        escaped_cover_src = html.escape(cover_template)
        rep_label_html = ""

        cover_html = f"""
        <section class=\"cover-page\">
            <img class=\"cover-bg\" src=\"{escaped_cover_src}\" alt=\"Capa\" />
            <div class=\"cover-top-right\">
                <div>{top_email}</div>
                <div>{top_site}</div>
                {rep_label_html}
                <div>{rep_nome}</div>
            </div>
            <div class=\"cover-title-sub\">{subtitulo}</div>
            <div class=\"cover-desc\">{descricao}</div>
            <div class=\"cover-prep\">
                <span class=\"name\">{prep_nome}</span>
                <div class=\"contact\">{prep_email}</div>
                <div class=\"contact\">{prep_phone}</div>
            </div>
            <div class=\"cover-date\">{data_text}</div>
        </section>
        <div style=\"page-break-after: always;\"></div>
        """

    # Criar o HTML completo
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            {css_to_use}
        </style>
    </head>
    <body>
        {footer_logo_html}
        {cover_html}
        {html_content}
    </body>
    </html>
    """

    # Converter HTML para PDF
    html_doc = HTML(string=full_html, base_url=str(resolved_base_dir))
    html_doc.write_pdf(pdf_file_path)

    logger.info(f"PDF criado com sucesso: {pdf_file_path}")
    return pdf_file_path


def batch_convert(directory, output_dir=None, css_style=None, logo_path=None):
    """
    Converte todos os arquivos .md em um diretório para PDF.

    Args:
        directory (str): Diretório contendo arquivos .md
        output_dir (str): Diretório de saída para os PDFs (opcional)
        css_style (str): CSS personalizado para estilização (opcional)
        logo_path (str): Caminho para imagem da logo a exibir no rodapé (opcional)
    """
    directory = Path(directory)

    if not directory.is_dir():
        raise ValueError(f"'{directory}' não é um diretório válido")

    # Criar diretório de saída se especificado
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Encontrar todos os arquivos .md
    md_files = list(directory.glob('*.md'))

    if not md_files:
        logger.info(f"Nenhum arquivo .md encontrado em {directory}")
        return

    logger.info(f"Encontrados {len(md_files)} arquivos .md para converter")

    # Converter cada arquivo
    for md_file in md_files:
        try:
            if output_dir:
                pdf_path = output_dir / md_file.with_suffix('.pdf').name
            else:
                pdf_path = md_file.with_suffix('.pdf')

            md_to_pdf(str(md_file), str(pdf_path), css_style, logo_path)
        except Exception as e:
            logger.error(f"Erro ao converter {md_file}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Converte arquivos Markdown (.md) para PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python md_to_pdf.py arquivo.md
  python md_to_pdf.py arquivo.md -o saida.pdf
  python md_to_pdf.py --batch ./documentos
  python md_to_pdf.py --batch ./documentos -o ./pdfs
  python md_to_pdf.py arquivo.md --css custom.css
  python md_to_pdf.py arquivo.md --logo ./logo.png
  python md_to_pdf.py --batch ./documentos --logo ./logo.png
        """
    )

    parser.add_argument(
        'input',
        nargs='?',
        help='Arquivo .md de entrada ou diretório (com --batch)'
    )

    parser.add_argument(
        '-o', '--output',
        help='Arquivo PDF de saída ou diretório de saída (com --batch)'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Converter todos os arquivos .md em um diretório'
    )

    parser.add_argument(
        '--css',
        help='Arquivo CSS personalizado para estilização'
    )

    parser.add_argument(
        '--logo',
        help="Caminho da imagem da logo a exibir no rodapé (PNG/JPG/SVG). Se omitido, o script tenta usar 'logo_zoi.png' no mesmo diretório do arquivo .md"
    )

    args = parser.parse_args()

    # Validar argumentos
    if not args.input:
        parser.print_help()
        return

    try:
        # Modo batch
        if args.batch:
            css_content = None
            if args.css:
                with open(args.css, 'r', encoding='utf-8') as f:
                    css_content = f.read()
            batch_convert(args.input, args.output, css_content, args.logo)
        # Modo arquivo único
        else:
            css_content = None
            if args.css:
                with open(args.css, 'r', encoding='utf-8') as f:
                    css_content = f.read()

            md_to_pdf(args.input, args.output, css_content, args.logo)

    except Exception as e:
        logger.error(f"Erro: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
