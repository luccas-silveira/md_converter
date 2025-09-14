# Guia de Deploy - MDconverter

## Pré-requisitos

### Ambiente de Produção:
- Docker e Docker Compose instalados
- Chave OpenAI API (para resumos de reunião)
- Mínimo 2GB de RAM disponível
- Mínimo 1 CPU core

## Configuração

### 1. Configurar Variáveis de Ambiente

Copie e configure o arquivo de produção:
```bash
cp .env.production .env
```

**IMPORTANTE**: Edite o `.env` e configure:
- `SECRET_KEY`: Uma string aleatória segura
- `OPENAI_API_KEY`: Sua chave da API OpenAI
 - `OPENAI_MODEL` (opcional): modelo da OpenAI para resumo. Padrão: `gpt-4o-mini`
 - `WHISPER_MODEL` (opcional): modelo do Whisper. Padrão: `base` (recomendado `tiny`/`small` em VPS)

### 2. Gerar SECRET_KEY Segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Build da Aplicação

```bash
docker-compose build
```

## Deploy

### Deploy Local/Desenvolvimento:
```bash
docker-compose up -d
```

### Deploy Produção:
```bash
# Usar arquivo de ambiente específico
docker-compose --env-file .env.production up -d
```

### Verificar Status:
```bash
# Ver logs
docker-compose logs -f

# Health check (endpoint dedicado)
curl http://localhost:8080/relatorio/healthz

# Status dos containers
docker-compose ps
```

## Configurações de Produção

### Recursos (serviço padrão):
- **Memória**: 2GB (ajustável no compose)
- **CPU**: 1 core (ajustável)
- **Timeout**: 5 minutos para uploads grandes
- **Workers/Threads**: por padrão `WORKERS=1`, `THREADS=2` (ajustável via env)

### Limites:
- **Upload máximo**: 100MB
- **Formatos suportados**:
  - Reuniões: MP3, MP4, WAV, AVI, MOV, TXT, MD
  - Markdown: MD, TXT

### Health Checks:
- Endpoint: `GET /relatorio/healthz`
- Intervalo: 30 segundos
- Timeout: 10 segundos
- Retries: 3 tentativas

## URLs

- **Aplicação**: http://localhost:8080
- **Health Check**: http://localhost:8080/relatorio/healthz

## Troubleshooting

### Container não inicia:
```bash
# Ver logs detalhados
docker-compose logs md-converter

# Verificar health check
docker-compose exec md-converter python health_check.py
```

### Erro de memória:
- Aumente o limite de memória no docker-compose.yml
- Reduza o número de workers Gunicorn

### Erro de API OpenAI:
- Verifique se a chave está correta no .env
- Confirme que a chave tem créditos disponíveis

### Upload falha:
- Verifique o tamanho do arquivo (máx 100MB)
- Confirme que o formato é suportado

## Backup

### Logs:
```bash
docker-compose logs md-converter > backup-logs.txt
```

### Configurações:
Faça backup dos arquivos:
- `.env`
- `docker-compose.yml`
- `prompts/prompt_resumo.md`

## Atualizações

```bash
# Parar aplicação
docker-compose down

# Atualizar código
git pull

# Rebuild e restart
docker-compose build
docker-compose up -d
```

## IA Opcional (serviço separado)

Para usar recursos de resumo de reunião (Whisper/Torch), suba o serviço opcional com perfil `ai`:

```bash
# Sobe o serviço padrão + serviço de IA
docker compose --profile ai up -d

# O serviço de IA expõe por padrão http://localhost:8081
# Ajuste portas/recursos no docker-compose.yml conforme necessário
```

Requisitos adicionais:
- Mais memória (recomendado 4GB+ para Whisper/Torch)
- `ffmpeg` já incluso no Dockerfile.ai
- Defina `WHISPER_MODEL=tiny` ou `small` se sua VPS for limitada em CPU/RAM

## Volumes e Uploads

- O diretório de uploads na produção é configurável via `UPLOAD_FOLDER` (default: `/data/uploads`).
- O `docker-compose.yml` já cria e monta o volume `uploads:/data/uploads`.

## Reverse Proxy e SSE (progresso)

Se estiver atrás de Nginx/Caddy, desabilite buffering para SSE:

Nginx (exemplo):
```nginx
location /relatorio/ {
  proxy_pass http://127.0.0.1:8080;
  proxy_http_version 1.1;
  proxy_set_header Connection "";
  proxy_buffering off;
  proxy_read_timeout 360s;
}
```

## Monitoramento

### Métricas importantes:
- Uso de memória (máx 2GB)
- Tempo de resposta health check
- Logs de erro
- Taxa de upload bem-sucedidos

### Comandos úteis:
```bash
# Monitor em tempo real
docker stats md-converter

# Logs filtrados por erro
docker-compose logs md-converter | grep ERROR

# Reiniciar se necessário
docker-compose restart md-converter
```
