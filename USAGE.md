# Guia de Uso - MD Converter

## Limites e restrições

### Tamanho de arquivo

- O limite efetivo é controlado por `MAX_CONTENT_LENGTH`.
- No estado atual do projeto, `app/__init__.py` usa `1GB` por padrão e o `docker-compose.yml` define o mesmo valor.
- O frontend lê esse limite do servidor e bloqueia uploads acima dele antes do envio.

### Escopo de entrada

- Conversão Markdown:
  o frontend foi desenhado para `.md` ou texto colado, mas o backend aceita qualquer upload e o trata como Markdown.

- Reuniões:
  o backend suporta `.txt`, `.md`, `.mp3`, `.wav`, `.mp4`, `.avi`, `.mov` e `.m4a`.

- Arquivos como `.pdf` e `.docx` não entram no fluxo de processamento da rota de reunião.


## Modos da interface

### Enviar arquivo

- Envie um arquivo e aguarde a geração do PDF.
- Os campos de capa são opcionais.
- O arquivo final é baixado automaticamente ao concluir.

### Colar texto

- Cole Markdown diretamente no editor.
- O texto é enviado como um arquivo temporário `documento.md`.
- A capa usa os mesmos campos do modo de upload.

### Resumo de reunião

- Envie uma transcrição (`.txt`, `.md`) ou mídia (`.mp3`, `.wav`, `.mp4`, `.avi`, `.mov`, `.m4a`).
- Informe participantes, data e título da reunião quando disponíveis.
- O subtítulo da capa passa a ser o título da reunião.
- A descrição da capa passa a ser `Reunião realizada em <data>` quando a data é informada.


## Como o processamento funciona

### Conversão Markdown

1. O frontend abre uma conexão SSE em `/relatorio/progress/<session_id>`.
2. O arquivo ou texto é enviado para `/relatorio/convert-md`.
3. O backend grava um arquivo temporário, monta a capa e chama `app/utils/md_to_pdf.py`.
4. O PDF é devolvido na resposta HTTP.

### Resumo de reunião

1. O arquivo é salvo temporariamente.
2. Para `.txt` e `.md`, o conteúdo é lido diretamente.
3. Para áudio ou vídeo, o Whisper transcreve em português.
4. Se `OPENAI_API_KEY` estiver disponível, o resumo usa `prompts/prompt_resumo.md`.
5. Sem OpenAI, o sistema gera um resumo padrão em Markdown.
6. O Markdown final passa pelo mesmo pipeline de PDF.


## Estrutura da saída

### Quando a IA está disponível

O resumo tende a seguir o prompt em `prompts/prompt_resumo.md`, com estes blocos:

1. Resumo geral da reunião
2. Tarefas decididas
3. Ideias ou ações consideradas

### Quando a IA não está disponível

O fallback atual gera um template com:

1. Resumo Executivo
2. Pontos Principais Discutidos
3. Ações e Responsáveis
4. Próximos Passos


## Dicas práticas

- Para reuniões longas, prefira áudio em vez de vídeo.
- Para o melhor tempo de resposta, use transcrições em `.txt` ou `.md`.
- Em ambientes com pouca RAM, use `WHISPER_MODEL=tiny`.
- Se a barra de progresso for importante em produção, mantenha `WORKERS=1`.


## Troubleshooting

### Erro 413 - arquivo muito grande

- Reduza o tamanho do arquivo.
- Ajuste `MAX_CONTENT_LENGTH` se o ambiente permitir.

### O PDF não abre em preview

- O comportamento atual da interface não usa iframe de preview.
- O download é disparado automaticamente quando a geração termina.

### O resumo saiu genérico

- Isso normalmente indica ausência de `OPENAI_API_KEY` ou falha no cliente OpenAI.
- Consulte os logs do container ou do servidor Flask.

### A transcrição ficou ruim

- Use áudio mais limpo.
- Evite ruído e sobreposição de vozes.
- Se necessário, envie uma transcrição manual em `.txt` ou `.md`.

### A barra de progresso falha em produção

- O progresso fica em memória do processo.
- Com múltiplos workers, o upload e o SSE podem cair em processos diferentes.
