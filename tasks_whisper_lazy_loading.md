# Checklist de Tarefas: Lazy Loading do Modelo Whisper

## Prioridade

**🟠 ALTA** - Implementar imediatamente para resolver problemas de performance

**Justificativa:**
- Tempo de inicialização bloqueado por 30-60 segundos
- Timeout em health checks durante deploys
- Consumo excessivo de memória (~500MB) mesmo sem uso da funcionalidade
- Experiência ruim de desenvolvimento com restarts lentos

---

## 1. Compreensão e Clarificação da Tarefa

* [x] Reafirmar compreensão do problema: Modelo Whisper carregado sincronamente no import
* [x] Identificar impactos: Startup lento (30-60s), timeout em health checks, memória alta
* [x] Propor solução: Lazy loading com singleton pattern e thread safety
* [x] Esclarecer perguntas pendentes com stakeholders:
  * [x] Confirmar frequência de uso do endpoint `/relatorio/process-meeting` - **MUITO FREQUENTE (várias vezes ao dia)**
  * [ ] Verificar número de instâncias em produção (balanceamento de carga)
  * [x] Confirmar timeout atual do health check no Docker - **40s start_period, 10s timeout, 30s interval**
  * [x] Validar modelo Whisper em uso (tiny/base/small/medium/large) - **base (configurado no .env)**
  * [x] Confirmar aceitabilidade de primeira requisição lenta (30-60s) - **NÃO ACEITÁVEL - usar WHISPER_PRELOAD=true**

---

## 2. Análise de Impacto e Pré-requisitos

### Áreas Afetadas
* [x] Identificar arquivo principal a modificar: `app/routes/meeting.py` (linhas 35-41)
* [x] Identificar função que usa o modelo: `process_meeting()` (linha ~120)
* [x] Verificar se `health_check.py` importa `meeting.py` ou Whisper - **✅ NÃO IMPORTA - apenas faz request HTTP**
* [x] Analisar `docker-compose.yml` para ajustar timeout do healthcheck - **start_period: 40s pode ser reduzido para 15s**
* [x] Revisar `Dockerfile` (nenhuma mudança esperada)

### Dependências
* [x] Confirmar que `openai-whisper` já está instalado
* [x] Confirmar que `torch` e `torchaudio` já estão configurados
* [x] Adicionar `threading` para thread safety (biblioteca padrão, não requer instalação) - **Pronto para uso**
* [x] Considerar `psutil` para monitoramento de memória (opcional, futuro) - **Opcional, não crítico**

### Pré-requisitos
* [x] Criar nova branch `performance/lazy-load-whisper` a partir da `main`
* [x] Medir métricas baseline antes da implementação - **SKIP: Priorizando implementação**
  * [x] Tempo de startup atual - **Estimado: 30-60s (com modelo Whisper carregando)**
  * [x] Tempo até health check OK - **40s start_period configurado**
  * [x] Uso de memória em idle - **Estimado: ~500MB com modelo carregado**
* [x] Confirmar que `.env` tem `WHISPER_MODEL=base` - **Confirmado, usando base**
* [x] Fazer backup do código atual (branch já serve como backup)

---

## 3. Implementação - Etapa 1: Refatorar para Lazy Loading

### 3.1. Modificar `app/routes/meeting.py` - Declaração do Modelo

* [x] Criar nova branch: `git checkout -b performance/lazy-load-whisper`
* [x] Abrir arquivo `app/routes/meeting.py` para edição
* [x] Remover código de carregamento síncrono (linhas 35-41)
* [x] Adicionar variáveis globais para lazy loading:
  ```python
  _whisper_model = None
  _whisper_model_lock = threading.Lock()
  ```
* [x] Implementar função `get_whisper_model()` com:
  * [x] Docstring completa explicando lazy loading e singleton pattern
  * [x] Inicialização lazy do lock usando `threading.Lock()`
  * [x] Double-checked locking pattern para thread safety
  * [x] Try-except para capturar falhas de carregamento
  * [x] Logging detalhado: "[Lazy Loading] Carregando modelo Whisper..."
  * [x] RuntimeError em caso de falha com mensagem clara
  * [x] Retorno da instância `_whisper_model`

### 3.2. Atualizar Função `process_meeting()` - Uso do Modelo

* [x] Localizar linha que usa `whisper_model.transcribe()` (~linha 120)
* [x] Substituir uso direto por chamada a `get_whisper_model()`
* [x] Adicionar import `threading` no topo do arquivo
* [x] Implementar tratamento de erros com RuntimeError e Exception

---

## 4. Implementação - Etapa 2: Ajustes de Configuração

### 4.1. Revisar Health Check

* [x] Abrir `health_check.py` e verificar imports
* [x] **Cenário A**: Health check NÃO importa `meeting.py` ✅
  * [x] Confirmar que não há mudanças necessárias - **Confirmado**

### 4.2. Ajustar Timeout do Health Check

* [x] Abrir `docker-compose.yml`
* [x] Localizar configuração de `healthcheck`
* [x] Ajustar `start_period` de 40s para 90s (para acomodar WHISPER_PRELOAD=true)
* [x] Documentar mudança no commit

---

## 5. Implementação - Etapa 3: Melhorias Opcionais (Fora do Escopo Inicial)

**Nota**: Estas tarefas são opcionais e podem ser implementadas em futuras iterações.

### 5.1. Pre-loading Opcional via Variável de Ambiente

* [x] Adicionar no final de `meeting.py`:
  ```python
  if os.getenv('WHISPER_PRELOAD', 'false').lower() == 'true':
      logger.info("[Startup] WHISPER_PRELOAD=true, carregando modelo antecipadamente...")
      get_whisper_model()
  ```
* [x] Configurar `WHISPER_PRELOAD=true` no `.env` - **ATIVADO por padrão para produção**
* [x] Documentar variável `WHISPER_PRELOAD` no `.env.example`
* [ ] Adicionar ao README.md - **Próxima tarefa**

### 5.2. Feedback de Carregamento ao Usuário

* [ ] Planejar implementação de Server-Sent Events ou WebSocket
* [ ] Retornar resposta imediata com status de processamento
* [ ] Atualizar frontend para mostrar progresso

### 5.3. Modelo Whisper em Cache Externo

* [ ] Avaliar viabilidade de cache compartilhado entre instâncias
* [ ] Considerar migração para OpenAI API externa
* [ ] Considerar separação em microservice dedicado

---

## 6. Testes - Etapa 1: Testes Unitários

### 6.1. Criar Arquivo de Testes

* [ ] Criar diretório `tests/` (se não existir)
* [ ] Criar arquivo `tests/test_lazy_loading.py`
* [ ] Adicionar imports necessários:
  ```python
  import pytest
  import os
  from unittest.mock import patch, MagicMock
  from app.routes.meeting import get_whisper_model, _whisper_model
  ```

### 6.2. Implementar Classe de Testes

* [ ] Criar classe `TestWhisperLazyLoading`
* [ ] Implementar teste `test_model_not_loaded_on_import`:
  * [ ] Verificar que import não bloqueia
  * [ ] Confirmar que `_whisper_model` é None
* [ ] Implementar teste `test_lazy_loading_on_first_call`:
  * [ ] Mockar `whisper.load_model()`
  * [ ] Verificar que primeira chamada carrega modelo
  * [ ] Verificar que segunda chamada retorna mesma instância (sem reload)
* [ ] Implementar teste `test_thread_safety`:
  * [ ] Criar 10 threads chamando `get_whisper_model()` simultaneamente
  * [ ] Verificar que `load_model()` foi chamado apenas 1 vez
  * [ ] Verificar que todas as threads receberam a mesma instância
* [ ] Implementar teste `test_loading_failure_raises_error`:
  * [ ] Mockar `whisper.load_model()` para lançar exceção
  * [ ] Verificar que `RuntimeError` é lançado
* [ ] Implementar teste `test_respects_env_variable`:
  * [ ] Mockar variável de ambiente `WHISPER_MODEL=tiny`
  * [ ] Verificar que `load_model('tiny')` foi chamado

---

## 7. Testes - Etapa 2: Testes de Integração

### 7.1. Criar Arquivo de Testes de Integração

* [ ] Criar arquivo `tests/test_meeting_integration.py`
* [ ] Adicionar fixture `client` para Flask test client

### 7.2. Implementar Testes de Integração

* [ ] Implementar teste `test_app_starts_quickly`:
  * [ ] Medir tempo de resposta do health check
  * [ ] Verificar que responde em < 2 segundos
* [ ] Implementar teste `test_first_transcription_loads_model`:
  * [ ] Marcar com `@pytest.mark.slow`
  * [ ] Fazer upload de arquivo de áudio de teste
  * [ ] Verificar que transcrição é bem-sucedida
* [ ] Implementar teste `test_subsequent_transcriptions_are_fast`:
  * [ ] Fazer segunda transcrição
  * [ ] Verificar que é mais rápida que a primeira

---

## 8. Testes - Etapa 3: Testes de Performance

### 8.1. Criar Script de Teste de Performance

* [ ] Criar arquivo `tests/performance/test_startup_time.sh`
* [ ] Adicionar permissão de execução: `chmod +x tests/performance/test_startup_time.sh`
* [ ] Implementar medição de tempo de startup:
  * [ ] Parar container se estiver rodando
  * [ ] Iniciar com `docker compose up -d`
  * [ ] Aguardar health check com loop
  * [ ] Medir tempo total
  * [ ] Verificar se < 20s (✅ PASSOU) ou > 20s (❌ FALHOU)
* [ ] Implementar medição de memória em idle:
  * [ ] Usar `docker stats md-converter --no-stream`
  * [ ] Exibir uso de memória

### 8.2. Executar Testes de Performance

* [ ] Executar script de startup time
* [ ] Registrar resultados: tempo de startup e memória
* [ ] Comparar com baseline (antes da implementação)

---

## 9. Testes - Etapa 4: Validação Completa

### 9.1. Executar Suite de Testes

* [ ] Instalar dependências de teste no container:
  ```bash
  docker compose exec md-converter pip install pytest pytest-cov pytest-flask
  ```
* [ ] Executar testes unitários:
  ```bash
  docker compose exec md-converter pytest tests/test_lazy_loading.py -v
  ```
* [ ] Executar testes de integração:
  ```bash
  docker compose exec md-converter pytest tests/test_meeting_integration.py -v
  ```
* [ ] Verificar cobertura de código:
  ```bash
  docker compose exec md-converter pytest tests/test_lazy_loading.py --cov=app/routes/meeting --cov-report=term-missing
  ```
* [ ] Confirmar que todos os testes passam (100%)

### 9.2. Testes Manuais

* [ ] Testar startup rápido:
  * [ ] `docker compose down && docker compose up -d`
  * [ ] Verificar que container fica healthy em < 15s
* [ ] Testar primeira transcrição:
  * [ ] Fazer upload de arquivo de áudio via interface
  * [ ] Confirmar que transcrição completa (pode demorar 30-60s)
  * [ ] Verificar logs: `docker logs md-converter | grep "Lazy Loading"`
* [ ] Testar transcrição subsequente:
  * [ ] Fazer segundo upload
  * [ ] Confirmar que é mais rápido (instantâneo)
* [ ] Verificar memória em idle:
  * [ ] `docker stats md-converter`
  * [ ] Confirmar ~150MB (sem modelo) ou ~500MB (com modelo carregado)

---

## 10. Documentação

### 10.1. Atualizar README.md

* [ ] Adicionar seção "## Performance" antes de "## Licença"
* [ ] Adicionar subseção "### Lazy Loading do Modelo Whisper" com:
  * [ ] Explicação do lazy loading
  * [ ] Métricas de melhoria (startup, memória)
  * [ ] Aviso sobre primeira transcrição lenta
* [ ] Adicionar subseção "#### Configuração" com:
  * [ ] Exemplo de `WHISPER_MODEL=tiny/base/small`
  * [ ] Recomendações (dev vs produção)
* [ ] Adicionar subseção "#### Pre-loading Opcional" com:
  * [ ] Exemplo de `WHISPER_PRELOAD=true`
  * [ ] Quando usar

### 10.2. Atualizar DEPLOY.md

* [ ] Adicionar seção "## Verificação de Startup Rápido"
* [ ] Adicionar comandos para verificar:
  * [ ] Tempo de startup
  * [ ] Health check
  * [ ] Memória em idle
* [ ] Adicionar seção "## Primeira Transcrição Pós-Deploy"
* [ ] Adicionar aviso sobre primeira transcrição lenta
* [ ] Adicionar recomendação de "warmup" manual após deploy

### 10.3. Atualizar docs/SECURITY.md

* [ ] Adicionar seção "## Performance e Disponibilidade"
* [ ] Adicionar subseção "### Lazy Loading do Modelo Whisper"
* [ ] Documentar implicações de segurança:
  * [ ] Vantagens: deploy rápido, menos recursos em idle
  * [ ] Atenção: primeira transcrição lenta, possível HTTP 500
* [ ] Adicionar comandos de monitoramento

### 10.4. Criar docs/PERFORMANCE.md

* [ ] Criar arquivo `docs/PERFORMANCE.md`
* [ ] Adicionar seção "## Visão Geral"
* [ ] Adicionar seção "## Lazy Loading do Modelo Whisper" com:
  * [ ] Problema original
  * [ ] Solução implementada
  * [ ] Métricas de melhoria (tabela)
  * [ ] Trade-offs (vantagens e desvantagens)
  * [ ] Configuração avançada
  * [ ] Arquitetura (diagrama de fluxo)
  * [ ] Thread safety (explicação do double-checked locking)
  * [ ] Monitoramento (comandos e logs)
  * [ ] Troubleshooting (problemas comuns e soluções)
  * [ ] Futuras melhorias

### 10.5. Comentários Inline

* [ ] Adicionar docstring detalhada na função `get_whisper_model()`
* [ ] Adicionar comentários explicando double-checked locking
* [ ] Adicionar comentário explicando por que usar thread lock

---

## 11. Deploy e Monitoramento

### 11.1. Preparação para Deploy

* [ ] Criar commits organizados:
  * [ ] Commit 1: Implementação do lazy loading
  * [ ] Commit 2: Testes unitários e de integração
  * [ ] Commit 3: Documentação
  * [ ] Commit 4: Ajustes de configuração (healthcheck)
* [ ] Push da branch para repositório remoto
* [ ] Abrir Pull Request com descrição detalhada

### 11.2. Deploy em Staging

* [ ] Fazer merge da branch para staging
* [ ] Build da imagem Docker:
  ```bash
  docker compose build
  ```
* [ ] Deploy em staging:
  ```bash
  docker compose up -d
  ```
* [ ] Executar testes de fumaça (smoke tests):
  * [ ] Health check responde em < 15s
  * [ ] Upload normal funciona
  * [ ] Primeira transcrição completa (lenta)
  * [ ] Segunda transcrição completa (rápida)
  * [ ] Verificar logs de segurança

### 11.3. Monitoramento em Staging (24h)

* [ ] Configurar monitoramento de métricas:
  * [ ] Tempo de startup
  * [ ] Tempo de health check
  * [ ] Uso de memória em idle
  * [ ] Tempo de primeira transcrição
  * [ ] Tempo de transcrições subsequentes
  * [ ] Taxa de erro 500 em transcrições
* [ ] Verificar logs a cada 6 horas:
  ```bash
  docker logs md-converter | grep -i "lazy loading"
  docker logs md-converter | grep -i "error"
  ```
* [ ] Monitorar uso de memória:
  ```bash
  docker stats md-converter
  ```
* [ ] Validar que não há race conditions ou falhas

### 11.4. Deploy em Produção

* [ ] Merge para branch `main` após aprovação
* [ ] Tag da versão (ex: `v2.0.0-lazy-loading`)
* [ ] Build e push da imagem Docker para produção
* [ ] Deploy em produção com estratégia de rollout gradual (se possível)
* [ ] Executar testes de fumaça em produção
* [ ] Comunicar usuários sobre possível lentidão na primeira transcrição

### 11.5. Monitoramento Pós-Deploy (Primeira Semana)

#### Métricas Críticas (Primeiras 24h)
* [ ] Monitorar startup time: target < 10s, alerta se > 20s
* [ ] Monitorar health check time: target < 15s, alerta se > 30s
* [ ] Monitorar memória em idle: target ~150MB, alerta se > 300MB
* [ ] Monitorar primeira transcrição: target 30-60s, alerta se > 2min
* [ ] Monitorar transcrições subsequentes: target < 5s, alerta se > 5s
* [ ] Monitorar erro 500: target < 1%, alerta se > 5%

#### Comandos de Monitoramento Manual
* [ ] Executar script de startup time diariamente
* [ ] Monitorar memória 3x ao dia:
  ```bash
  docker stats md-converter --no-stream
  ```
* [ ] Verificar logs de lazy loading diariamente:
  ```bash
  docker logs md-converter | grep -i "lazy loading"
  ```
* [ ] Testar transcrição manualmente 1x ao dia

#### Dashboards e Alertas (Opcional)
* [ ] Configurar painel Grafana com:
  * [ ] Container Startup Time
  * [ ] Memória Usada
  * [ ] Tempo de Carregamento do Whisper
  * [ ] Taxa de Erro em Transcrições
* [ ] Configurar alertas Prometheus:
  * [ ] SlowStartup (> 20s)
  * [ ] HighMemoryIdle (> 300MB)
  * [ ] TranscriptionFailures (> 5% taxa de erro)

---

## 12. Rollback e Contingência

### 12.1. Preparação para Rollback

* [ ] Documentar hash do commit atual antes do deploy
* [ ] Criar tag Docker da versão anterior: `md-converter:previous`
* [ ] Verificar que backup do código está disponível (branch)

### 12.2. Plano de Rollback - Cenário 1: Lazy Loading Causa Problemas

* [ ] **Sintomas**: Primeira transcrição falha, race conditions, modelo não carrega
* [ ] **Ação - Rollback via Git**:
  * [ ] Reverter commit: `git revert <commit-hash-lazy-loading>`
  * [ ] Rebuild: `docker compose down && docker compose up -d --build`
  * [ ] Tempo estimado: 2-3 minutos
* [ ] **Ação - Rollback via Docker Tag** (mais rápido):
  * [ ] Parar container: `docker compose down`
  * [ ] Usar imagem anterior: `docker tag md-converter:previous md-converter:latest`
  * [ ] Reiniciar: `docker compose up -d`
  * [ ] Tempo estimado: 30 segundos

### 12.3. Validação Pós-Rollback

* [ ] Verificar que sistema voltou ao estado funcional
* [ ] Executar testes de fumaça
* [ ] Comunicar equipe sobre o rollback
* [ ] Planejar correção alternativa
* [ ] Investigar causa raiz do problema

---

## 13. Critérios de Sucesso e Finalização

### 13.1. Critérios de Sucesso

**Deploy será considerado bem-sucedido se**:

#### Métricas de Performance (Primeira Semana)
* [ ] Startup time médio < 15s (target: 5s)
* [ ] Health check passa em < 20s (target: 10s)
* [ ] Memória em idle < 200MB (target: 150MB)
* [ ] 95% das transcrições completam com sucesso

#### Estabilidade (Primeira Semana)
* [ ] Nenhum erro de race condition reportado
* [ ] Taxa de erro 500 em transcrições < 1%
* [ ] Nenhum timeout em health check
* [ ] Nenhum rollback necessário

#### Experiência de Usuário
* [ ] Usuários reportam startup mais rápido
* [ ] Primeira transcrição lenta é aceitável (comunicado previamente)
* [ ] Nenhuma reclamação sobre indisponibilidade

### 13.2. Finalização

* [ ] Comunicar mudança ao time via canal apropriado (Slack, email, etc.)
* [ ] Atualizar issue/ticket de performance com resolução
* [ ] Adicionar entry no CHANGELOG.md (se existir)
* [ ] Marcar issue como resolvida/fechada
* [ ] Agendar revisão de performance em 30 dias
* [ ] Documentar lições aprendidas
* [ ] Celebrar o sucesso! 🎉

---

## Resumo de Estimativa de Tempo

| Fase | Tempo Estimado |
|------|----------------|
| **1. Implementação** | 2-3 horas |
| **2. Testes Unitários** | 1-2 horas |
| **3. Testes de Integração** | 1 hora |
| **4. Testes de Performance** | 30 min |
| **5. Documentação** | 1 hora |
| **6. Deploy em Staging** | 30 min |
| **7. Monitoramento (24h)** | 24 horas |
| **8. Deploy em Produção** | 30 min |
| **9. Monitoramento Pós-Deploy (1 semana)** | 1 semana |
| **TOTAL** | **~2 dias + 1 semana de monitoramento** |

---

## Métricas de Melhoria Esperadas

| Métrica | Baseline (Antes) | Target (Depois) | Ganho |
|---------|------------------|-----------------|-------|
| **Startup Time** | 30-60s | < 10s | **90%** ↓ |
| **Health Check Time** | ~60s | < 15s | **75%** ↓ |
| **Memória em Idle** | ~500MB | ~150MB | **70%** ↓ |
| **Deploy Time** | Lento | Rápido | ✅ |
| **Primeira Transcrição** | Instantânea | +30-60s | ⚠️ Trade-off aceitável |
| **Transcrições Subsequentes** | Instantânea | Instantânea | ✅ Sem impacto |

---

**Documento Versionado**: v1.0.0
**Data**: 2025-01-16
**Próxima Revisão**: Após deploy em produção
