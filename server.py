"""
MDconverter - Aplicação principal
"""

import logging
import os
from app import create_app

# Configurar logging baseado no ambiente
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação
app = create_app()

# Log startup info
logger.info(f"Application starting with log level: {log_level}")
logger.info(f"Flask environment: {os.environ.get('FLASK_ENV', 'development')}")

if __name__ == "__main__":
    # Flask dev server (apenas para desenvolvimento)
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)