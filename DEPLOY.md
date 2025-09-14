# Deploy Único (Completo, com IA)

## Pré‑requisitos
- Docker e Docker Compose v2 (plugin). Verifique com: `docker compose version`
- Chave OpenAI (`OPENAI_API_KEY`)
- VPS com 4GB+ RAM recomendado (para Whisper/Torch)

## Configuração
1) Criar `.env` a partir do exemplo:
```bash
cp .env.example .env
```
Edite no `.env`:
- `SECRET_KEY`: string aleatória segura (gere com `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `OPENAI_API_KEY`: sua chave
- Opcional: `WHISPER_MODEL=tiny|small|base` (use `tiny` em VPS modesta)

2) Build e subir (porta 8080):
```bash
docker compose up -d --build
```

3) Verificar e logs:
```bash
curl http://localhost:8080/relatorio/healthz
docker compose logs -f md-converter
```

4) Acessar a aplicação:
- http://SEU_IP:8080/relatorio/

## Produção
- `WORKERS=1`, `THREADS=2` (default): bom começo para 4GB RAM
- `TIMEOUT=600` recomendado para uploads grandes
- `UPLOAD_FOLDER=/data/uploads` (volume persistente já montado no compose)
- Healthcheck: `GET /relatorio/healthz`

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

## Firewall (Ubuntu)
```bash
sudo ufw allow 8080/tcp
```

## Problemas comuns
- Torch/Whisper pesados: use `WHISPER_MODEL=tiny` no `.env`.
- Falha no healthcheck: confira `docker compose logs -f` e `curl http://localhost:8080/relatorio/healthz`.

