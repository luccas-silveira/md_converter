"""
Utilidades de segurança para manipulação de arquivos.

Este módulo fornece funções para sanitizar nomes de arquivo fornecidos por usuários,
prevenindo ataques de path traversal e garantindo nomes de arquivo seguros.
"""

import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


def sanitize_filename(
    filename: Optional[str],
    default_extension: Optional[str] = None,
    max_length: int = 255
) -> str:
    """
    Sanitiza nome de arquivo fornecido por usuário para prevenir path traversal.

    Esta função implementa múltiplas camadas de proteção:
    1. Trata casos de filename vazio ou None
    2. Aplica secure_filename() do Werkzeug para remover caracteres perigosos
    3. Gera nome seguro se secure_filename() retornar vazio
    4. Força extensão padrão se não houver
    5. Limita o comprimento do filename
    6. Registra tentativas suspeitas nos logs de segurança

    Args:
        filename: Nome do arquivo original fornecido pelo usuário (pode ser None)
        default_extension: Extensão padrão a ser adicionada se não houver (ex: '.md', '.txt')
        max_length: Comprimento máximo permitido para o nome do arquivo (padrão: 255)

    Returns:
        Nome de arquivo seguro e sanitizado

    Raises:
        ValueError: Se não for possível gerar um nome de arquivo seguro e nenhuma
                   extensão padrão foi fornecida

    Examples:
        >>> sanitize_filename("../../etc/passwd", ".md")
        'etc_passwd.md'

        >>> sanitize_filename("/etc/passwd", ".md")
        'etc_passwd.md'

        >>> sanitize_filename("arquivo válido.md")
        'arquivo_valido.md'

        >>> sanitize_filename("", ".md")
        'uploaded_file_a1b2c3d4.md'
    """
    # Caso 1: Filename vazio ou None
    if not filename or not filename.strip():
        if default_extension:
            safe_name = f"uploaded_file_{uuid4().hex[:8]}{default_extension}"
            logger.warning(f"Nome de arquivo vazio fornecido, usando nome gerado: {safe_name}")
            return safe_name
        raise ValueError("Nome de arquivo não fornecido e nenhuma extensão padrão especificada")

    # Caso 2: Sanitizar com werkzeug.secure_filename()
    safe_name = secure_filename(filename)

    # Caso 3: secure_filename retornou vazio (nome completamente inválido)
    if not safe_name or safe_name == '':
        # Tentar preservar extensão original se possível
        original_ext = Path(filename).suffix
        if original_ext and len(original_ext) <= 10:  # Validar tamanho razoável da extensão
            safe_ext = secure_filename(original_ext)
        else:
            safe_ext = default_extension or ''

        safe_name = f"uploaded_file_{uuid4().hex[:8]}{safe_ext}"
        logger.warning(
            f"Nome de arquivo inválido '{filename}' substituído por '{safe_name}'"
        )

    # Caso 4: Forçar extensão padrão se não houver
    if default_extension and not Path(safe_name).suffix:
        safe_name = f"{safe_name}{default_extension}"

    # Caso 5: Limitar comprimento do filename
    if len(safe_name) > max_length:
        # Preservar a extensão ao truncar
        name_part = Path(safe_name).stem[:max_length-20]  # Reservar espaço para extensão
        ext_part = Path(safe_name).suffix[:10]
        safe_name = f"{name_part}{ext_part}"
        logger.info(f"Nome de arquivo truncado para {max_length} caracteres: {safe_name}")

    # Log de segurança para nomes suspeitos (tentativa de path traversal)
    dangerous_patterns = ['..', '/', '\\', '\x00']
    if any(dangerous in filename for dangerous in dangerous_patterns):
        # Tentar obter informações da requisição para logging (se disponível)
        try:
            from flask import request
            client_ip = request.remote_addr if request else 'N/A'
        except (ImportError, RuntimeError):
            # Flask request context não disponível (ex: chamada direta)
            client_ip = 'N/A'

        logger.warning(
            f"Tentativa de path traversal detectada! "
            f"Original: '{filename}', Sanitizado: '{safe_name}', "
            f"IP: {client_ip}"
        )

    return safe_name
