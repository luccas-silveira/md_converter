# Guia de Segurança - MD Converter

## Visão Geral

Este documento descreve as medidas de segurança implementadas no MD Converter para proteger contra vulnerabilidades comuns em aplicações web que processam uploads de arquivos.

**Última Atualização**: Implementação da proteção contra Path Traversal (CWE-22)
**Responsável**: Equipe de Desenvolvimento

---

## Proteção contra Path Traversal (CWE-22)

### Problema

**Path Traversal** (também conhecido como Directory Traversal) é uma vulnerabilidade de segurança que permite que atacantes acessem arquivos e diretórios fora do diretório pretendido pela aplicação.

**Como funciona o ataque:**

Atacantes podem inserir sequências especiais nos nomes de arquivo para navegar na estrutura de diretórios do servidor:

```
../../etc/passwd           # Unix: tentar ler arquivo de senhas
../../../windows/system.ini  # Windows: tentar acessar arquivo de sistema
file.md\x00.exe            # Null byte injection: bypassar validação de extensão
```

**Impacto potencial:**
- ✗ Leitura de arquivos sensíveis do sistema
- ✗ Sobrescrita de arquivos de configuração
- ✗ Execução de código malicioso
- ✗ Comprometimento completo do servidor

### Solução Implementada

O MD Converter implementa **defesa em profundidade** com múltiplas camadas de proteção:

#### 1. Sanitização com Werkzeug

Todos os nomes de arquivo passam pela função `secure_filename()` do framework Werkzeug, que:

- Remove caracteres ASCII não imprimíveis
- Substitui espaços por underscores
- Remove separadores de caminho (`/`, `\`)
- Remove caracteres perigosos (`..`, null bytes)

```python
from werkzeug.utils import secure_filename

# Exemplo de transformação
secure_filename("../../etc/passwd")  # → "etc_passwd"
```

#### 2. Validação Adicional

A função customizada `sanitize_filename()` adiciona camadas extras:

- **Limite de comprimento**: Máximo de 200 caracteres (docs) ou 100 (logos)
- **Detecção de padrões suspeitos**: Identifica tentativas de path traversal
- **Geração de nomes seguros**: Cria identificadores únicos (UUID) para nomes completamente inválidos
- **Extensões padrão**: Força `.md` ou `.txt` se não houver extensão

```python
from app.utils.file_security import sanitize_filename

# Nomes suspeitos são substituídos
sanitize_filename("", default_extension=".md")
# → "uploaded_file_a1b2c3d4.md"
```

#### 3. Logging de Auditoria

Todas as tentativas suspeitas são registradas nos logs com:

- Nome do arquivo original
- Nome sanitizado gerado
- Endereço IP do cliente
- Timestamp da tentativa

**Exemplo de log:**
```
WARNING - Tentativa de path traversal detectada! Original: '../../etc/passwd', Sanitizado: 'etc_passwd.md', IP: 192.168.1.100
```

### Exemplos de Transformação

A tabela abaixo mostra como diferentes tipos de ataque são neutralizados:

| Tipo de Ataque | Input do Usuário | Output Sanitizado | Descrição |
|----------------|------------------|-------------------|-----------|
| Path Traversal | `../../etc/passwd` | `etc_passwd.md` | Sequências `../` removidas |
| Caminho Absoluto | `/etc/passwd` | `etc_passwd.md` | Barra inicial removida |
| Windows Path | `..\\..\\system32` | `system32.md` | Backslashes removidos |
| Null Byte Injection | `file.md\x00.exe` | `file.md` | Null byte removido |
| Caracteres Especiais | `file<>name?.md` | `filename.md` | Chars perigosos removidos |
| Nome Completamente Inválido | `../../` | `uploaded_file_a1b2c3d4.md` | UUID gerado |
| Nome Muito Longo | `a`×300 + `.md` | `aaa...aa.md` (200 chars) | Truncado preservando extensão |

### Pontos de Aplicação

A sanitização é aplicada em **todos os pontos de upload** da aplicação:

| Endpoint | Arquivo | Linha | Descrição |
|----------|---------|-------|-----------|
| `POST /relatorio/convert-md` | `app/routes/conversion.py` | 38 | Upload de arquivos Markdown |
| `POST /relatorio/convert-md` | `app/routes/conversion.py` | 99 | Upload de logos customizados |
| `POST /relatorio/process-meeting` | `app/routes/meeting.py` | 60 | Upload de arquivos de reunião |

### Testes de Segurança

A implementação é validada por **20+ casos de teste** em `tests/test_file_security.py`:

```bash
# Executar testes de segurança
pytest tests/test_file_security.py -v

# Verificar cobertura
pytest tests/test_file_security.py --cov=app/utils/file_security --cov-report=term-missing
```

**Casos de teste cobertos:**
- ✅ Path traversal (`../../etc/passwd`)
- ✅ Caminhos absolutos Unix (`/etc/passwd`)
- ✅ Caminhos Windows (`..\\system32`)
- ✅ Null byte injection (`file\x00.exe`)
- ✅ Caracteres Unicode (`relatório_çã.md`)
- ✅ Nomes vazios e None
- ✅ Nomes muito longos (300+ chars)
- ✅ Caracteres especiais (`<>?*|`)

---

## Monitoramento e Detecção

### Logs de Segurança

Para monitorar tentativas de ataque em tempo real:

```bash
# Ver todas as tentativas de path traversal
docker logs md-converter | grep "path traversal"

# Contar tentativas nas últimas 24 horas
docker logs md-converter --since 24h | grep -i "path traversal" | wc -l

# Identificar IPs suspeitos com mais tentativas
docker logs md-converter | grep "path traversal" | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -10

# Verificar nomes de arquivo inválidos
docker logs md-converter | grep "Nome inválido"
```

### Métricas Recomendadas

Configure alertas para as seguintes condições:

| Métrica | Threshold | Severidade | Ação |
|---------|-----------|------------|------|
| Tentativas de path traversal | > 10 em 5min (mesmo IP) | 🔴 Alta | Bloquear IP, investigar |
| Filenames inválidos | > 50 em 1h | 🟡 Média | Revisar logs |
| Taxa de erro 400 | > 20% dos uploads | 🟡 Média | Verificar funcionalidade |

### Dashboard Sugerido (Grafana/Prometheus)

Se estiver usando Grafana/Prometheus, configure os seguintes painéis:

```yaml
panels:
  - title: "Tentativas de Path Traversal (24h)"
    query: 'rate(path_traversal_attempts[24h])'

  - title: "Top 10 IPs Suspeitos"
    query: 'topk(10, count by (client_ip) (path_traversal_attempts))'

  - title: "Taxa de Uploads Bem-Sucedidos"
    query: '(successful_uploads / total_uploads) * 100'
```

---

## Recomendações Adicionais

### 1. Rate Limiting

**Status**: ⚠️ Não implementado
**Prioridade**: Alta

Implemente rate limiting para prevenir ataques de força bruta:

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@limiter.limit("5 per minute")
@conversion_bp.route("/convert-md", methods=["POST"])
def convert_md():
    ...
```

### 2. Validação de Tipo MIME

**Status**: ⚠️ Não implementado
**Prioridade**: Média

Adicione validação do tipo MIME real do arquivo (não apenas extensão):

```python
import magic

# Verificar tipo MIME real
file_type = magic.from_buffer(uploaded.read(2048), mime=True)
uploaded.seek(0)

ALLOWED_MIMES = {'text/markdown', 'text/plain', 'audio/mpeg'}
if file_type not in ALLOWED_MIMES:
    abort(400, f"Tipo de arquivo não permitido: {file_type}")
```

### 3. Monitoramento Diário de Logs

**Status**: 📋 Processo manual
**Prioridade**: Alta

- Revise logs de segurança **diariamente** durante a primeira semana após deploy
- Configure alertas automáticos para tentativas repetidas do mesmo IP
- Mantenha logs por no mínimo 30 dias para análise forense

### 4. Atualização de Dependências

**Status**: ✅ Dependências atuais
**Prioridade**: Contínua

Mantenha as bibliotecas de segurança atualizadas:

```bash
# Verificar dependências desatualizadas
pip list --outdated | grep -E "werkzeug|flask"

# Atualizar dependências de segurança
pip install --upgrade werkzeug flask
```

**Dependências críticas:**
- `werkzeug >= 2.0.0` - Função `secure_filename()` melhorada
- `flask >= 3.0.0` - Correções de segurança

### 5. HTTPS em Produção

**Status**: ⚠️ Configuração do servidor
**Prioridade**: Crítica

**NUNCA** execute a aplicação em produção sem HTTPS:

```nginx
# Configuração Nginx com HTTPS
server {
    listen 443 ssl http2;
    server_name md-converter.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## Resposta a Incidentes

### Identificação de Ataque Ativo

Se você detectar tentativas coordenadas de ataque:

1. **Identificar o padrão**:
   ```bash
   # Ver detalhes das tentativas
   docker logs md-converter | grep "path traversal" | tail -50
   ```

2. **Bloquear IPs suspeitos** (temporariamente):
   ```bash
   # Adicionar regra UFW
   sudo ufw deny from 192.168.1.100
   ```

3. **Investigar escopo**:
   ```bash
   # Verificar se houve uploads bem-sucedidos do mesmo IP
   docker logs md-converter | grep "192.168.1.100" | grep "PDF criado"
   ```

4. **Revisar arquivos criados** (se houver suspeita de comprometimento):
   ```bash
   # Listar uploads recentes
   find /data/uploads -type f -mmin -60 -ls
   ```

### Contatos de Emergência

Em caso de incidente de segurança crítico:

- **Equipe de Segurança**: [definir contato]
- **Administrador de Sistema**: [definir contato]
- **Responsável pela Aplicação**: [definir contato]

---

## Referências

- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [Werkzeug Security Utils](https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.utils.secure_filename)

---

**Documento Versionado**: v1.0.0
**Data**: 2025-01-16
**Próxima Revisão**: 2025-02-16
