# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Comandos essenciais

**Desenvolvimento local:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py            # Flask dev server em http://127.0.0.1:5000/relatorio/
```

**Docker (recomendado para produção):**
```bash
docker compose up -d --build
curl http://localhost:8080/relatorio/healthz
docker compose logs -f md-converter
```

**Variáveis de ambiente importantes:**
- `OPENAI_API_KEY`: habilita o resumo com IA; sem ela, o módulo de reunião cai para template padrão
- `OPENAI_MODEL`: modelo usado no resumo com OpenAI (default atual `gpt-4o-mini`)
- `SECRET_KEY`: obrigatório em produção
- `WHISPER_MODEL`: default `base`; `tiny` é mais seguro para VPS com pouca RAM
- `MAX_CONTENT_LENGTH`: limite de upload em bytes (default efetivo atual: 1GB)

## Arquitetura

A aplicação é um servidor Flask com **Application Factory** (`app/__init__.py:create_app()`), exposto via `server.py`.

Todas as rotas são servidas sob o prefixo `/relatorio`.

**Blueprints:**
- `app/routes/main.py` → `GET /relatorio/` — serve `front.html` e injeta o limite de upload
- `app/routes/conversion.py` → `POST /relatorio/convert-md` — recebe Markdown enviado por arquivo ou texto colado e retorna PDF
- `app/routes/progress.py` → `GET /relatorio/progress/<session_id>` — Server-Sent Events para acompanhar progresso em tempo real
- `app/routes/meeting.py` → `POST /relatorio/process-meeting` — recebe texto/áudio/vídeo, transcreve quando necessário, resume e retorna PDF

**Núcleo de conversão:**
- `app/utils/md_to_pdf.py` — função `md_to_pdf()` que converte Markdown → HTML → PDF via WeasyPrint. Centraliza CSS padrão, lógica de capa, logo no rodapé e CLI auxiliar.

**Assets esperados em `assets/`:**
- `assets/images/logo_zoi.png` — logo do rodapé
- `assets/images/capa mockup.jpg` — imagem de fundo da primeira página
- `assets/fonts/` — fontes locais consumidas pelo CSS de geração

**Módulo de reunião (IA):**
- Suporta `.txt`, `.md`, `.mp3`, `.wav`, `.mp4`, `.avi`, `.mov`, `.m4a`
- Usa `prompts/prompt_resumo.md` para o resumo com OpenAI
- Limita o trecho enviado ao modelo aos primeiros 4000 caracteres da transcrição
- Continua disponível sem `OPENAI_API_KEY`, retornando um resumo padrão

**Progresso via SSE:**
- Estado armazenado em memória (`progress_data`) com lock de thread
- Cada requisição usa um `session_id`
- O armazenamento é por processo; em produção, `WORKERS=1` evita inconsistência entre upload e stream SSE

**Frontend:**
- SPA single-file em `app/templates/front.html` (sem framework JS)
- Três modos: upload de arquivo, colagem de texto e resumo de reunião
- O fluxo atual faz download automático do PDF; não existe preview em iframe

**Configuração:**
- `app/__init__.py` lê as variáveis de ambiente efetivas usadas no runtime (não há módulo de config separado)
- `UPLOAD_FOLDER` default `/tmp`; no Docker Compose usa `/data/uploads`
