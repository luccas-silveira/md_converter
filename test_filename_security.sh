#!/bin/bash

# Script de teste manual para validação de segurança de filenames
# Testa a proteção contra path traversal e outras tentativas maliciosas
#
# Uso: ./test_filename_security.sh [BASE_URL]
# Exemplo: ./test_filename_security.sh http://localhost:8080

set -e

# Configuração
BASE_URL="${1:-http://localhost:8080}"
ENDPOINT="/relatorio/convert-md"
FULL_URL="${BASE_URL}${ENDPOINT}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Teste de Segurança - Path Traversal"
echo "========================================"
echo "Endpoint: ${FULL_URL}"
echo ""

# Criar arquivo de teste temporário com conteúdo Markdown válido
TEST_CONTENT="# Documento de Teste

Este é um arquivo de teste para validação de segurança.

## Seção 1
Conteúdo de exemplo.
"

# Função auxiliar para teste
test_upload() {
    local filename="$1"
    local description="$2"
    local expected_result="$3"

    echo -e "${YELLOW}Teste: ${description}${NC}"
    echo "Filename: ${filename}"

    # Criar arquivo temporário
    TEMP_FILE=$(mktemp)
    echo "$TEST_CONTENT" > "$TEMP_FILE"

    # Fazer upload com curl
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -F "file=@${TEMP_FILE};filename=${filename}" \
        -F "cover_subtitulo=Teste" \
        -F "cover_descricao=Validação de Segurança" \
        "${FULL_URL}")

    # Verificar resultado
    if [ "$HTTP_CODE" == "$expected_result" ]; then
        echo -e "${GREEN}✓ PASSOU${NC} - HTTP ${HTTP_CODE} (esperado: ${expected_result})"
    else
        echo -e "${RED}✗ FALHOU${NC} - HTTP ${HTTP_CODE} (esperado: ${expected_result})"
    fi

    # Cleanup
    rm -f "$TEMP_FILE"
    echo ""
}

# 1. Teste de Path Traversal - Unix
test_upload "../../etc/passwd" \
    "Path Traversal Unix (../..)" \
    "200"

# 2. Teste de Path Traversal - Caminho absoluto
test_upload "/etc/passwd" \
    "Caminho absoluto Unix" \
    "200"

# 3. Teste de Path Traversal - Windows
test_upload "..\\..\\system32\\config" \
    "Path Traversal Windows (..\\..)" \
    "200"

# 4. Teste de Null Byte Injection
# Nota: Bash pode ter problemas com null bytes, este teste pode ser limitado
test_upload "arquivo.md%00.exe" \
    "Null Byte Injection (URL-encoded)" \
    "200"

# 5. Teste de caracteres especiais
test_upload "file<>name?.md" \
    "Caracteres especiais (<>?)" \
    "200"

# 6. Teste de nome extremamente longo
LONG_NAME=$(printf 'a%.0s' {1..300})".md"
test_upload "${LONG_NAME}" \
    "Nome muito longo (300+ chars)" \
    "200"

# 7. Teste de nome vazio (deve falhar ou gerar nome genérico)
test_upload "" \
    "Nome de arquivo vazio" \
    "400"

# 8. Teste de nome válido (controle positivo)
test_upload "documento_valido_2024.md" \
    "Nome válido (controle positivo)" \
    "200"

# 9. Teste com Unicode
test_upload "relatório_reunião_2024.md" \
    "Nome com caracteres Unicode (acentos)" \
    "200"

# 10. Teste de múltiplas barras
test_upload "///etc///passwd" \
    "Múltiplas barras consecutivas" \
    "200"

echo "========================================"
echo "Verificação de Logs"
echo "========================================"
echo ""
echo -e "${YELLOW}Comandos para verificar logs de segurança:${NC}"
echo ""
echo "# Ver tentativas de path traversal:"
echo "docker logs md-converter | grep \"path traversal\""
echo ""
echo "# Contar tentativas nas últimas 24h:"
echo "docker logs md-converter --since 24h | grep -i \"path traversal\" | wc -l"
echo ""
echo "# Identificar IPs suspeitos:"
echo "docker logs md-converter | grep \"path traversal\" | awk '{print \$NF}' | sort | uniq -c | sort -rn"
echo ""
echo "# Verificar nomes inválidos:"
echo "docker logs md-converter | grep \"Nome inválido\""
echo ""
echo "========================================"
echo "Testes Concluídos"
echo "========================================"
