# Guia de Uso - MDconverter

## Limites e Restrições

### Tamanho de Arquivo
- **Tamanho máximo**: 100MB por arquivo
- **Formatos recomendados para reuniões grandes**:
  - Áudio MP3 (menor que vídeo)
  - Transcrições em texto (.txt, .md)
  - Vídeos comprimidos

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
- Reduza o tamanho do arquivo
- Use formato de áudio ao invés de vídeo
- Comprima o arquivo antes do upload

### Transcrição de Baixa Qualidade
- Verifique a qualidade do áudio
- Use arquivos com menos ruído de fundo
- Considere fazer uma transcrição manual em .txt

### Processamento Lento
- Arquivos maiores demoram mais
- Transcrições de áudio são mais rápidas que de vídeo
- Arquivos de texto são processados instantaneamente

## Formatos de Saída

### PDF Gerado Contém:
- Capa personalizada (se configurada)
- Resumo estruturado da reunião
- Transcrição original (primeiros 1500 caracteres)
- Metadados (data, participantes)

### Estrutura do Resumo:
1. **Resumo Executivo**
2. **Pontos Principais Discutidos**
3. **Decisões Tomadas**
4. **Ações e Responsáveis**
5. **Próximos Passos**