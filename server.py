"""
Ponto de entrada local do MD Converter.

Expõe a aplicação Flask criada pela factory e adiciona logs de boot para
facilitar depuração de ambiente e conferência de rotas registradas.
"""

import logging
import os
from app import create_app

# Logging controlado por `LOG_LEVEL`, útil tanto no dev server quanto no Gunicorn.
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# A aplicação real é construída em `app/__init__.py`.
app = create_app()

# Informações de boot úteis para operação e troubleshooting.
logger.info(f"Application starting with log level: {log_level}")
logger.info(f"Flask environment: {os.environ.get('FLASK_ENV', 'development')}")

# Lista de rotas registrada no startup para inspeção rápida em logs.
logger.info("=== ROTAS REGISTRADAS ===")
for rule in app.url_map.iter_rules():
    logger.info(f"Route: {rule.rule} | Methods: {list(rule.methods)} | Endpoint: {rule.endpoint}")
logger.info("=========================")

if __name__ == "__main__":
    # O dev server é suficiente para uso local; produção usa Gunicorn no Dockerfile.
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
