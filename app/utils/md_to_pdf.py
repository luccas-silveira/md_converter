import html
import os
import re
from weasyprint import HTML
import argparse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Sol da ZOI vetorizado (potrace) do PNG oficial — viewBox 0 0 796 801.
# Recolorível via CSS (fill="currentColor"). Gerado uma vez em dev; não precisa
# de potrace em runtime. Fonte do traço: assets/images/sol_zoi.png.
_SUN_PATH = "M336.73,790.56 C315.96,784.91 298.67,780.01 298.32,779.66 C297.67,779.00 353.81,567.12 355.02,565.70 C355.39,565.26 360.38,565.91 366.10,567.15 C380.29,570.22 413.29,570.48 428.31,567.65 C433.71,566.63 438.26,565.95 438.43,566.15 C438.60,566.34 424.63,619.15 407.40,683.50 C390.16,747.85 376.04,800.61 376.03,800.75 C375.98,801.21 374.69,800.87 336.73,790.56 z M499.00,778.59 C499.00,778.36 486.17,730.15 470.48,671.44 C454.80,612.73 442.08,564.63 442.23,564.54 C442.38,564.45 446.32,563.12 451.00,561.59 C469.54,555.49 490.07,543.48 506.49,529.13 C510.89,525.29 514.58,522.25 514.71,522.38 C515.08,522.75 577.94,758.39 577.71,758.56 C577.00,759.09 501.80,779.00 500.54,779.00 C499.70,779.00 499.00,778.81 499.00,778.59 z M151.03,707.53 L122.57,679.06 L201.53,599.78 L280.50,520.50 L287.00,526.37 C296.50,534.94 304.04,540.57 314.82,547.14 C324.39,552.98 343.05,561.46 348.89,562.63 C350.60,562.97 352.00,563.53 352.00,563.88 C352.00,564.62 180.73,736.00 179.99,736.00 C179.71,736.00 166.68,723.19 151.03,707.53 z M594.89,598.72 L516.29,519.46 L521.67,513.55 C534.04,499.93 547.01,476.58 553.08,457.00 C554.87,451.23 556.50,446.29 556.71,446.04 C557.25,445.38 731.00,619.30 731.00,620.50 C731.00,621.50 674.95,678.01 673.99,677.98 C673.72,677.98 638.13,642.31 594.89,598.72 z M42.00,581.60 C42.00,581.38 37.50,564.35 32.00,543.75 C26.50,523.15 22.00,505.64 22.00,504.85 C22.00,503.77 49.54,495.99 129.25,474.56 C188.24,458.70 237.28,445.51 238.24,445.25 C239.19,444.99 240.15,445.39 240.37,446.14 C248.14,473.08 259.71,495.73 274.45,512.88 C277.00,515.84 278.93,518.40 278.75,518.58 C278.34,519.00 43.98,582.00 42.85,582.00 C42.38,582.00 42.00,581.82 42.00,581.60 z M666.00,473.44 C570.36,447.69 557.52,444.00 557.63,442.36 C557.70,441.34 558.49,435.19 559.38,428.70 C570.85,345.25 514.76,265.24 432.69,247.98 C395.22,240.10 359.59,244.79 325.05,262.15 C280.04,284.77 249.00,325.89 238.73,376.50 C236.83,385.88 236.51,390.51 236.58,408.00 C236.64,422.46 237.13,430.71 238.24,436.00 C239.10,440.12 239.67,443.64 239.51,443.80 C239.22,444.11 0.89,380.22 0.36,379.69 C0.04,379.37 20.62,302.04 21.17,301.50 C21.35,301.31 64.93,312.84 118.00,327.10 C171.08,341.37 220.34,354.60 227.48,356.50 L240.47,359.97 L152.73,272.23 C104.48,223.98 65.00,184.04 65.00,183.49 C65.00,182.94 77.82,169.67 93.49,154.01 L121.99,125.53 L201.70,205.89 C245.54,250.09 281.54,285.86 281.70,285.38 C281.85,284.89 267.61,230.73 250.05,165.02 C232.49,99.31 218.23,45.44 218.35,45.31 C218.72,44.95 296.42,24.08 296.60,24.30 C296.69,24.41 309.88,73.78 325.92,134.00 C341.96,194.22 355.40,244.30 355.79,245.28 C356.24,246.40 368.72,201.27 389.40,123.78 C407.49,55.98 422.36,0.39 422.46,0.27 C422.68,-0.03 500.07,20.73 500.56,21.22 C500.76,21.43 487.72,71.01 471.58,131.42 L442.24,241.26 L529.12,154.38 L616.00,67.50 L644.75,96.25 L673.50,125.00 L593.00,205.60 C548.72,249.92 513.40,285.94 514.50,285.64 C522.20,283.51 744.50,223.90 748.29,222.94 C750.92,222.28 753.30,221.97 753.57,222.24 C753.84,222.51 758.70,240.11 764.36,261.35 L774.66,299.96 L771.58,300.93 C769.89,301.47 721.25,314.58 663.50,330.07 C605.75,345.56 557.98,358.52 557.33,358.87 C556.69,359.21 609.66,373.86 675.04,391.41 C740.42,408.97 794.36,423.60 794.90,423.94 C795.49,424.31 791.76,439.94 785.46,463.42 C779.73,484.80 774.92,502.37 774.77,502.47 C774.62,502.57 725.67,489.51 666.00,473.44 z"


COVER_CSS = """
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
    /* Satoshi (em assets/fonts) antes do system: o system do servidor Linux não é o do
       navegador, e a capa sairia com fonte diferente do preview */
    font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
/* subtítulo + descrição abaixo do wordmark, alinhados à haste do R */
.cover-headblock {
    position: absolute; left: 24.6mm; top: 115mm; width: 150mm; text-align: left;
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
.ord { font-family: 'Satoshi', -apple-system, sans-serif; }
"""

_FONT_WEIGHTS = {'extralight': 200, 'light': 300, 'regular': 400, 'medium': 500,
                 'semibold': 600, 'bold': 700, 'black': 900}


def font_faces_css(fonts_dir: Path, url_prefix: str):
    """@font-face de cada arquivo Clash/Satoshi em fonts_dir, peso tirado do nome.
    Mesma declaração no PDF e no preview do front: nenhum dos dois sintetiza negrito.
    Devolve (css, famílias encontradas)."""
    faces, families = [], set()
    if fonts_dir.is_dir():
        for f in sorted(fonts_dir.iterdir()):
            stem = f.stem.lower()
            if f.suffix.lower() not in ('.woff2', '.woff', '.ttf', '.otf'):
                continue
            family = 'Clash Display' if 'clash' in stem else 'Satoshi' if 'satoshi' in stem else None
            if not family:
                continue
            style = 'italic' if 'italic' in stem else 'normal'
            # 'semibold' antes de 'bold', 'extralight' antes de 'light': o mais longo que casar vence
            weight = max(((len(k), w) for k, w in _FONT_WEIGHTS.items() if k in stem), default=(0, 400))[1]
            faces.append(f"@font-face {{ font-family: '{family}'; src: url('{url_prefix}{f.name}'); "
                         f"font-weight: {weight}; font-style: {style}; }}")
            families.add(family)
    return '\n'.join(faces), families


def build_cover_html(cover_data=None):
    """HTML da capa. Usado pelo PDF e pela pré-visualização do front (mesma fonte)."""
    # Capa gerada 100% por código (réplica fiel do mockup, sem imagem de fundo).
    # O sol é o PNG da ZOI vetorizado uma vez via potrace; vai versionado aqui como
    # path SVG, recolorível trocando sun_color abaixo. cover_template_path continua
    # aceito na assinatura por compat, mas não é mais usado.
    cd = cover_data or {}
    # Estáticos do mockup (texto fixo). Coluna direita aceita override do form.
    top_email = html.escape(cd.get('topo_direito_email') or 'contato@zoi.tech')
    top_site = html.escape(cd.get('topo_direito_site') or 'www.zoitech.com.br')
    rep_label = html.escape(cd.get('representante_label') or 'Representante Técnico')
    rep_nome = html.escape(cd.get('representante_nome') or 'Luccas Silveira')
    # Título principal (wordmark): editável, default "Relatório". 1-2 palavras.
    titulo = (cd.get('titulo_principal') or '').strip() or 'Relatório'
    titulo_esc = _ord(html.escape(titulo))
    # ponytail: encolhe a fonte p/ título longo não estourar a largura. ~0.147mm
    # por (char·pt) medido p/ Clash em "Relatório"; teto 65pt, piso 34pt.
    wm_size = max(34, min(65, int(1050 / max(len(titulo), 9))))
    # Dinâmicos (conteúdo deste relatório).
    subtitulo = _ord(html.escape(cd.get('subtitulo', '')))
    descricao = html.escape(cd.get('descricao', ''))
    prep_nome = html.escape(cd.get('preparado_nome', ''))
    prep_email = html.escape(cd.get('preparado_email', ''))
    prep_phone = html.escape(cd.get('preparado_phone', ''))
    data_raw = cd.get('data', '')
    # <input type=date> manda AAAA-MM-DD; a capa mostra DD/MM/AAAA.
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', data_raw):
        data_raw = '/'.join(reversed(data_raw.split('-')))
    data_text = html.escape(data_raw)

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
            <div class="col">{top_email}<br>{top_site}<br><b>{rep_label}</b><br>{rep_nome}</div>
        </div>
        <div class="cover-sun">{sun_svg}</div>
        <div class="cover-wordmark" style="font-size:{wm_size}pt">{titulo_esc}</div>
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
    return cover_html


# Separadores de linha/página Unicode que o WeasyPrint não aceita no meio do texto
# (U+2029 derrubava a conversão). Viram quebra de linha comum.
_LINE_SEPS = re.compile('[  \x0b\x0c\x85]')
_WIKILINK = re.compile(r'\[\[([^\[\]|\n]+)(?:\|([^\[\]\n]+))?\]\]')
# "Status: ativo" — rótulo curto e capitalizado no começo da linha
_PLAIN_LABEL = re.compile(r'^[A-ZÀ-Ý][^\s:]*(?: [^\s:]+){0,2}:(\s|$)')
# "Expected: …" — rótulo de uma palavra abre linha própria mesmo depois de linha longa
_ABBREV_END = re.compile(r'\b(?:[A-Z][a-z]{0,3}|art|arts|inc|p|pp)\.$')
_ONE_WORD_LABEL = re.compile(r'^[A-ZÀ-Ý][\w-]*:(\s|$)')
# item digitado à mão ("• x", "4. x" que não interrompe parágrafo no CommonMark)
_ITEM_LINE = re.compile(r'^(?:[•·▪◦‣-]|\d+[.)])\s')
# ~texto~ (til simples, riscado do GitHub); ~~ o markdown-it já trata
_SINGLE_TILDE = re.compile(r'(?<![~\w])~(?=\S)([^~\n]*?\S)~(?![~\w])')
# moldura de desenho ASCII: verticais e cantos (─ sozinho é só separador de comentário)
_FRAME_CHARS = re.compile('[│┃┌-╋║-╬]')
_DANGEROUS_URL = re.compile(r'\s*(javascript|vbscript|file|data:text):', re.I)
_ORDINAL = re.compile('[ºª]')
_EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿]'
                    '[️‍\U0001F3FB-\U0001F3FF\U0001F000-\U0001FAFF☀-➿]*')


def _ord(text):
    """º/ª na Satoshi: na Clash Display o desenho parece o símbolo de grau."""
    return _ORDINAL.sub(lambda m: f'<span class="ord">{m.group(0)}</span>', text)


def _vis_len(text):
    """Largura visual aproximada em caracteres (emoji ocupa ~2)."""
    return len(text) + len(_EMOJI.findall(text))


def _split_lines(children):
    """Linhas visíveis de um parágrafo, separadas pelas quebras simples do md:
    [(texto, começa_em_negrito, só_link_ou_url)]."""
    lines, cur = [], []
    for c in children + [None]:
        if c is None or c.type in ('softbreak', 'hardbreak'):
            kinds = [x.type for x in cur if not (x.type == 'text' and not x.content.strip())]
            text = ''.join(x.content for x in cur if x.type in ('text', 'code_inline')).strip()
            # "**Rótulo:** valor" / "**Rótulo**: valor" (negrito de ênfase no meio da frase não conta)
            vis = [x for x in cur if not (x.type == 'text' and not x.content.strip())]
            bold = False
            if vis and vis[0].type == 'strong_open':
                close = next((j for j, x in enumerate(vis) if x.type == 'strong_close'), None)
                if close is not None:
                    inner = ''.join(x.content for x in vis[1:close]).strip()
                    after = vis[close + 1].content.lstrip() if close + 1 < len(vis) and vis[close + 1].type == 'text' else ''
                    if inner.endswith(':') or after.startswith(':'):
                        bold = 'colon'
                    elif inner.endswith('.') and (inner[:1].isupper() or inner[:1].isdigit()):
                        bold = 'dot'
                    else:
                        # só começa em negrito: conta para "sequência de linhas em negrito"
                        bold = 'plain'
            only_link = (bool(kinds) and kinds[0] == 'link_open' and kinds[-1] == 'link_close'
                         and kinds.count('link_open') >= 1 and all(k in ('link_open', 'link_close', 'text', 'image') for k in kinds))
            # linha inteira em negrito (cabeçalho de metadados) também é rótulo
            whole = (bool(vis) and vis[0].type == 'strong_open' and vis[-1].type == 'strong_close'
                     and kinds.count('strong_open') == 1)
            lines.append((text, 'whole' if whole else bold or '',
                          only_link or text.startswith(('http://', 'https://'))))
            cur = []
        else:
            cur.append(c)
    return lines


def _bare(text):
    """Sem aspas/parênteses de fechamento no fim: 'fim.”' termina em ponto."""
    return text.rstrip('"”’\')]»')


def _hard_breaks(lines):
    """Para cada quebra simples do parágrafo, True se ela é intencional.

    Por padrão junta, como o GitHub. Mantém a quebra só quando o autor claramente
    a quis: linhas curtas (endereço, assinatura), linha que é só link, sequência
    de "Rótulo: valor", ou linha que acabou bem antes da largura das outras.

    ponytail: heurística por comprimento de linha visível; a largura de coluna é
    a maior linha exceto a última (que pode ser mais curta ou mais longa).
    """
    lens = [_vis_len(t) for t, _, _ in lines]
    width = max(lens[:-1] if len(lens) > 2 else lens)
    labels = [bold or bool(_PLAIN_LABEL.match(t)) for t, bold, _ in lines]
    # uma frase por linha (toda linha termina em pontuação): o autor quis as quebras
    if len(lines) >= 3 and all(_bare(t).endswith(('.', '!', '?')) and not _ABBREV_END.search(_bare(t))
                               for t, _, _ in lines[:-1]):
        return [True] * (len(lines) - 1)
    out = []
    for k in range(len(lines) - 1):
        (cur, cur_bold, cur_link), (nxt, nxt_bold, nxt_link) = lines[k], lines[k + 1]
        fits = lens[k] + 1 + _vis_len(nxt.split(maxsplit=1)[0] if nxt.split() else '')
        out.append(width < 50
                   or (cur_link and nxt_link)
                   or nxt_bold == 'colon'
                   # "**Cl. 30 — Título.**" / linha toda em negrito: só abre linha se a
                   # anterior terminou a frase (senão é ênfase caindo no começo da linha)
                   or (nxt_bold in ('dot', 'whole') and _bare(cur).endswith(('.', '!', '?', ':')))
                   or (cur_bold == 'whole' and not nxt[:1].islower())
                   or bool(_ITEM_LINE.match(nxt))
                   or (bool(_ONE_WORD_LABEL.match(nxt))
                       and (cur.endswith(('.', '!', '?', ':', ';', ')')) or fits <= 0.8 * width))
                   or (cur.endswith(':') and fits <= 0.8 * width and not nxt[:1].islower())
                   or (labels[k] and labels[k + 1])
                   or fits <= 0.6 * width
                   or (cur.endswith(('.', ':', ';', '!', '?')) and fits <= 0.8 * width))
    return out


def _tilde_strike(children, Token):
    """Divide texto com ~x~ em s_open/texto/s_close."""
    out = []
    for c in children:
        if c.type != 'text' or '~' not in c.content:
            out.append(c)
            continue
        pos = 0
        for m in _SINGLE_TILDE.finditer(c.content):
            if m.start() > pos:
                t = Token('text', '', 0); t.content = c.content[pos:m.start()]; out.append(t)
            out.append(Token('s_open', 's', 1))
            t = Token('text', '', 0); t.content = m.group(1); out.append(t)
            out.append(Token('s_close', 's', -1))
            pos = m.end()
        if pos == 0:
            out.append(c)
        elif pos < len(c.content):
            t = Token('text', '', 0); t.content = c.content[pos:]; out.append(t)
    return out


def _core_fixes(state):
    """Pós-parse: quebras de linha intencionais, wikilinks, riscado com ~, títulos
    vazios, links perigosos, rótulo colado no bloco seguinte, numeração de lista
    e largura de tabelas."""
    from markdown_it.token import Token
    toks = state.tokens
    table = None
    for i, tok in enumerate(toks):
        if tok.type == 'table_open':
            table, cols = tok, 0
        elif tok.type == 'th_open':
            cols += 1
        elif tok.type == 'thead_close' and table is not None:
            if cols >= 6:
                table.attrSet('class', 'wide' if cols < 8 else 'very-wide')
            table = None
        elif tok.type == 'ordered_list_open' and tok.attrGet('start'):
            # WeasyPrint ignora start=; o contador CSS respeita
            tok.attrSet('style', f"counter-reset: list-item {int(tok.attrGet('start')) - 1}")
        if tok.type != 'inline':
            continue
        prev = toks[i - 1] if i else None
        tok.children = _tilde_strike(tok.children or [], Token)
        for child in tok.children:
            if child.type == 'text':
                if '[[' in child.content:
                    child.content = _WIKILINK.sub(lambda m: (m.group(2) or m.group(1)).strip(), child.content)
                # "R$ 50.000,00" não parte entre o símbolo e o valor
                child.content = re.sub(r'R\$ (?=\d)', 'R$ ', child.content)
            if child.type == 'link_open' and _DANGEROUS_URL.match(child.attrGet('href') or ''):
                del child.attrs['href']  # vira texto, sem link executável no PDF
        if prev is not None and prev.type == 'paragraph_open':
            breaks = iter(_hard_breaks(_split_lines(tok.children)))
            for child in tok.children:
                if child.type == 'softbreak' and next(breaks, False):
                    child.type, child.tag = 'hardbreak', 'br'
                elif child.type == 'hardbreak':
                    next(breaks, None)
            classes = []
            # "Arquivos:" / "**Datas.**": rótulo que apresenta o bloco seguinte
            if re.search(r':(\*\*|__)?\s*$', tok.content) or re.fullmatch(r'\*\*[^*\n]+\*\*', tok.content.strip()):
                classes.append('lead-in')
            if any(c.type == 'image' for c in tok.children):
                classes.append('has-img')
            if classes:
                prev.attrJoin('class', ' '.join(classes))
    # Título vazio ("## " sem texto) não vira badge verde vazio
    keep, skip = [], 0
    for i, tok in enumerate(toks):
        if skip:
            skip -= 1
            continue
        if tok.type == 'heading_open' and i + 1 < len(toks) and not toks[i + 1].content.strip():
            skip = 2
            continue
        keep.append(tok)
    state.tokens = keep
    _unchain_lead_ins(keep)
    _table_widths(keep)


def _unchain_lead_ins(toks):
    """Rótulo seguido de outro rótulo ("Step 2" + "Run:" + código) não fica preso:
    só o último da sequência gruda no bloco seguinte. Cadeias de "não quebrar"
    empurravam três ou quatro blocos juntos e deixavam meia página em branco."""
    def lead(t):
        return t.nesting == 1 and 'lead-in' in (t.attrGet('class') or '').split()
    for i, t in enumerate(toks):
        if not lead(t):
            continue
        close = t.type.replace('_open', '_close')
        j = next((k for k in range(i + 1, len(toks)) if toks[k].type == close and toks[k].level == t.level), None)
        if j is not None and j + 1 < len(toks) and lead(toks[j + 1]):
            rest = [c for c in t.attrGet('class').split() if c != 'lead-in']
            if rest:
                t.attrSet('class', ' '.join(rest))
            else:
                del t.attrs['class']


def _table_widths(toks):
    """Largura de cada coluna pelo conteúdo, como o layout automático do navegador.
    O automático do WeasyPrint 60 deixa tabela larga passar da página; aqui a
    tabela é fixa e as larguras vêm do texto: coluna curta fica estreita, a de
    texto longo ganha o resto, e nenhuma fica menor que a sua maior palavra. Se
    as palavras não cabem nem assim, a fonte da tabela diminui.

    ponytail: mede em caracteres, não em pontos (Satoshi ~0.55em, código ~0.66em,
    cabeçalho em Clash negrito ~0.72em). Refinar com métrica de fonte se preciso.
    """
    usable = 440.0  # pt úteis da página (A4 menos margens e padding do corpo)
    for i, tok in enumerate(toks):
        if tok.type != 'table_open':
            continue
        cls = tok.attrGet('class') or ''
        scale = 0.78 if 'very-wide' in cls else 0.9 if 'wide' in cls else 1.0
        longest, widest, heads, col, in_head = {}, {}, [], -1, False
        for t in toks[i + 1:]:
            if t.type == 'table_close':
                break
            if t.type == 'tr_open':
                col = -1
            elif t.type in ('th_open', 'td_open'):
                col += 1
                in_head = t.type == 'th_open'
                if in_head:
                    heads.append(t)
            elif t.type == 'inline' and col >= 0:
                total, word = 0.0, 0.0
                for c in t.children or []:
                    if c.type not in ('text', 'code_inline'):
                        continue
                    k = 1.3 if in_head else 1.0
                    total += _vis_len(c.content) * k
                    # maior trecho sem ponto de quebra; código parte em / e - (onde a
                    # quebra de linha é permitida; _ e . não são) e token
                    # acima de 20 caracteres (URL, ID) quebra dentro da célula
                    splitter = r'[ \t\n]+|(?<=[/\-])' if c.type == 'code_inline' else r'[ \t\n]+'
                    pad = 2 if c.type == 'code_inline' else 1
                    cap = 30 if c.type == 'code_inline' else 20
                    word = max([word] + [min(_vis_len(w), cap) * k + pad for w in re.split(splitter, c.content)])
                longest[col] = max(longest.get(col, 0), total)
                widest[col] = max(widest.get(col, 0), word)
        n = len(heads)
        if not n:
            continue
        mins = [max(widest.get(c, 1), 3) for c in range(n)]
        maxs = [max(longest.get(c, 1), mins[c]) for c in range(n)]
        pad_pt = 10 if scale < 1 else 20

        def avail(s):
            return (usable - pad_pt * n) / (9.24 * 0.6 * s)
        if sum(mins) > avail(scale):
            # nem as maiores palavras cabem: fonte menor (piso ~7pt) antes de partir palavra
            # tabela estreita não encolhe tanto: melhor partir um token longo que ilegível
            scale = max(0.8 if n < 6 else 0.62, scale * avail(scale) / sum(mins))
            tok.attrSet('style', f'font-size: {scale:.2f}em')
            tok.attrSet('class', (cls + ' shrunk').strip())
        room = avail(scale)
        if sum(maxs) <= room:
            chars = [m * room / sum(maxs) for m in maxs]
        elif sum(mins) >= room:
            chars = [m * room / sum(mins) for m in mins]
        else:
            extra = (room - sum(mins)) / (sum(maxs) - sum(mins))
            chars = [lo + (hi - lo) * extra for lo, hi in zip(mins, maxs)]
        pts = [ch * 9.24 * 0.6 * scale + pad_pt for ch in chars]
        for th, pt in zip(heads, pts):
            th.attrSet('style', f'width: {100 * pt / sum(pts):.1f}%')


def _render_code(self, tokens, idx, options, env):
    """Bloco de código: cada linha num bloco com recuo pendente, então a continuação
    de uma linha longa quebra alinhada à indentação dela. Desenho com moldura
    (┌─┐ │) não quebra: a fonte encolhe até a linha mais longa caber."""
    tok = tokens[idx]
    lang = tok.info.strip().split()[0] if tok.info.strip() else ''
    cls = f' class="language-{html.escape(lang)}"' if lang else ''
    lines = tok.content.rstrip('\n').expandtabs(4).split('\n')
    if sum(1 for l in lines if _FRAME_CHARS.search(l)) >= 2:
        # ~420pt úteis no bloco; DejaVu Sans Mono tem 0.602em por caractere
        size = max(3.0, min(8.9, 420 / (max(map(_vis_len, lines)) * 0.602)))
        # não parte só se couber numa página (~650pt úteis); maior que isso, parte
        keep = '; page-break-inside: avoid' if len(lines) * size * 1.25 < 600 else ''
        return (f'<pre class="diagram" style="font-size:{size:.2f}pt{keep}"><code{cls}>'
                f'{html.escape(chr(10).join(lines))}\n</code></pre>\n')
    spans = []
    for l in lines:
        indent = len(l) - len(l.lstrip(' '))
        text = html.escape(l)
        first = l.split()[0] if l.split() else ''
        if indent + len(first) > 60:
            # recuo + palavra que não cabem na linha: sem espaço inquebrável o recuo
            # vira uma linha em branco antes da palavra
            text = ' ' * indent + html.escape(l[indent:])
        n = indent + 2
        spans.append(f'<span class="ln"><span class="cl" style="padding-left:{n}ch;text-indent:-{n}ch">{text or " "}</span></span>')
    # 2 primeiras e 2 últimas linhas em grupos inseparáveis (orphans/widows). O fundo
    # escuro fica nas linhas, não no <pre>: se a página quebrar no começo do bloco, o
    # pedaço que sobra é invisível, em vez de uma caixa preta vazia
    if len(spans) <= 6:
        groups = [spans]
    else:
        groups = [spans[:2]] + [[x] for x in spans[2:-2]] + [spans[-2:]]
    parts = []
    for gi, g in enumerate(groups):
        edge = (' top' if gi == 0 else '') + (' bot' if gi == len(groups) - 1 else '')
        parts.append(f'<span class="grp{edge}">{"".join(g)}</span>' if edge else g[0])
    short = ' short' if len(groups) == 1 else ''
    return f'<pre class="lines{short}"><code{cls}>{"".join(parts)}</code></pre>\n'


def _render_code_inline(self, tokens, idx, options, env):
    """Código inline curto não parte no meio ("--short" / "branch")."""
    content = tokens[idx].content
    cls = ' class="nw"' if len(content) <= 40 else ''
    return f'<code{cls}>{html.escape(content)}</code>'


_TASK_INPUT = re.compile(r'<input class="task-list-item-checkbox"([^>]*)>')
_HEADING = re.compile(r'<h([1-6])([^>]*)>(.*?)</h\1>', re.S)
_TEXT_NODE = re.compile(r'>([^<]+)<')
_EMOJI_SP = re.compile(f'({_EMOJI.pattern})( ?)')


def _build_markdown():
    from markdown_it import MarkdownIt
    from mdit_py_plugins.anchors import anchors_plugin
    from mdit_py_plugins.footnote import footnote_plugin
    from mdit_py_plugins.front_matter import front_matter_plugin
    from mdit_py_plugins.tasklists import tasklists_plugin

    # CommonMark (mesmas regras do GitHub): lista colada no parágrafo, código dentro
    # de lista, "_ênfase_", numeração inicial de lista. Só aspas curvas; sem troca de
    # "--" por travessão (quebrava comandos e URLs). URL solta vira link, como no GitHub.
    md = (MarkdownIt('commonmark', {'html': True, 'typographer': True, 'linkify': True})
          .enable(['table', 'strikethrough', 'smartquotes', 'linkify'])
          .use(front_matter_plugin)
          .use(footnote_plugin)
          .use(tasklists_plugin)
          .use(anchors_plugin, max_level=6))
    # só URL com esquema/www vira link; "DESIGN.md" não é domínio
    md.linkify.set({'fuzzy_link': False})
    # Todo link é parseado (senão "[x](javascript:…)" aparece cru); os perigosos
    # perdem o href em _core_fixes. data: fica: o SVG do Mermaid vem assim do front.
    md.validateLink = lambda url: True
    md.core.ruler.push('zoi_fixes', _core_fixes)
    md.add_render_rule('fence', _render_code)
    md.add_render_rule('code_block', _render_code)
    md.add_render_rule('code_inline', _render_code_inline)
    return md


_MD = None


def render_markdown(md_content):
    """Markdown → HTML do corpo do PDF."""
    global _MD
    if _MD is None:
        _MD = _build_markdown()
    html_out = _MD.render(_LINE_SEPS.sub('\n', md_content))
    html_out = _HEADING.sub(lambda m: f'<h{m.group(1)}{m.group(2)}>{_ord(m.group(3))}</h{m.group(1)}>', html_out)
    # emoji em span próprio: o espaço seguinte fica na fonte do texto (na fonte de
    # emoji ele some e o título sai "🔒SEGUROS")
    html_out = _TEXT_NODE.sub(
        lambda m: '>' + _EMOJI_SP.sub(
            lambda e: f'<span class="emo{" sp" if e.group(2) else ""}">{e.group(1)}</span>', m.group(1)) + '<',
        html_out)
    # Checkbox desenhado em CSS: <input> no WeasyPrint vira quadrado preto/caixa de texto
    return _TASK_INPUT.sub(
        lambda m: '<span class="task-box">%s</span>' % ('✓' if 'checked' in m.group(1) else ''),
        html_out)


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

    html_content = render_markdown(md_content)

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
            font-size: 8pt;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
    }

    """ + COVER_CSS + """

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.5;
        color: #333333;
        max-width: 100%;
        margin: 0 auto;
        padding: 20px;
        font-size: 10.5pt;
    }
    /* HTML cru no md (ex.: e-mail com largura fixa de 600px) não passa da página */
    .md-body * { max-width: 100% !important; box-sizing: border-box; }

    /* capa sangra até a borda: desfaz o padding do body (senão desce/anda 20px vs preview) */
    .cover-page { margin: -20px 0 0 -20px; }

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

    h1 strong, h2 strong, h3 strong, h4 strong, h5 strong, h6 strong { font-weight: inherit; }

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
        orphans: 2;
        widows: 2;
    }

    strong { color: #141414; }
    th strong { color: inherit; }  /* cabeçalho é fundo preto */

    /* rótulo "Arquivos:" fica na mesma página que a lista/código que apresenta */
    p.lead-in { page-break-after: avoid; }
    /* código não fica sozinho no topo da página longe do texto que o apresenta */
    li > pre { page-break-before: avoid; }
    /* "O print da conversa:" + imagem andam juntos */
    p.has-img { page-break-inside: avoid; }

    code {
        background-color: #f7fff2;
        padding: 0 1px;
        border-radius: 3px;
        overflow-wrap: anywhere;
        font-family: 'DejaVu Sans Mono', 'DejaVu Sans', monospace;
        font-size: 0.88em;
        font-weight: normal;
        color: #364c26;
    }

    pre {
        background-color: #141414;
        color: #b5ff81;
        padding: 16px 20px;
        border-radius: 12px;
        /* PDF não rola: linha longa quebra dentro do bloco em vez de vazar/cortar */
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        line-height: 1.5;
        font-size: 0.85em;
        /* Blocos longos (ex.: fluxograma ASCII) quebram entre páginas em vez de
           pular o bloco inteiro e deixar um vão em branco após o título. */
        page-break-inside: auto;
        orphans: 2;
        widows: 2;
    }

    pre .cl { display: block; }
    /* linhas são blocos: orphans/widows à mão (2 no começo, 1 no fim) */
    pre.lines { background: transparent; padding: 0; border-radius: 0; }
    pre .ln { display: block; background: #141414; padding: 0 20px; }
    pre .grp { display: block; page-break-inside: avoid; background: #141414; }
    pre .grp.top { padding-top: 16px; border-radius: 12px 12px 0 0; page-break-before: avoid; }
    pre .grp.bot { padding-bottom: 16px; border-radius: 0 0 12px 12px; }
    pre .grp.top.bot { border-radius: 12px; }
    pre.short { page-break-inside: avoid; }
    .emo.sp { margin-right: 0.3em; }
    th code { background: transparent; color: inherit; }
    td code.nw, th code.nw { white-space: normal; overflow-wrap: anywhere; }
    a:not([href]) { color: inherit; text-decoration: none; }
    /* "Step 1: …" / "Arquivos:" em item de lista fica com o que vem depois */
    li > p.lead-in { page-break-after: avoid; }
    /* ponytail: "Step N" (item de lista) pode ficar no pé da página. Prender a lista
       ao bloco seguinte faz o WeasyPrint 60 recuar a quebra e deixar até 75% da
       página em branco; o rótulo solto é o mal menor. */
    /* "# Título" + "---": a linha não deixa o título sozinho no pé da página */
    h1 + hr, h2 + hr, h3 + hr { page-break-after: avoid; }
    code.nw { white-space: nowrap; }
    a { overflow-wrap: anywhere; }
    pre.diagram { white-space: pre; overflow-wrap: normal; line-height: 1.25; }

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
        /* larguras vêm do conteúdo (_table_widths); fixa para nunca passar da página */
        table-layout: fixed;
        page-break-inside: auto;
    }

    table th,
    table td {
        border: 1px solid #d0d7de;
        padding: 6px 10px;
        text-align: left;
        overflow-wrap: anywhere;  /* só parte token maior que a coluna (URL, ID) */
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

    table.wide { font-size: 0.9em; }
    table.very-wide { font-size: 0.78em; }
    table.wide th, table.wide td, table.very-wide th, table.very-wide td { padding: 4px 5px; }


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

    /* caixa no lugar do marcador: texto e continuação alinham com os outros itens */
    .task-list-item { list-style-type: none; }

    .task-box {
        display: inline-block;
        width: 0.8em;
        height: 0.8em;
        line-height: 0.8em;
        border: 1.2px solid #5c5c5c;
        border-radius: 3px;
        margin-left: -1.35em;
        margin-right: 0.45em;
        text-align: center;
        font-size: 0.95em;
        font-family: 'DejaVu Sans', sans-serif;
        color: #141414;
        vertical-align: -0.05em;
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

    faces_css, families = font_faces_css(fonts_dir, 'assets/fonts/')
    if families:
        # Clash Display nos títulos, Satoshi/system no corpo
        body_font = "'Satoshi', " if 'Satoshi' in families else ""
        css_to_use += f"""
            {faces_css}
            body {{ font-family: {body_font}-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            h1, h2, h3, h4, h5, h6 {{ font-family: 'Clash Display', {body_font}-apple-system, sans-serif; }}
            """

    # Elemento de rodapé (logo) como running element para @page @bottom-left
    footer_logo_html = f"<div class=\"footer-left\"><img src=\"{html.escape(logo_path)}\" alt=\"logo\"></div>" if logo_path else ""

    cover_html = build_cover_html(cover_data)

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
        <div class="md-body">{html_content}</div>
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
