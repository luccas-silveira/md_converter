# MD Converter — Markdown → PDF (CLI e Web)

Conversor de Markdown para PDF com renderização HTML/CSS via WeasyPrint. Inclui:

- Conversão individual e em lote via CLI
- Servidor web com frontend (upload, preview e download)
- Capa automática baseada em mockup (imagem de fundo) com campos sobrepostos
- Rodapé com logo (inferior esquerdo) e número da página (inferior direito)
- Suporte a CSS customizado e fontes locais (pasta `fonts/`)


## Requisitos

- Python 3.10+
- Dependências Python: `weasyprint`, `markdown2`, `flask`, `gunicorn` (opcional p/ prod)
- Linux (precisa das libs do WeasyPrint):
  - `libcairo2`, `libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf2.0-0`
- macOS: funciona direto com `pip install weasyprint` (se faltar Cairo/Pango, use Homebrew)


## Estrutura do projeto

- `md_to_pdf.py`: núcleo da conversão (Markdown → HTML → PDF), CSS padrão, capa, fontes, rodapé
- `server.py`: backend Flask (serve `front.html` e rota `/convert-md`)
- `front.html`: frontend com upload, form de capa, barra de progresso, preview e download
- `capa mockup.jpg`: mockup em branco da capa (imagem usada como background da 1ª página)
- `logo_zoi.png`: logo usada no rodapé (inferior esquerdo)
- `fonts/`: fontes locais (ex.: arquivos contendo “modica” e/ou “clash” no nome)


## Uso — CLI

- Um arquivo:
  - `python md_to_pdf.py arquivo.md`
  - saída: `arquivo.pdf` (na mesma pasta)
- Arquivo com nome de saída e CSS custom:
  - `python md_to_pdf.py arquivo.md -o saida.pdf --css custom.css`
- Conversão em lote (todos `.md` de um diretório):
  - `python md_to_pdf.py --batch ./documentos -o ./pdfs`

Notas:
- Logo: se `--logo` não for passado, procura `logo_zoi.png` ao lado do `.md` e na raiz do app.
- CSS custom: é concatenado após o CSS padrão (sobrescreve o que precisar).


## Uso — Web (frontend + preview)

1) `python server.py`
2) Abra http://127.0.0.1:5000
3) Selecione o `.md`, informe os dados da capa (opcionais) e clique em “Converter arquivo”.
4) O PDF renderizado aparece no preview e o botão “Download” salva o arquivo.


## Capa (mockup + campos)

- A primeira página usa `capa mockup.jpg` (ou `capa_mockup.jpg`/`capa-mockup.jpg`/`capa.jpg`/`capa.png`) como fundo.
- Os campos são sobrepostos em posições fixas (mm), seguindo o modelo preenchido:
  - Topo direito: email, site, nome do representante (rótulo desabilitado por padrão)
  - Abaixo de “Relatório”: subtítulo e descrição
  - Faixa verde inferior: “Preparado por” (nome, e‑mail, telefone) e data
- Configuração/estilo em `md_to_pdf.py` (CSS embutido — seletores `.cover-*`).

Personalizações comuns:
- Posições: edite `top/left/right/bottom` (em mm) dos seletores `.cover-*`.
- Fonte: por padrão, as informações da capa usam “Modica” se encontrada (pasta `fonts/`).
- Ocultar itens (ex.: rótulo do representante):
  - Já desabilitado no código; se quiser ocultar mais, ajuste HTML/CSS das `.cover-*`.


## Fontes e CSS

- Coloque arquivos de fonte na pasta `fonts/`. O script detecta automaticamente:
  - Corpo/títulos: busca arquivos com “modica” (corpo) e “clash” (títulos)
  - Formatos aceitos: `.woff2`, `.woff`, `.ttf`, `.otf`
- Para a capa, forçamos “Modica” nas informações (pode trocar no CSS `.cover-*`).
- CSS custom: opcionalmente forneça um arquivo com `--css custom.css` (CLI) — é somado ao padrão.


## Rodapé e numeração

- Logo: canto inferior esquerdo (margin box `@bottom-left`).
- Numeração: canto inferior direito com `counter(page)` (apenas o número da página).
- Ajustes no CSS padrão dentro de `md_to_pdf.py`.


## Dependências e instalação local

```bash
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -U pip wheel
pip install weasyprint markdown2 flask gunicorn
```

Linux (se faltar libs do WeasyPrint):

```bash
sudo apt update && sudo apt install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```


## Deploy (VPS)

- Crie o diretório do app (ex.: `/srv/mdconverter`) e envie os arquivos: `md_to_pdf.py`, `server.py`, `front.html`, `capa mockup.jpg`, `logo_zoi.png`, `fonts/`.
- Ambiente Python em produção:
  - `python3 -m venv venv && . venv/bin/activate`
  - `pip install weasyprint markdown2 flask gunicorn`
  - Teste: `venv/bin/gunicorn -b 127.0.0.1:5000 server:app`
- systemd (exemplo `/etc/systemd/system/mdconverter.service`):
  - ExecStart: `/srv/mdconverter/venv/bin/gunicorn -b 127.0.0.1:5000 server:app --workers 2`
  - `sudo systemctl daemon-reload && sudo systemctl enable --now mdconverter`
- Nginx (reverse proxy):
  - Proxy para `http://127.0.0.1:5000` e habilite HTTPS com Certbot se tiver domínio.


## API (backend)

- `GET /` → serve `front.html` e arquivos estáticos da raiz do app
- `POST /convert-md` → multipart/form-data
  - `file`: arquivo `.md` (obrigatório)
  - Campos opcionais da capa (enviados pelo front):
    - `cover_top_email`, `cover_top_site`, `cover_rep_nome`, `cover_subtitulo`, `cover_descricao`, `cover_prep_nome`, `cover_prep_email`, `cover_prep_phone`, `cover_data`
  - Resposta: PDF (`application/pdf`)


## Dicas e troubleshooting

- Preview não aparece no iframe: alguns navegadores bloqueiam PDF embutido; use o botão "Download".
- Capa desalinhada: ajuste `object-position` da `.cover-bg` ou as coordenadas em mm dos blocos `.cover-*`.
- Fontes não aplicadas: confirme nomes dos arquivos (contendo "modica"/"clash") e a pasta `fonts/` ao lado do app.
- Logo não aparece: verifique `logo_zoi.png` na raiz ou passe `--logo` na CLI; no web, o app procura na raiz automaticamente.


## Segurança

### Sanitização Automática de Nomes de Arquivo

O MD Converter implementa **proteção contra ataques de path traversal** (CWE-22) através de sanitização automática de todos os nomes de arquivo enviados por usuários.

**Características de Segurança:**

- ✅ **Sanitização automática**: Todos os filenames são processados via `werkzeug.secure_filename()`
- ✅ **Bloqueio de path traversal**: Sequências como `..`, `/`, `\` e null bytes são removidos
- ✅ **Geração de nomes seguros**: Filenames completamente inválidos são substituídos por identificadores únicos (UUID)
- ✅ **Limite de comprimento**: Nomes de arquivo são truncados para máximo de 200 caracteres
- ✅ **Logging de tentativas suspeitas**: Tentativas de path traversal são registradas nos logs com IP do cliente

**Exemplos de Transformação:**

| Entrada do Usuário | Saída Sanitizada |
|-------------------|------------------|
| `../../etc/passwd` | `etc_passwd.md` |
| `/etc/passwd` | `etc_passwd.md` |
| `file<>name?.md` | `filename.md` |
| `arquivo\x00.exe.md` | `arquivo.md` |
| *(nome vazio)* | `uploaded_file_a1b2c3d4.md` |

**Monitoramento:**

Para verificar tentativas de ataque nos logs:

```bash
# Ver tentativas de path traversal
docker logs md-converter | grep "path traversal"

# Contar tentativas suspeitas
docker logs md-converter --since 24h | grep -i "path traversal" | wc -l
```

Para mais detalhes sobre segurança, consulte [`docs/SECURITY.md`](docs/SECURITY.md).


## Performance

### Lazy Loading do Modelo Whisper

O MD Converter implementa **lazy loading com pre-carregamento configurável** para o modelo Whisper, otimizando o tempo de inicialização e consumo de memória.

**Como Funciona:**

- **Lazy Loading**: O modelo Whisper só é carregado quando realmente necessário (primeira transcrição de áudio)
- **Pre-loading Opcional**: Variável de ambiente `WHISPER_PRELOAD` permite carregar o modelo durante o startup
- **Thread-Safe**: Implementação com double-checked locking previne race conditions
- **Singleton Pattern**: Modelo é carregado apenas uma vez e reutilizado em todas as requisições

**Configuração:**

```bash
# No arquivo .env

# Modelo Whisper (opções: tiny, base, small, medium, large)
WHISPER_MODEL=base

# Pre-loading do modelo durante startup
# - true: Carrega modelo no startup (~60s delay, mas transcrições sempre rápidas)
# - false: Carrega modelo na primeira transcrição (startup rápido ~5s, primeira transcrição lenta)
WHISPER_PRELOAD=true
```

**Recomendações de Uso:**

| Cenário | WHISPER_PRELOAD | Motivo |
|---------|-----------------|--------|
| **Produção (uso frequente)** | `true` | Garante que todas transcrições sejam rápidas, evita timeout na primeira requisição |
| **Desenvolvimento** | `false` | Startup rápido, economiza memória durante desenvolvimento |
| **Servidor com poucos recursos** | `false` | Economiza ~350MB de RAM quando transcrição não está em uso |

**Métricas de Performance:**

| Métrica | Sem Lazy Loading | Com Lazy Loading (PRELOAD=false) | Com Lazy Loading (PRELOAD=true) |
|---------|------------------|-----------------------------------|----------------------------------|
| **Startup Time** | 30-60s | ~5-10s ✅ | 30-60s |
| **Memória em Idle** | ~500MB | ~150MB ✅ | ~500MB |
| **Primeira Transcrição** | Instantânea | +30-60s ⚠️ | Instantânea ✅ |
| **Transcrições Subsequentes** | Instantânea | Instantânea | Instantânea |

**Logs de Lazy Loading:**

```bash
# Ver quando o modelo está sendo carregado
docker logs md-converter | grep "Lazy Loading"

# Exemplo de saída:
# [Startup] WHISPER_PRELOAD=true detectado - carregando modelo Whisper antecipadamente...
# [Lazy Loading] Carregando modelo Whisper 'base'... (isso pode demorar 30-60s)
# [Lazy Loading] Modelo Whisper 'base' carregado com sucesso!
```

**Troubleshooting:**

- **Problema**: Primeira transcrição sempre demora muito
  - **Solução**: Configure `WHISPER_PRELOAD=true` no arquivo `.env`

- **Problema**: Container demora muito para ficar healthy
  - **Solução**: Se `WHISPER_PRELOAD=true`, o healthcheck `start_period` está configurado para 90s (normal)

- **Problema**: Memória alta mesmo sem usar transcrições
  - **Solução**: Configure `WHISPER_PRELOAD=false` para economizar ~350MB de RAM


## Licença

Uso interno/proprietário (não definido). Adapte conforme necessário.
