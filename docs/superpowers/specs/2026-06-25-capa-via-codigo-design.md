# Capa via código (réplica fiel) — Design

**Data:** 2026-06-25
**Status:** Aprovado
**Arquivo-alvo:** `app/utils/md_to_pdf.py` (bloco de capa, ~linhas 116-182 CSS e 450-489 HTML)

## Objetivo

Substituir a capa atual — `capa mockup.jpg` usado como `background` + campos sobrepostos
em mm — por uma capa **100% gerada em HTML/CSS**, visualmente **idêntica** ao JPG de hoje.
O JPG sai do caminho de renderização.

Motivação (do grilling): a capa deve "nascer do código" — editável (endereço, cor, texto
sem reexportar imagem no Figma) e em vetor (nítida em qualquer zoom/impressão), eliminando a
dependência de um raster e do alinhamento frágil de campos sobre pixels.

Decisão de escopo: **réplica fiel**, não redesign. Exploramos variantes de layout (V1/V2/V3 e
fusões) no companion visual; o usuário concluiu que a capa original já está boa. Portanto o
entregável é reproduzir o existente 1:1, só que em código.

## Estado atual (o que reproduzir)

Hoje `md_to_pdf()` monta `cover_html` com:
- `<img class="cover-bg">` = o JPG inteiro (régua, contatos, sol, wordmark, faixa verde, rótulos)
- Campos sobrepostos via `position:absolute` em mm: top-right (email/site/rep), headblock
  (subtítulo/descrição), prep (nome/email/phone), data.

O JPG é A4 a 300dpi: **2480×3508 px** → fator **1 px ≈ 0,0847 mm** (210/2480 e 297/3508).

### Elementos ESTÁTICOS (chapados no JPG → viram template fixo)
- Régua preta horizontal no topo.
- Coluna de contato esquerda: `ZOI` / `Benjamin Constant 2839` / `Joinville — SC, Brasil` /
  `+55 (47) 9 9638-4996`.
- Coluna de contato direita: `contato@zoi.tech` / `www.zoitech.com.br` /
  `Representante Técnico` / `Luccas Silveira`.
- Sol verde + wordmark **"Relatório"** (fonte Clash Display, preto) + a dropline vertical fina
  com a setinha que desce do conjunto.
- Faixa verde inferior (#b5ff81) + rótulos `Preparado por:` e `Data:`.

### Elementos DINÂMICOS (continuam vindos de `cover_data`, comportamento inalterado)
- `subtitulo`, `descricao` (headblock abaixo do wordmark).
- `preparado_nome`, `preparado_email`, `preparado_phone` (na faixa verde).
- `data` (na faixa verde).
- `topo_direito_email`, `topo_direito_site`, `representante_nome`: viram **override opcional** —
  se preenchidos no form, substituem o texto estático da coluna direita; se vazios, mostra o
  padrão ZOI acima. (Preserva o input do form sem quebrar a aparência default.)

## Abordagem técnica

### 1. Sol → SVG vetorial recolorível
- `brew install potrace` (não está instalado; só ImageMagick presente, que não vetoriza).
- PNG de origem: `assets/images/sol_zoi.png` (do link enviado; 796×801, RGBA transparente, verde
  ZOI). Salvar o PNG no repo.
- Pipeline: PNG → flatten alpha pra bitmap (PBM/PGM) via ImageMagick → `potrace` → SVG path.
- Pós-processo: remover `fill` fixo do path e expor cor via CSS (`fill: var(--sun)` ou
  `currentColor`), pra ser recolorível. Embutir o SVG inline no `cover_html` (sem arquivo solto
  na renderização).
- Guard: o SVG gerado deve ter o miolo vazado (a forma é um anel de raios, centro transparente).

### 2. Capa em HTML/CSS
- Manter `@page cover { margin:0 }` e `.cover-page { width:210mm; height:297mm; position:relative }`.
- Trocar o `<img class="cover-bg">` por blocos posicionados (`position:absolute` em mm, medidos do
  JPG) para cada elemento estático + os dinâmicos já existentes.
- Medir posições/tamanhos reais no JPG (pixel → mm) para bater fiel: topo da régua, x/y das
  colunas de contato, posição e tamanho do sol+wordmark, geometria da dropline, altura/topo da
  faixa verde, posição dos rótulos.
- Fontes: wordmark em Clash Display (já detectada/embutida em `assets/fonts/`); corpo na fonte
  Modica/padrão já usada. Sem dependência nova de fonte.
- Verde: `#b5ff81` (já é a cor de acento no código).

### 3. Limpeza
- Remover `_find_cover_template()` e toda a lógica de localizar/escapar o template de imagem.
- Remover o parâmetro de caminho do mockup do fluxo de capa (o `cover_template_path` da
  assinatura pode permanecer aceito-e-ignorado para não quebrar callers, ou ser removido — decidir
  no plano; preferência: remover se nenhum caller usa).
- `capa mockup.jpg` fica órfão; pode ser apagado em commit separado (fora do escopo de render).

## Arquivos afetados
- `app/utils/md_to_pdf.py` — CSS da capa (~116-182) e construção do `cover_html` (~450-489).
- `assets/images/sol_zoi.png` — novo asset (origem do traço).
- SVG do sol — inline no código (ou um pequeno helper que retorna a string SVG).

## Verificação
- Render no Docker (`docker compose up -d --build`) com um doc usando dados de capa.
- Comparar o PDF gerado com a capa atual (JPG) lado a lado: posições, tamanhos, cor, fonte do
  wordmark, dropline, faixa verde. Diferença visual deve ser imperceptível.
- Conferir que campos dinâmicos (subtítulo, descrição, preparado, data) caem nos mesmos lugares.
- Conferir que o sol está nítido em zoom alto (ganho do vetor sobre o raster).

## Fora de escopo
- Qualquer redesign de layout/hierarquia (explorado e descartado).
- Mexer no corpo do documento, rodapé das páginas internas, ou outras rotas.
- Tornar o endereço/contato configurável por env/form além do override de topo-direito que já existe.

## Riscos
- **Fidelidade de posição:** depende de medir bem o JPG. Mitigação: extrair coords por pixel e
  converter, ajustar no Docker comparando com o original.
- **potrace ausente em produção:** o traço é feito **uma vez** em dev e o SVG vai versionado no
  código — produção não precisa de potrace em runtime.
- **Clash Display na faixa/wordmark:** se a fonte não embutir no WeasyPrint, o wordmark cai em
  fallback. Já é risco pré-existente (a capa atual também usa Clash nos campos sobrepostos).
