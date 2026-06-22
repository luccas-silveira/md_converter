# Graph Report - .  (2026-06-19)

## Corpus Check
- Corpus is ~30,289 words - fits in a single context window. You may not need a graph.

## Summary
- 85 nodes · 156 edges · 13 communities (10 shown, 3 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.86)
- Token cost: 57,366 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_API & Architecture Docs|API & Architecture Docs]]
- [[_COMMUNITY_Meeting Flow & SSE Progress|Meeting Flow & SSE Progress]]
- [[_COMMUNITY_Deployment & Config|Deployment & Config]]
- [[_COMMUNITY_Route Handlers Core|Route Handlers Core]]
- [[_COMMUNITY_PDF Cover Design|PDF Cover Design]]
- [[_COMMUNITY_MD→PDF CLI|MD→PDF CLI]]
- [[_COMMUNITY_Conversion → PDF Pipeline|Conversion → PDF Pipeline]]
- [[_COMMUNITY_Frontend Route (SPA)|Frontend Route (SPA)]]
- [[_COMMUNITY_ZOI Logo Footer|ZOI Logo Footer]]
- [[_COMMUNITY_Server Entrypoint|Server Entrypoint]]
- [[_COMMUNITY_Markdown Normalization|Markdown Normalization]]

## God Nodes (most connected - your core abstractions)
1. `md_to_pdf()` - 11 edges
2. `update_progress()` - 10 edges
3. `create_app()` - 8 edges
4. `process_meeting()` - 8 edges
5. `convert_md()` - 7 edges
6. `process_meeting_file()` - 6 edges
7. `progress_stream()` - 6 edges
8. `front.html (SPA single-file)` - 6 edges
9. `Capa Mockup (ZOI Report Cover Background)` - 6 edges
10. `batch_convert()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Resumo padrão (fallback sem IA)` --semantically_similar_to--> `OpenAI (resumo IA)`  [INFERRED] [semantically similar]
  /Users/luccassilveira/Desktop/Projetos_ZOI/md_converter/USAGE.md → /Users/luccassilveira/Desktop/Projetos_ZOI/md_converter/README.md
- `create_app()` --references--> `index()`  [INFERRED]
  app/__init__.py → app/routes/main.py
- `create_app()` --references--> `progress_stream()`  [INFERRED]
  app/__init__.py → app/routes/progress.py
- `convert_md()` --semantically_similar_to--> `process_meeting()`  [INFERRED] [semantically similar]
  app/routes/conversion.py → app/routes/meeting.py
- `batch_convert()` --calls--> `Path`  [INFERRED]
  app/utils/md_to_pdf.py → app/routes/meeting.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Docs de deploy (Docker/Gunicorn/WORKERS=1)** — deploy_unico, concept_docker, concept_gunicorn, concept_workers_single, composeyml_md_converter [EXTRACTED 0.85]
- **Fluxo Markdown → PDF com capa e progresso** — concept_route_convert_md, concept_md_pipeline, concept_weasyprint, concept_cover_capa, concept_sse_progress [EXTRACTED 0.85]
- **Fluxo de resumo de reunião (IA)** — concept_route_process_meeting, concept_whisper, concept_openai, concept_env_openai_api_key, concept_env_whisper_model, prompts_prompt_resumo, concept_meeting_fallback [EXTRACTED 0.85]
- **SSE progress trio sharing progress_data** — routes_progress_update_progress, routes_progress_get_progress, routes_progress_progress_stream, concept_progress_data_store [EXTRACTED 1.00]
- **Meeting AI summarization flow** — routes_meeting_process_meeting, routes_meeting_process_meeting_file, routes_meeting_generate_meeting_summary [EXTRACTED 1.00]
- **Blueprints registered by create_app factory** — app_init_create_app, routes_main_index, routes_conversion_convert_md, routes_progress_progress_stream, routes_meeting_process_meeting [INFERRED 0.95]

## Communities (13 total, 3 thin omitted)

### Community 0 - "API & Architecture Docs"
Cohesion: 0.24
Nodes (13): Application Factory (create_app), Pipeline Markdown → HTML → PDF, Resumo padrão (fallback sem IA), OpenAI (resumo IA), POST /relatorio/convert-md, POST /relatorio/process-meeting, GET /relatorio/progress/<session_id>, GET /relatorio/ (frontend) (+5 more)

### Community 1 - "Meeting Flow & SSE Progress"
Cohesion: 0.18
Nodes (14): Application factory do MD Converter.  Centraliza o boot da aplicação Flask, regi, In-memory progress_data store, generate_meeting_summary(), process_meeting_file(), Rotas para processamento de reuniões e geração de resumos em PDF.  O fluxo tenta, Processa um arquivo de reunião e devolve o resumo final em Markdown.      Tipos, Gera um resumo estruturado em Markdown.      Quando a OpenAI está configurada, u, get_progress() (+6 more)

### Community 2 - "Deployment & Config"
Cohesion: 0.27
Nodes (12): docker-compose.yml (md-converter service), Capa automática (mockup de fundo), Docker / Docker Compose, MAX_CONTENT_LENGTH, OPENAI_API_KEY, OPENAI_MODEL, SECRET_KEY, UPLOAD_FOLDER (+4 more)

### Community 3 - "Route Handlers Core"
Cohesion: 0.43
Nodes (7): create_app(), Cria a aplicação Flask usando variáveis de ambiente como fonte de verdade., Path, convert_md(), Recebe um arquivo textual, aplica dados opcionais de capa e devolve um PDF., process_meeting(), Processa texto/áudio/vídeo de reunião e retorna um PDF com o resumo.

### Community 4 - "PDF Cover Design"
Cohesion: 0.48
Nodes (7): Capa Mockup (ZOI Report Cover Background), ZOI Brand Palette (Lime Green + Black on White), Green Bottom Band (Preparado por / Data), Minimal A4 Letterhead Layout Rationale, PDF Generator Text Overlay Zones, Centered 'Relatório' Title with Sunburst Logo, Top Two-Column Contact Block

### Community 5 - "MD→PDF CLI"
Cohesion: 0.40
Nodes (5): batch_convert(), main(), Utilitário de conversão de Markdown para PDF usado pela web e pela CLI.  Além da, Converte todos os arquivos `.md` de um diretório para PDF.          Args:, Interface CLI simples para uso manual do conversor.

### Community 6 - "Conversion → PDF Pipeline"
Cohesion: 0.40
Nodes (4): Markdown to HTML to PDF pipeline, Rotas HTTP para conversão de Markdown em PDF.  Este módulo atende tanto o upload, md_to_pdf(), Converte um arquivo Markdown para PDF.          Args:         md_file_path (str)

### Community 7 - "Frontend Route (SPA)"
Cohesion: 0.50
Nodes (3): index(), Rotas principais da aplicação, Renderiza a SPA principal e informa ao frontend o limite atual de upload.

## Knowledge Gaps
- **4 isolated node(s):** `Capa automática (mockup de fundo)`, `ZOI Brand Logo (logo_zoi.png)`, `ZOI Logo Footer Placement in PDF`, `Markdown to HTML to PDF pipeline`
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `md_to_pdf()` connect `Conversion → PDF Pipeline` to `Meeting Flow & SSE Progress`, `Markdown Normalization`, `Route Handlers Core`, `MD→PDF CLI`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `create_app()` connect `Route Handlers Core` to `Meeting Flow & SSE Progress`, `Server Entrypoint`, `Frontend Route (SPA)`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `update_progress()` connect `Meeting Flow & SSE Progress` to `Route Handlers Core`, `Conversion → PDF Pipeline`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `md_to_pdf()` (e.g. with `Markdown to HTML to PDF pipeline` and `Path`) actually correct?**
  _`md_to_pdf()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `create_app()` (e.g. with `Path` and `convert_md()`) actually correct?**
  _`create_app()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `process_meeting()` (e.g. with `create_app()` and `convert_md()`) actually correct?**
  _`process_meeting()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `convert_md()` (e.g. with `create_app()` and `Path`) actually correct?**
  _`convert_md()` has 3 INFERRED edges - model-reasoned connections that need verification._