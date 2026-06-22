# MD Converter — Markdown e Reuniões em PDF

Aplicação Flask para gerar PDFs no padrão ZOI a partir de Markdown ou de resumos de reunião. A interface principal roda sob o prefixo `/relatorio` e oferece três fluxos no frontend:

- envio de arquivo Markdown
- colagem de texto Markdown
- processamento de reunião com IA a partir de texto, áudio ou vídeo

O projeto também inclui um utilitário CLI em `app/utils/md_to_pdf.py`, usando o mesmo pipeline de conversão para PDF.


## Principais recursos

- Conversão Markdown → HTML → PDF com WeasyPrint
- Capa automática com mockup de fundo e campos posicionados em milímetros
- Rodapé com logo no canto inferior esquerdo e numeração no canto inferior direito
- Barra de progresso via Server-Sent Events (SSE) durante o processamento
- Download automático do PDF ao final da geração
- Resumo de reunião com Whisper + OpenAI quando disponível, com fallback para template padrão


## Estrutura do projeto

- `server.py` — ponto de entrada local; cria a aplicação e registra logs de boot
- `app/__init__.py` — application factory, blueprints, handlers de erro e `GET /relatorio/healthz`
- `app/routes/main.py` — `GET /relatorio/`, entrega o frontend e injeta o limite atual de upload
- `app/routes/conversion.py` — `POST /relatorio/convert-md`, converte Markdown enviado pelo frontend/API em PDF
- `app/routes/meeting.py` — `POST /relatorio/process-meeting`, processa texto/áudio/vídeo e gera PDF de resumo
- `app/routes/progress.py` — `GET /relatorio/progress/<session_id>`, expõe o progresso em memória por `session_id`
- `app/utils/md_to_pdf.py` — núcleo da conversão, capa, rodapé, CLI e normalização básica de Markdown
- `app/templates/front.html` — SPA single-file sem framework JS, com três modos de entrada
- `assets/images/logo_zoi.png` — logo usada no rodapé
- `assets/images/capa mockup.jpg` — imagem base da capa
- `prompts/prompt_resumo.md` — prompt usado para o resumo com IA


## Requisitos

- Python 3.11 recomendado para desenvolvimento local
- Bibliotecas de sistema exigidas pelo WeasyPrint
- `ffmpeg` para transcrição local de áudio/vídeo com Whisper
- Docker + Docker Compose v2 para o fluxo recomendado de produção

Linux/Debian ou Ubuntu:

```bash
sudo apt update && sudo apt install -y \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 \
  shared-mime-info \
  ffmpeg
```


## Instalação local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

Aplicação local:

- UI: [http://127.0.0.1:5000/relatorio/](http://127.0.0.1:5000/relatorio/)
- Healthcheck: [http://127.0.0.1:5000/relatorio/healthz](http://127.0.0.1:5000/relatorio/healthz)


## Variáveis de ambiente

| Variável | Uso | Default atual |
| --- | --- | --- |
| `OPENAI_API_KEY` | habilita resumo com OpenAI no fluxo de reunião | ausente |
| `OPENAI_MODEL` | modelo usado no resumo com IA | `gpt-4o-mini` |
| `WHISPER_MODEL` | modelo Whisper carregado no boot | `base` |
| `SECRET_KEY` | chave do Flask para produção | `dev-key-change-in-production` |
| `MAX_CONTENT_LENGTH` | limite máximo de upload em bytes | `1073741824` (1GB) |
| `UPLOAD_FOLDER` | diretório base de arquivos temporários | `/tmp` |
| `SEND_FILE_MAX_AGE` | cache de arquivos servidos pelo Flask | `0` |
| `LOG_LEVEL` | nível de log do servidor | `INFO` |

Observações:

- Se `OPENAI_API_KEY` não estiver configurada, o módulo de reunião continua disponível, mas gera um resumo padrão sem IA.
- O modelo Whisper é carregado na importação de `app/routes/meeting.py`; se esse carregamento falhar, a aplicação continua operando para Markdown e texto.


## Uso pelo frontend

1. Inicie a aplicação com `python server.py` ou `docker compose up -d --build`.
2. Abra `/relatorio/`.
3. Escolha um dos três modos.

### Enviar arquivo

- Recebe um arquivo pelo campo `file`.
- O backend aceita o upload mesmo sem extensão `.md`; nesses casos ele renomeia internamente para `.md` e trata o conteúdo como Markdown.
- O formulário de capa permite preencher subtítulo, descrição, responsável, e-mail, telefone e data.

### Colar texto

- O texto digitado é enviado como um arquivo temporário `documento.md`.
- Usa o mesmo endpoint de conversão e a mesma capa do modo de upload.

### Resumo de reunião

- Aceita `.txt`, `.md`, `.mp3`, `.wav`, `.mp4`, `.avi`, `.mov` e `.m4a`.
- Para arquivos de texto, o conteúdo é lido diretamente.
- Para áudio e vídeo, a transcrição usa Whisper em português.
- O resumo com IA usa `prompts/prompt_resumo.md` e envia até os primeiros 4000 caracteres da transcrição ao modelo configurado.
- Se a IA não estiver disponível, o sistema cai para um template Markdown padrão antes de gerar o PDF.
- Nesse modo, o subtítulo da capa passa a ser o título da reunião e a descrição vira `Reunião realizada em <data>` quando a data é informada.

Fluxo de saída:

- a barra de progresso é atualizada via SSE
- ao concluir, o frontend inicia o download automaticamente
- não há preview embutido em iframe no estado atual da interface


## Uso via CLI

O utilitário CLI está em `app/utils/md_to_pdf.py`.

Um arquivo:

```bash
python app/utils/md_to_pdf.py arquivo.md
```

Definindo o PDF de saída:

```bash
python app/utils/md_to_pdf.py arquivo.md -o saida.pdf
```

Com CSS adicional:

```bash
python app/utils/md_to_pdf.py arquivo.md --css custom.css
```

Em lote:

```bash
python app/utils/md_to_pdf.py --batch ./documentos -o ./pdfs
```

Notas sobre a CLI:

- se `--logo` não for informado, o utilitário procura `logo_zoi.png` ao lado do Markdown e, quando o diretório base permitir, em `assets/images/logo_zoi.png`
- a imagem de capa é procurada em `assets/images/` dentro do diretório base resolvido para o arquivo Markdown
- para reutilizar os assets deste repositório com previsibilidade, execute a CLI a partir da raiz do projeto ou informe caminhos explícitos quando o Markdown estiver fora dela


## Assets e layout

### Capa

A primeira página usa uma imagem de fundo localizada automaticamente nesta ordem:

- `assets/images/capa mockup.jpg`
- `assets/images/capa_mockup.jpg`
- `assets/images/capa-mockup.jpg`
- `assets/images/capa.png`
- `assets/images/capa.jpg`

Também existem fallbacks equivalentes na raiz do diretório base, preservados por compatibilidade.

### Fontes

- Os assets de fonte ficam em `assets/fonts/`.
- O gerador procura uma fonte local com `clash` no nome do arquivo para os títulos.
- Os demais elementos usam a família `Satoshi`/sans-serif definida no CSS do gerador, com fallback para fontes do sistema quando necessário.


## API HTTP

Todas as rotas ficam sob `/relatorio`.

- `GET /relatorio/` — frontend
- `GET /relatorio/healthz` — healthcheck simples
- `GET /relatorio/progress/<session_id>` — stream SSE de progresso
- `POST /relatorio/convert-md` — conversão Markdown → PDF
- `POST /relatorio/process-meeting` — resumo de reunião → PDF

Campos de `POST /relatorio/convert-md`:

- `file` obrigatório
- `session_id` opcional
- `css` opcional
- `logo` opcional
- campos de capa opcionais: `cover_top_email`, `cover_top_site`, `cover_rep_label`, `cover_rep_nome`, `cover_subtitulo`, `cover_descricao`, `cover_prep_nome`, `cover_prep_email`, `cover_prep_phone`, `cover_data`

Campos de `POST /relatorio/process-meeting`:

- `meeting_file` obrigatório
- `session_id` opcional
- `meeting_participants`, `meeting_date`, `meeting_title` opcionais
- campos de capa de responsável/data também podem ser enviados, mas `subtitulo` e `descricao` são sobrescritos pelo fluxo da reunião


## Observações de operação

- O estado de progresso fica em memória do processo atual. Em produção, manter `WORKERS=1` evita divergência entre o request de upload e o stream SSE.
- O fluxo Docker do projeto combina volume persistente em `/data/uploads` no `docker-compose.yml` com defaults de `WORKERS=1` e `THREADS=2` definidos no `Dockerfile`.
- O healthcheck Docker usa `GET /relatorio/healthz`.


## Troubleshooting

- O navegador não abriu um preview:
  Isso é esperado. O fluxo atual faz download automático do PDF.

- Recebi HTTP 413:
  Verifique `MAX_CONTENT_LENGTH`; o default atual é 1GB.

- O resumo saiu sem IA:
  Confira `OPENAI_API_KEY` e os logs do módulo `app.routes.meeting`.

- Áudio/vídeo não transcreve:
  Confira `ffmpeg`, `WHISPER_MODEL` e a memória disponível.

- A barra de progresso não acompanha a conversão em produção:
  Garanta afinidade de processo ou mantenha `WORKERS=1`, já que o progresso é armazenado em memória local.


## Deploy

As instruções operacionais de Docker/Gunicorn estão em `DEPLOY.md`.
