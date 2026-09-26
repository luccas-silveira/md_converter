"""Regressões do teste com 100 markdowns reais (renderização md → HTML)."""
from app.utils.md_to_pdf import render_markdown, build_cover_html


def test_casos_reais():
    src = (
        "---\ntitle: x\nsummary: y\n---\n# T\n\n"
        "**Files:**\n- a\n- b\n\n"
        "1. passo\n   ```py\n   x=1\n   ```\n2. dois\n\n"
        "- [ ] todo\n- [x] feito\n\n"
        "## \n\n"
        "_it_ git rm --cached a--b\n\n"
        "**Status:** ok\n**Data:** hoje\n\n"
        "[[Nota|alias]] [[Outra]]\n\n"
        "| a | b |\n|---|---|\n| https://example.com/very/long/path/to/something | x |\n\n"
        "x y\n\n"
        "```\n#!/bin/bash\n# comment\ncode\n```\n\n"
        "#hashtag\n\n"
        "- item\n---\n"
    )
    out = render_markdown(src)
    assert 'summary' not in out                                   # front matter some
    assert '<p class="lead-in"><strong>Files:</strong></p>\n<ul>' in out  # lista colada vira lista
    assert '<li>passo<pre class="lines short"><code class="language-py">' in out  # código dentro de lista
    assert '<span class="task-box"></span> todo' in out and '<span class="task-box">✓</span> feito' in out
    assert '<h2' not in out                                       # título vazio removido
    assert '<em>it</em> git rm --cached a--b' in out              # sem travessão, _ênfase_ ok
    assert '<strong>Status:</strong> ok<br />' in out            # metadados em linhas
    assert 'alias Outra' in out                                   # wikilinks
    assert '\u200b' not in out            # sem caractere invisível: corrompia busca/cópia no PDF
    assert ' ' not in out
    assert '>#!/bin/bash</span>' in out and '>code</span>' in out   # código intacto, linha a linha
    assert '<p>#hashtag</p>' in out and '<hr />' in out


def test_prosa_quebrada_em_coluna_continua_junta():
    linha = "palavra " * 9
    out = render_markdown(f"{linha}\n{linha}\n{linha}\nfim.")
    assert '<br' not in out


def test_rotulo_da_capa_vem_do_formulario():
    assert '<b>Cliente</b>' in build_cover_html({'representante_label': 'Cliente'})
    assert '<b>Representante Técnico</b>' in build_cover_html({})


def test_quebras_por_linha():
    prosa = "palavra " * 9
    # "Rótulo:" na linha seguinte quebra; a prosa em coluna continua junta
    out = render_markdown(f"{prosa}\n{prosa}\n**Risco:** alto")
    assert out.count('<br') == 1
    # linha curta cuja próxima palavra caberia: quebra intencional (inciso de lei)
    out = render_markdown(f"{prosa}\nI - curto;\n{prosa}\nfim.")
    assert out.count('<br') == 1


def test_tabela_larga_lista_numerada_e_link_perigoso():
    cab = "|" + "|".join("c%d" % i for i in range(8)) + "|\n|" + "---|" * 8 + "\n"
    out = render_markdown(cab + "|" + "`aaaaaaaaaaaaaaaaaaaaaaaaaaa.bbb`|" * 8 + "\n\n3. tres\n4. quatro\n\n[x](javascript:alert(1))")
    assert 'very-wide' in out and '<th style="width: 12.5%">' in out
    assert '\u200b' not in out
    assert 'counter-reset: list-item 2' in out
    assert 'javascript' not in out


def test_linkify_riscado_e_codigo():
    out = render_markdown("veja DESIGN.md e https://example.com ~caro~ `git status --short`\n")
    assert 'http://DESIGN.md' not in out and 'href="https://example.com"' in out
    assert '<s>caro</s>' in out and '<code class="nw">git status --short</code>' in out


def test_negrito_de_enfase_nao_quebra_e_item_manual_quebra():
    prosa = "palavra " * 9
    out = render_markdown(f"{prosa}\n**ênfase** no meio da frase {prosa}\n")
    assert '<br' not in out
    out = render_markdown(f"{prosa}\n• Produto: x\n• Valor: y\n")
    assert out.count('<br') == 2


def test_codigo_em_grupos_sem_linha_sozinha():
    out = render_markdown("```\n" + "\n".join(f"l{i}" for i in range(10)) + "\n```\n")
    assert out.count('class="grp') == 2 and 'grp top' in out and 'grp bot' in out


def test_uma_frase_por_linha():
    out = render_markdown("Primeira frase longa o bastante para parecer prosa comum de verdade aqui.\nCC art. 413, redução equitativa.\nCPC art. 373, ônus da prova.\n")
    assert out.count('<br') == 2


def test_rotulos_em_negrito():
    prosa = "palavra " * 9
    # rótulo abrindo parágrafo em prosa quebrada: continua corrido
    assert '<br' not in render_markdown(f"**Pausa.** {prosa}\n{prosa}\nfim")
    # ênfase caindo por acaso no começo da linha: corrido
    assert '<br' not in render_markdown(f"{prosa}\n**Cl. 30 — Restrições.** {prosa}\nfim")
    assert '<br' not in render_markdown(f"{prosa}\n**o distrato não narra.** {prosa}\nfim")
    # cláusula nova depois de frase terminada: linha própria
    out = render_markdown(f"{prosa}fim.\n**Cl. 30 — Restrições.** {prosa}\nfim")
    assert out.count('<br') == 1
    # sequência "**X** — …" uma por linha
    assert render_markdown("**Starter** — a\n**Growth** — b\n**Scale** — c\n").count('<br') == 2


def test_rotulos_em_cadeia_so_o_ultimo_prende():
    out = render_markdown("- **Step 2: rodar**\n\nRun:\n\n```\nx\n```\n")
    assert '<ul>' in out and '<p class="lead-in">Run:</p>' in out
