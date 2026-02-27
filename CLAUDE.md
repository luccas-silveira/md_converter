# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos essenciais

**Desenvolvimento local:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py            # Flask dev server em http://127.0.0.1:5000
```

**Docker (recomendado para produção):**
```bash
docker compose up -d --build
curl http://localhost:8080/relatorio/healthz  # verificar saúde
docker compose logs -f md-converter
```

**Variáveis de ambiente necessárias:**
- `OPENAI_API_KEY`: obrigatório para o módulo de reuniões com IA
- `SECRET_KEY`: para produção (gerar com `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `WHISPER_MODEL`: `tiny|base|small` (default `base`; use `tiny` em VPS com pouca RAM)

## Arquitetura

A aplicação é um servidor Flask com **Application Factory** (`app/__init__.py:create_app()`), exposto via `server.py`.

Todas as rotas são servidas sob o prefixo `/relatorio`.

**Blueprints:**
- `app/routes/main.py` → `GET /relatorio/` — serve o frontend `front.html`
- `app/routes/conversion.py` → `POST /relatorio/convert-md` — recebe arquivo `.md` + dados de capa, retorna PDF
- `app/routes/progress.py` → `GET /relatorio/progress/<session_id>` — Server-Sent Events para acompanhar progresso em tempo real
- `app/routes/meeting.py` → `POST /relatorio/process-meeting` — recebe áudio/vídeo/texto, transcreve com Whisper, resume com GPT, retorna PDF (carregado condicionalmente; app funciona sem ele)

**Núcleo de conversão:**
- `app/utils/md_to_pdf.py` — função `md_to_pdf()` que converte Markdown → HTML → PDF via WeasyPrint. Embutida nela: CSS padrão completo, lógica de capa (mockup JPG como background + campos sobrepostos em mm), detecção automática de fontes em `assets/fonts/` (busca por "modica" para corpo e "clash" para títulos), e rodapé com logo e numeração via CSS `@page`.

**Assets esperados em `assets/`:**
- `assets/images/logo_zoi.png` — logo do rodapé (inferior esquerdo)
- `assets/images/capa mockup.jpg` — imagem de fundo da primeira página (aceita também `capa_mockup.jpg`, `capa-mockup.jpg`, `capa.jpg`, `capa.png`)
- `assets/fonts/` — fontes locais (`.woff2`, `.woff`, `.ttf`, `.otf`); detectadas pelo nome do arquivo

**Módulo de reunião (IA):**
- Aceita arquivos `.txt`, `.md` (leitura direta) e `.mp3`, `.wav`, `.mp4`, `.m4a`, `.avi`, `.mov` (transcrição via Whisper)
- Prompt de resumo carregado de `prompts/prompt_resumo.md` com placeholders `<<DATA>>`, `<<NOMES>>`, `<<PARTICIPANTES_INTERNOS>>`, `<<TRANSCRIÇÂO>>`
- Se `OPENAI_API_KEY` não estiver configurada, retorna template padrão sem IA

**Progresso via SSE:**
- Estado de progresso armazenado em memória (`progress_data` dict com lock de thread)
- Cada requisição usa um `session_id` (UUID) para rastrear o progresso independentemente
- Frontend consome o SSE para exibir barra de progresso

**Frontend:**
- SPA single-file em `app/templates/front.html` (sem framework JS)
- Dois modos: "Converter Markdown" e "Processar Reunião com IA"
- Conecta ao SSE antes de enviar o POST, exibe preview do PDF em iframe

**Configuração:**
- `config/settings.py` define classes `Config`, `DevelopmentConfig`, `ProductionConfig`
- `app/__init__.py` lê configs de variáveis de ambiente com defaults (ex.: `MAX_CONTENT_LENGTH` default 1GB)
- `UPLOAD_FOLDER` default `/tmp`; em produção usa volume Docker `/data/uploads`
