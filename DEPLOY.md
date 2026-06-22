# Deploy Único (Completo, com IA)

## Pré-requisitos

- Docker e Docker Compose v2
- `OPENAI_API_KEY` se o fluxo de reunião precisar de resumo com IA
- VPS com 4GB+ de RAM para `WHISPER_MODEL=base`
- Porta `8080/tcp` liberada no host


## Configuração

1. Crie ou edite o arquivo `.env` na raiz do projeto.

Exemplo mínimo:

```bash
cat > .env <<'EOF'
SECRET_KEY=gere-uma-chave-segura-aqui
OPENAI_API_KEY=sua-chave-openai
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=base
EOF
```

2. Suba a stack:

```bash
docker compose up -d --build
```

3. Verifique saúde e logs:

```bash
curl http://localhost:8080/relatorio/healthz
docker compose logs -f md-converter
```

4. Acesse:

- [http://SEU_IP:8080/relatorio/](http://SEU_IP:8080/relatorio/)


## Variáveis relevantes

- `SECRET_KEY`: obrigatório em produção
- `OPENAI_API_KEY`: habilita o resumo com IA; sem ela, o modo de reunião gera um template padrão
- `OPENAI_MODEL`: modelo usado no resumo; default atual `gpt-4o-mini`
- `WHISPER_MODEL`: default `base`; use `tiny` em hosts menores
- `MAX_CONTENT_LENGTH`: limite de upload em bytes; o compose atual define `1073741824` (1GB)
- `UPLOAD_FOLDER`: diretório persistente para temporários; o compose usa `/data/uploads`
- `WORKERS`, `THREADS`, `TIMEOUT`: parâmetros do Gunicorn lidos no `CMD` da imagem


## Padrões atuais da imagem

O `Dockerfile` já sobe o Gunicorn com estes defaults:

- `WORKERS=1`
- `THREADS=2`
- `TIMEOUT=300`
- `PRELOAD=1`
- `ACCESS_LOG=-`
- `ERROR_LOG=-`

Notas operacionais:

- mantenha `WORKERS=1` se a barra de progresso via SSE for importante, porque o estado é mantido em memória por processo
- aumente `TIMEOUT` para uploads ou transcrições longas
- se a VPS for limitada, prefira `WHISPER_MODEL=tiny`


## Operação

Atualizar código e reiniciar:

```bash
git pull
docker compose up -d --build
```

Logs e monitoramento:

```bash
docker compose logs -f md-converter
docker stats md-converter
```


## Reverse Proxy

Se houver Nginx ou outro proxy na frente:

- preserve o prefixo `/relatorio`
- encaminhe `GET /relatorio/healthz` para o backend para health checks externos
- use `proxy_read_timeout` compatível com o `TIMEOUT` do Gunicorn em uploads/transcrições longas


## Firewall (Ubuntu)

```bash
sudo ufw allow 8080/tcp
```


## Problemas comuns

- `ModuleNotFoundError` ou falha de build:
  Refaça a imagem com `docker compose build --no-cache`.

- Healthcheck falha:
  Confira `docker compose logs -f md-converter` e `curl http://localhost:8080/relatorio/healthz`.

- Processamento de reunião muito lento:
  Reduza `WHISPER_MODEL`, aumente `TIMEOUT` e confirme recursos do host.

- Resumo sai sem IA:
  Verifique se `OPENAI_API_KEY` está presente no `.env` carregado pelo compose.
