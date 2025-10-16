# Checklist de Tarefas: Correção da Vulnerabilidade de Path Traversal

## 1. Compreensão e Clarificação da Tarefa

* [x] Reafirmar compreensão da vulnerabilidade de path traversal identificada
* [x] Revisar os 3 pontos de impacto crítico:
  * [x] Possibilidade de leitura/escrita de arquivos não autorizados
  * [x] Risco de sobrescrita de arquivos críticos do sistema
  * [x] Potencial execução de código malicioso
* [x] Responder perguntas de clarificação:
  * [x] Definir política de nomenclatura de arquivos (comprimento máximo: 200 chars, remover caracteres perigosos)
  * [x] Decidir comportamento para nomes inválidos (gerar nome genérico com UUID)
  * [x] Confirmar preservação de extensões (.md para conversões, .txt para reuniões)
  * [x] Verificar retrocompatibilidade com integrações existentes (compatível)
  * [x] Confirmar necessidade de logging de segurança para tentativas suspeitas (sim, implementar)

---

## 2. Análise de Impacto e Pré-requisitos

### Áreas Afetadas
* [x] Identificar e documentar arquivos a modificar:
  * [x] `app/routes/conversion.py` (linhas 34, 85)
  * [x] `app/routes/meeting.py` (linha 56)
* [x] Mapear funções impactadas:
  * [x] `convert_md()` - endpoint de conversão MD→PDF
  * [x] `process_meeting()` - endpoint de processamento de reuniões
* [x] Listar fluxos de usuário afetados:
  * [x] Upload de arquivos Markdown
  * [x] Upload de logos customizados
  * [x] Upload de arquivos de reunião (texto, áudio, vídeo)

### Dependências
* [x] Verificar versão do Werkzeug instalado (Werkzeug já está no Flask, será verificado no container)
* [x] Confirmar que `pathlib.Path` está disponível (biblioteca padrão Python - confirmado)
* [x] Verificar que nenhuma dependência nova é necessária (confirmado)

### Pré-requisitos
* [x] Criar backup do código atual antes das modificações (branch security/fix-path-traversal criada)
* [x] Configurar ambiente de testes para validação (será feito nas próximas etapas)
* [x] Preparar casos de teste com nomes maliciosos (será implementado)

---

## 3. Implementação - Etapa 1: Criar Função Utilitária Centralizada

* [x] Criar novo arquivo `app/utils/file_security.py`
* [x] Implementar função `sanitize_filename()` com os seguintes recursos:
  * [x] Parâmetros: `filename`, `default_extension`, `max_length`
  * [x] Caso 1: Tratar filename vazio ou None
  * [x] Caso 2: Aplicar `secure_filename()` do Werkzeug
  * [x] Caso 3: Gerar nome seguro se `secure_filename()` retornar vazio
  * [x] Caso 4: Forçar extensão padrão se não houver
  * [x] Caso 5: Limitar comprimento do filename (max_length)
  * [x] Adicionar logging de segurança para nomes suspeitos (contendo `..`, `/`, `\`, `\x00`)
* [x] Adicionar docstring completa com Args, Returns e Raises
* [x] Adicionar type hints para todos os parâmetros
* [x] Importar bibliotecas necessárias:
  * [x] `logging`
  * [x] `pathlib.Path`
  * [x] `werkzeug.utils.secure_filename`
  * [x] `uuid.uuid4`

---

## 4. Implementação - Etapa 2: Modificar `app/routes/conversion.py`

* [x] Adicionar importações no topo do arquivo:
  * [x] `from werkzeug.utils import secure_filename`
  * [x] `from app.utils.file_security import sanitize_filename`
* [x] Modificar função `convert_md()` - Sanitização do arquivo principal (linha ~34):
  * [x] Substituir `filename = Path(uploaded.filename or "document.md").name`
  * [x] Implementar chamada a `sanitize_filename()` com:
    * [x] `default_extension='.md'`
    * [x] `max_length=200`
  * [x] Adicionar bloco try-except para capturar `ValueError`
  * [x] Em caso de erro, retornar 400 com mensagem apropriada
* [x] Modificar função `convert_md()` - Sanitização do logo (linha ~85):
  * [x] Substituir `logo_name = Path(logo_file.filename).name`
  * [x] Implementar chamada a `sanitize_filename()` com `max_length=100`
  * [x] Adicionar bloco try-except para tratar nomes inválidos
  * [x] Logar warning e ignorar logo se nome for inválido
* [x] Atualizar logs informativos para refletir sanitização

---

## 5. Implementação - Etapa 3: Modificar `app/routes/meeting.py`

* [x] Adicionar importações no topo do arquivo:
  * [x] `from werkzeug.utils import secure_filename`
  * [x] `from app.utils.file_security import sanitize_filename`
* [x] Modificar função `process_meeting()` - Sanitização do arquivo de reunião (linha ~56):
  * [x] Substituir `filename = Path(meeting_file.filename or "meeting").name`
  * [x] Implementar chamada a `sanitize_filename()` com:
    * [x] `default_extension='.txt'`
    * [x] `max_length=200`
  * [x] Adicionar bloco try-except para capturar `ValueError`
  * [x] Em caso de erro, retornar 400 com mensagem apropriada
* [x] Atualizar logs informativos para refletir sanitização

---

## 6. Implementação - Etapa 4: Adicionar Testes de Segurança

* [x] Criar diretório `tests/` (se não existir)
* [x] Criar arquivo `tests/test_file_security.py`
* [x] Implementar classe `TestFilenameSanitization`
* [x] Criar testes unitários:
  * [x] `test_path_traversal_attack()` - Bloquear `../../etc/passwd`
  * [x] `test_absolute_path_attack()` - Remover `/etc/passwd`
  * [x] `test_windows_path_attack()` - Bloquear `..\\..\\system32`
  * [x] `test_null_byte_injection()` - Remover `\x00` de `file.md\x00.exe`
  * [x] `test_valid_filename_preserved()` - Preservar `my_document_2024.md`
  * [x] `test_unicode_filename_handling()` - Lidar com `relatório_reunião_2024.md`
  * [x] `test_empty_filename_with_default()` - Gerar nome para string vazia
  * [x] `test_very_long_filename()` - Truncar nomes com 300+ caracteres
* [x] Adicionar imports necessários:
  * [x] `pytest`
  * [x] `from app.utils.file_security import sanitize_filename`

---

## 7. Testes e Validação

### Configuração de Ferramentas de Teste
* [x] Criar/atualizar `requirements-dev.txt` com:
  * [x] `pytest==7.4.3`
  * [x] `pytest-cov==4.1.0`
  * [x] `pytest-flask==1.3.0`
  * [x] `faker==20.1.0`
  * [x] `hypothesis==6.92.0`
* [ ] Instalar dependências de desenvolvimento (a ser feito no container):
  ```bash
  pip install -r requirements-dev.txt
  ```

### Execução de Testes
* [ ] Executar testes unitários:
  ```bash
  pytest tests/test_file_security.py -v --cov=app/utils/file_security
  ```
* [ ] Executar suite completa de testes do projeto
* [ ] Verificar cobertura de código (mínimo 90% para arquivo novo)

### Testes de Integração
* [ ] Criar script de teste manual `test_filename_security.sh`
* [ ] Testar upload com path traversal via curl
* [ ] Testar upload com caminho absoluto via curl
* [ ] Testar upload com null byte via curl
* [ ] Verificar logs para detecção de tentativas suspeitas:
  ```bash
  docker logs md-converter | grep "path traversal"
  ```

### Testes de Regressão
* [ ] Executar suite de testes existente
* [ ] Validar que funcionalidades existentes não foram quebradas
* [ ] Testar uploads normais (sem caracteres maliciosos)

### Code Review
* [ ] Solicitar code review por par
* [ ] Revisar checklist de segurança
* [ ] Validar que todas as instâncias de upload foram corrigidas

---

## 8. Documentação

### Atualizar Documentação Existente

#### README.md
* [ ] Adicionar seção "Segurança"
* [ ] Documentar sanitização automática de nomes de arquivo
* [ ] Explicar prevenção de path traversal
* [ ] Mencionar logging de tentativas suspeitas

#### DEPLOY.md
* [ ] Adicionar seção "Monitoramento de Segurança"
* [ ] Documentar comandos para verificar logs de path traversal:
  ```bash
  docker logs md-converter | grep "path traversal"
  docker logs md-converter | grep "Nome inválido"
  ```
* [ ] Adicionar recomendação para configurar alertas

#### Documentação de API
* [ ] Criar/atualizar documentação do endpoint `POST /relatorio/convert-md`
* [ ] Adicionar nota de segurança sobre sanitização automática
* [ ] Listar caracteres perigosos que são removidos (`.., /, \, null bytes`)
* [ ] Documentar comportamento para nomes inválidos

### Criar Nova Documentação

#### docs/SECURITY.md
* [ ] Criar diretório `docs/` (se não existir)
* [ ] Criar arquivo `docs/SECURITY.md`
* [ ] Escrever seção "Visão Geral"
* [ ] Escrever seção "Proteção contra Path Traversal":
  * [ ] Subsection "Problema" - Explicar o ataque
  * [ ] Subsection "Solução Implementada" - Descrever as 3 camadas de proteção
  * [ ] Subsection "Exemplos de Transformação" - Tabela com inputs/outputs
* [ ] Escrever seção "Recomendações Adicionais":
  * [ ] Rate limiting
  * [ ] Monitoramento diário de logs
  * [ ] Atualização de dependências
  * [ ] Uso de HTTPS em produção

### Comentários Inline
* [ ] Adicionar comentários explicativos em `file_security.py`
* [ ] Documentar cada caso tratado pela função `sanitize_filename()`
* [ ] Adicionar comentários ANTES/DEPOIS nos arquivos modificados

---

## 9. Deploy e Monitoramento

### Pré-Deploy
* [ ] Criar branch `security/fix-path-traversal`
* [ ] Fazer commit das alterações com mensagem descritiva
* [ ] Push do branch para repositório remoto

### Deploy em Staging
* [ ] Merge da branch para ambiente de staging
* [ ] Build da imagem Docker:
  ```bash
  docker compose build
  ```
* [ ] Deploy em staging:
  ```bash
  docker compose up -d
  ```
* [ ] Executar testes de fumaça (smoke tests):
  * [ ] Upload normal deve funcionar
  * [ ] Upload com nome malicioso deve ser sanitizado
  * [ ] Verificar logs de segurança

### Deploy em Produção
* [ ] Merge para branch `main` após aprovação
* [ ] Tag da versão (ex: `v1.2.1-security-fix`)
* [ ] Build e push da imagem Docker para produção
* [ ] Deploy em produção
* [ ] Executar testes de fumaça em produção

### Monitoramento Pós-Deploy (24h ativo, depois 1 semana)

#### Métricas de Segurança
* [ ] Monitorar tentativas de path traversal:
  ```bash
  docker logs md-converter --since 24h | grep -i "path traversal" | wc -l
  ```
* [ ] Identificar IPs suspeitos:
  ```bash
  docker logs md-converter | grep "path traversal" | awk '{print $NF}' | sort | uniq -c | sort -rn
  ```
* [ ] Verificar logs diariamente durante primeira semana

#### Métricas de Funcionalidade
* [ ] Monitorar taxa de erros 400 (nome inválido):
  ```bash
  docker logs md-converter --since 1h | grep "400" | wc -l
  ```
* [ ] Verificar uploads bem-sucedidos:
  ```bash
  docker logs md-converter --since 1h | grep "PDF criado com sucesso" | wc -l
  ```
* [ ] Validar que não há aumento anormal de erros

#### Dashboards e Alertas (Opcional - Grafana/Prometheus)
* [ ] Configurar alerta `HighPathTraversalAttempts`:
  * [ ] Condição: `rate(path_traversal_attempts[5m]) > 10`
  * [ ] Severidade: Alta
  * [ ] Ação: Notificar equipe de segurança
* [ ] Configurar alerta `MultipleInvalidFilenames`:
  * [ ] Condição: `count(invalid_filename_errors[1h]) > 50`
  * [ ] Severidade: Média
  * [ ] Ação: Notificar equipe de desenvolvimento

---

## 10. Rollback e Contingência

### Preparação para Rollback
* [ ] Documentar hash do commit atual antes do deploy
* [ ] Criar tag Docker da versão anterior (`md-converter:previous`)
* [ ] Verificar que backup do código está disponível

### Plano de Rollback - Cenário 1: Quebra de Funcionalidade
* [ ] Identificar commit problemático
* [ ] Executar rollback via git:
  ```bash
  git revert <commit-hash>
  ```
* [ ] Rebuild e redeploy:
  ```bash
  docker compose down
  docker compose up -d --build
  ```
* [ ] Tempo estimado: 2-3 minutos

### Plano de Rollback - Cenário 2: Problema Crítico em Produção
* [ ] Executar rollback instantâneo via Docker:
  ```bash
  docker tag md-converter:previous md-converter:latest
  docker compose restart
  ```
* [ ] Tempo estimado: 30 segundos
* [ ] Investigar causa raiz em ambiente de desenvolvimento

### Validação Pós-Rollback
* [ ] Verificar que sistema voltou ao estado funcional
* [ ] Executar testes de fumaça
* [ ] Comunicar equipe sobre o rollback
* [ ] Planejar correção alternativa

---

## 11. Finalização

* [ ] Comunicar mudança ao time via canal apropriado (Slack, email, etc.)
* [ ] Atualizar issue/ticket de segurança com resolução
* [ ] Adicionar entry no CHANGELOG.md (se existir)
* [ ] Marcar issue como resolvida/fechada
* [ ] Agendar revisão de segurança em 30 dias
* [ ] Documentar lições aprendidas (se aplicável)

---

## Resumo de Estimativa de Tempo

| Fase                       | Tempo Estimado |
|----------------------------|----------------|
| Desenvolvimento            | 2-3 horas      |
| Testes                     | 1-2 horas      |
| Code Review                | 30 min         |
| Documentação               | 1 hora         |
| Deploy + Monitoramento     | 1 hora         |
| **TOTAL**                  | **5-7 horas**  |

---

## Prioridade

**🔴 CRÍTICA** - Implementar imediatamente

**Justificativa:**
* Vulnerabilidade de segurança confirmada (CWE-22: Path Traversal)
* Potencial de comprometimento total do sistema
* Correção simples e de baixo risco
* Sem impacto em funcionalidade existente
* Requerido para compliance de segurança
