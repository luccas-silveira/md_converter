import html
import markdown2
import os
from weasyprint import HTML
import argparse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Sol da ZOI vetorizado (potrace) do PNG oficial — viewBox 0 0 796 801.
# Recolorível via CSS (fill="currentColor"). Gerado uma vez em dev; não precisa
# de potrace em runtime. Fonte do traço: assets/images/sol_zoi.png.
_SUN_PATH = "M336.73,790.56 C315.96,784.91 298.67,780.01 298.32,779.66 C297.67,779.00 353.81,567.12 355.02,565.70 C355.39,565.26 360.38,565.91 366.10,567.15 C380.29,570.22 413.29,570.48 428.31,567.65 C433.71,566.63 438.26,565.95 438.43,566.15 C438.60,566.34 424.63,619.15 407.40,683.50 C390.16,747.85 376.04,800.61 376.03,800.75 C375.98,801.21 374.69,800.87 336.73,790.56 z M499.00,778.59 C499.00,778.36 486.17,730.15 470.48,671.44 C454.80,612.73 442.08,564.63 442.23,564.54 C442.38,564.45 446.32,563.12 451.00,561.59 C469.54,555.49 490.07,543.48 506.49,529.13 C510.89,525.29 514.58,522.25 514.71,522.38 C515.08,522.75 577.94,758.39 577.71,758.56 C577.00,759.09 501.80,779.00 500.54,779.00 C499.70,779.00 499.00,778.81 499.00,778.59 z M151.03,707.53 L122.57,679.06 L201.53,599.78 L280.50,520.50 L287.00,526.37 C296.50,534.94 304.04,540.57 314.82,547.14 C324.39,552.98 343.05,561.46 348.89,562.63 C350.60,562.97 352.00,563.53 352.00,563.88 C352.00,564.62 180.73,736.00 179.99,736.00 C179.71,736.00 166.68,723.19 151.03,707.53 z M594.89,598.72 L516.29,519.46 L521.67,513.55 C534.04,499.93 547.01,476.58 553.08,457.00 C554.87,451.23 556.50,446.29 556.71,446.04 C557.25,445.38 731.00,619.30 731.00,620.50 C731.00,621.50 674.95,678.01 673.99,677.98 C673.72,677.98 638.13,642.31 594.89,598.72 z M42.00,581.60 C42.00,581.38 37.50,564.35 32.00,543.75 C26.50,523.15 22.00,505.64 22.00,504.85 C22.00,503.77 49.54,495.99 129.25,474.56 C188.24,458.70 237.28,445.51 238.24,445.25 C239.19,444.99 240.15,445.39 240.37,446.14 C248.14,473.08 259.71,495.73 274.45,512.88 C277.00,515.84 278.93,518.40 278.75,518.58 C278.34,519.00 43.98,582.00 42.85,582.00 C42.38,582.00 42.00,581.82 42.00,581.60 z M666.00,473.44 C570.36,447.69 557.52,444.00 557.63,442.36 C557.70,441.34 558.49,435.19 559.38,428.70 C570.85,345.25 514.76,265.24 432.69,247.98 C395.22,240.10 359.59,244.79 325.05,262.15 C280.04,284.77 249.00,325.89 238.73,376.50 C236.83,385.88 236.51,390.51 236.58,408.00 C236.64,422.46 237.13,430.71 238.24,436.00 C239.10,440.12 239.67,443.64 239.51,443.80 C239.22,444.11 0.89,380.22 0.36,379.69 C0.04,379.37 20.62,302.04 21.17,301.50 C21.35,301.31 64.93,312.84 118.00,327.10 C171.08,341.37 220.34,354.60 227.48,356.50 L240.47,359.97 L152.73,272.23 C104.48,223.98 65.00,184.04 65.00,183.49 C65.00,182.94 77.82,169.67 93.49,154.01 L121.99,125.53 L201.70,205.89 C245.54,250.09 281.54,285.86 281.70,285.38 C281.85,284.89 267.61,230.73 250.05,165.02 C232.49,99.31 218.23,45.44 218.35,45.31 C218.72,44.95 296.42,24.08 296.60,24.30 C296.69,24.41 309.88,73.78 325.92,134.00 C341.96,194.22 355.40,244.30 355.79,245.28 C356.24,246.40 368.72,201.27 389.40,123.78 C407.49,55.98 422.36,0.39 422.46,0.27 C422.68,-0.03 500.07,20.73 500.56,21.22 C500.76,21.43 487.72,71.01 471.58,131.42 L442.24,241.26 L529.12,154.38 L616.00,67.50 L644.75,96.25 L673.50,125.00 L593.00,205.60 C548.72,249.92 513.40,285.94 514.50,285.64 C522.20,283.51 744.50,223.90 748.29,222.94 C750.92,222.28 753.30,221.97 753.57,222.24 C753.84,222.51 758.70,240.11 764.36,261.35 L774.66,299.96 L771.58,300.93 C769.89,301.47 721.25,314.58 663.50,330.07 C605.75,345.56 557.98,358.52 557.33,358.87 C556.69,359.21 609.66,373.86 675.04,391.41 C740.42,408.97 794.36,423.60 794.90,423.94 C795.49,424.31 791.76,439.94 785.46,463.42 C779.73,484.80 774.92,502.37 774.77,502.47 C774.62,502.57 725.67,489.51 666.00,473.44 z"


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
        cover_template_path (str): OBSOLETO — a capa agora é gerada por código (sem imagem de fundo). Mantido na assinatura por compat; ignorado.

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

    /* ===== Capa gerada por código (sem imagem de fundo) ===== */
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
        background: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    /* régua preta no topo */
    .cover-rule {
        position: absolute; top: 15.5mm; left: 14mm; right: 14mm;
        border-top: 1.2mm solid #141414;
    }
    /* contatos em duas colunas sob a régua */
    .cover-contacts {
        position: absolute; top: 18.5mm; left: 14mm; right: 14mm;
        display: flex; color: #141414; font-size: 10pt; line-height: 1.5;
    }
    .cover-contacts .col { width: 58mm; }
    .cover-contacts .col + .col { border-left: 0.3mm solid #141414; padding-left: 7mm; }
    .cover-contacts b { font-weight: 700; }
    /* sol vetorial (recolorível via 'color') + wordmark */
    .cover-sun {
        position: absolute; left: 16.5mm; top: 78mm;
        width: 15mm; height: 15mm; color: #b5ff81;
    }
    .cover-sun svg { width: 100%; height: 100%; display: block; }
    .cover-wordmark {
        position: absolute; left: 24mm; top: 89mm; margin: 0;
        color: #141414; line-height: 1; white-space: nowrap;
        font-family: 'Clash Display', -apple-system, sans-serif;
        font-weight: 800; font-size: 65pt; letter-spacing: -0.02em;
    }
    /* linha-fio que desce do wordmark (assinatura ZOI) */
    .cover-dropline {
        position: absolute; left: 20.5mm; top: 112mm;
        width: 0.4mm; height: 12mm; background: #141414;
    }
    .cover-dropline::after {
        content: ""; position: absolute; left: -1.2mm; bottom: -2mm;
        border-left: 1.4mm solid transparent; border-right: 1.4mm solid transparent;
        border-top: 2mm solid #141414;
    }
    /* subtítulo + descrição abaixo do wordmark */
    .cover-headblock {
        position: absolute; left: 26mm; top: 130mm; width: 150mm; text-align: left;
    }
    .cover-title-sub {
        color: #141414; font-size: 16pt; font-weight: 600; line-height: 1.2; margin: 0;
        overflow-wrap: break-word; word-break: break-word;
        font-family: 'Clash Display', -apple-system, sans-serif;
    }
    .cover-desc {
        color: #5c5c5c; font-size: 10.5pt; line-height: 1.35; margin: 3mm 0 0 0;
        overflow-wrap: break-word; word-break: break-word;
    }
    /* faixa verde inferior */
    .cover-band {
        position: absolute; left: 0; right: 0; bottom: 0; height: 76.1mm;
        background: #b5ff81;
    }
    /* prep e data em posição absoluta (compat WeasyPrint 60, sem grid/flex):
       centralizados na altura da faixa, na mesma linha base */
    .cover-prep {
        position: absolute; left: 14mm; top: 248mm; width: 90mm; color: #141414;
    }
    .cover-prep .label { font-weight: 700; font-size: 11pt; }
    .cover-prep .name {
        display: block; margin-top: 2mm; font-size: 13pt; font-weight: 700; color: #141414;
        font-family: 'Clash Display', -apple-system, sans-serif;
    }
    .cover-prep .contact { margin-top: 1mm; color: #333333; font-size: 10.5pt; }
    .cover-date {
        position: absolute; left: 105mm; top: 248mm; width: 80mm; color: #141414; font-size: 11pt;
    }
    .cover-date .label { font-weight: 700; }

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
        display: table;
        padding: 6px 12px;
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
        /* Blocos longos (ex.: fluxograma ASCII) quebram entre páginas em vez de
           pular o bloco inteiro e deixar um vão em branco após o título. */
        page-break-inside: auto;
        orphans: 4;
        widows: 4;
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
        table-layout: fixed;
        word-wrap: break-word;
        page-break-inside: auto;
    }

    table th,
    table td {
        border: 1px solid #d0d7de;
        padding: 6px 10px;
        text-align: left;
        overflow-wrap: break-word;
        word-break: break-word;
        font-size: 0.88em;
    }

    table th {
        background-color: #141414;
        color: #ffffff;
        font-weight: 600;
        font-family: 'Clash Display', -apple-system, sans-serif;
        font-size: 0.92em;
    }

    table tr {
        page-break-inside: avoid;
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
        max-height: 235mm; /* altura útil da página; SVG alto (mermaid) não é fatiado, só encolhido */
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

    # Capa gerada 100% por código (réplica fiel do mockup, sem imagem de fundo).
    # O sol é o PNG da ZOI vetorizado uma vez via potrace; vai versionado aqui como
    # path SVG, recolorível trocando sun_color abaixo. cover_template_path continua
    # aceito na assinatura por compat, mas não é mais usado.
    cd = cover_data or {}
    # Estáticos do mockup (texto fixo). Coluna direita aceita override do form.
    top_email = html.escape(cd.get('topo_direito_email') or 'contato@zoi.tech')
    top_site = html.escape(cd.get('topo_direito_site') or 'www.zoitech.com.br')
    rep_nome = html.escape(cd.get('representante_nome') or 'Luccas Silveira')
    # Título principal (wordmark): editável, default "Relatório". 1-2 palavras.
    titulo = (cd.get('titulo_principal') or '').strip() or 'Relatório'
    titulo_esc = html.escape(titulo)
    # ponytail: encolhe a fonte p/ título longo não estourar a largura. ~0.147mm
    # por (char·pt) medido p/ Clash em "Relatório"; teto 65pt, piso 34pt.
    wm_size = max(34, min(65, int(1050 / max(len(titulo), 9))))
    # Dinâmicos (conteúdo deste relatório).
    subtitulo = html.escape(cd.get('subtitulo', ''))
    descricao = html.escape(cd.get('descricao', ''))
    prep_nome = html.escape(cd.get('preparado_nome', ''))
    prep_email = html.escape(cd.get('preparado_email', ''))
    prep_phone = html.escape(cd.get('preparado_phone', ''))
    data_text = html.escape(cd.get('data', ''))

    # fill direto na cor da ZOI: WeasyPrint não resolve currentColor em SVG inline.
    sun_color = '#b5ff81'
    sun_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 796 801" aria-hidden="true">'
        f'<path fill-rule="evenodd" fill="{sun_color}" d="{_SUN_PATH}"/></svg>'
    )

    cover_html = f"""
    <section class="cover-page">
        <div class="cover-rule"></div>
        <div class="cover-contacts">
            <div class="col"><b>ZOI</b><br>Benjamin Constant 2839<br>Joinville &mdash; SC, Brasil<br>+55 (47) 9 9638-4996</div>
            <div class="col">{top_email}<br>{top_site}<br><b>Representante Técnico</b><br>{rep_nome}</div>
        </div>
        <div class="cover-sun">{sun_svg}</div>
        <div class="cover-wordmark" style="font-size:{wm_size}pt">{titulo_esc}</div>
        <div class="cover-dropline"></div>
        <div class="cover-headblock">
            <div class="cover-title-sub">{subtitulo}</div>
            <div class="cover-desc">{descricao}</div>
        </div>
        <div class="cover-band"></div>
        <div class="cover-prep">
            <span class="label">Preparado por:</span>
            <span class="name">{prep_nome}</span>
            <div class="contact">{prep_email}</div>
            <div class="contact">{prep_phone}</div>
        </div>
        <div class="cover-date"><span class="label">Data:</span> {data_text}</div>
    </section>
    <div style="page-break-after: always;"></div>
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

    # Converter HTML para PDF.
    # url_fetcher com guard de SSRF p/ imagens remotas (data:/file: caem no padrão).
    # Import tolerante: execução CLI fora do pacote cai no fetcher padrão.
    html_kwargs = {'base_url': str(resolved_base_dir)}
    try:
        from app.utils.image_check import safe_url_fetcher
        html_kwargs['url_fetcher'] = safe_url_fetcher
    except Exception:
        pass
    html_doc = HTML(string=full_html, **html_kwargs)
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
