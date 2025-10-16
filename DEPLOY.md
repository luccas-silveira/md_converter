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

## Monitoramento de Segurança

### Verificar Tentativas de Path Traversal

Monitore regularmente os logs para detectar tentativas de ataque:

```bash
# Ver todas as tentativas de path traversal
docker logs md-converter | grep "path traversal"

# Contar tentativas nas últimas 24 horas
docker logs md-converter --since 24h | grep -i "path traversal" | wc -l

# Identificar IPs suspeitos
docker logs md-converter | grep "path traversal" | awk '{print $NF}' | sort | uniq -c | sort -rn

# Verificar filenames inválidos
docker logs md-converter | grep "Nome inválido"
```

### Alertas Recomendados

Configure alertas para:
- **Alta prioridade**: Mais de 10 tentativas de path traversal em 5 minutos do mesmo IP
- **Média prioridade**: Mais de 50 filenames inválidos em 1 hora

### Métricas de Segurança

```bash
# Taxa de uploads bem-sucedidos
docker logs md-converter --since 1h | grep "PDF criado com sucesso" | wc -l

# Taxa de erros 400 (filename inválido)
docker logs md-converter --since 1h | grep "400" | wc -l
```

**Ação Recomendada**: Revise logs de segurança **diariamente** durante a primeira semana após deploy.

## Problemas comuns
- Torch/Whisper pesados: use `WHISPER_MODEL=tiny` no `.env`.
- Falha no healthcheck: confira `docker compose logs -f` e `curl http://localhost:8080/relatorio/healthz`.
- Múltiplas tentativas de path traversal: Verifique se há ataque coordenado e considere implementar rate limiting.

