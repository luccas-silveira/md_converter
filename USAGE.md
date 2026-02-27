# Guia de Uso - MDconverter

## Limites e Restrições

### Tamanho de Arquivo
- **Tamanho máximo geral**: 100MB por arquivo
- **Limite Whisper Cloud API**: 25MB para arquivos de áudio/vídeo
- **Formatos recomendados para reuniões grandes**:
  - Áudio MP3 (menor que vídeo)
  - Transcrições em texto (.txt, .md) - sem limite de 25MB
  - Vídeos comprimidos (atenção ao limite de 25MB para transcrição)

### Formatos Suportados

#### Para Reuniões:
- **Áudio**: MP3, WAV, M4A
- **Vídeo**: MP4, AVI, MOV
- **Texto**: TXT, MD

#### Para Conversão MD:
- Arquivos Markdown (.md)
- Texto simples tratado como Markdown

## Dicas de Performance

### Para Arquivos Grandes:
1. **Prefira áudio a vídeo** - Arquivos menores, mesmo resultado
2. **Use transcrições prontas** - Processamento muito mais rápido
3. **Comprima vídeos antes** - Use ferramentas como Handbrake

### Para Melhor Qualidade:
1. **Áudio limpo** - Menos ruído = transcrição melhor
2. **Fale claramente** - Whisper funciona melhor com fala clara
3. **Evite sobreposição** - Uma pessoa falando por vez

## Troubleshooting

### Erro 413 - Arquivo Muito Grande
- Reduza o tamanho do arquivo para menos de 100MB
- Use formato de áudio ao invés de vídeo
- Comprima o arquivo antes do upload

### Erro "Arquivo muito grande" (Whisper)
- **Causa**: Arquivo de áudio/vídeo maior que 25MB (limite da API Whisper)
- **Solução 1**: Comprima o áudio para menos de 25MB
- **Solução 2**: Use uma transcrição manual em .txt (sem limite)
- **Solução 3**: Divida o áudio em partes menores

### Transcrição de Baixa Qualidade
- Verifique a qualidade do áudio
- Use arquivos com menos ruído de fundo
- Considere fazer uma transcrição manual em .txt
- Whisper Cloud API já usa modelo otimizado

### Processamento Lento
- Whisper Cloud API processa remotamente (depende da conexão)
- Arquivos de texto são processados instantaneamente
- Resumos GPT-4o são mais lentos que GPT-4o-mini (mas mais precisos)

## Formatos de Saída

### PDF Gerado Contém:
- Capa personalizada (se configurada)
- Resumo estruturado da reunião
- Transcrição original (primeiros 1500 caracteres)
- Metadados (data, participantes)

### Estrutura do Resumo (Gerado por GPT-4o):
1. **Resumo Geral da Reunião** - Tópicos agrupados por contexto (automático)
2. **Tarefas Decididas** - Tabelas agrupadas por responsável
3. **Ideias / Ações Consideradas** - Itens discutidos mas sem compromisso

**Nota**: O resumo é gerado pela IA sem metaprompts ou headers duplicados. A capa do PDF já contém título, data e participantes.