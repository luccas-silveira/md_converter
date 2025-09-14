"""
MDconverter - Aplicação principal
"""

import logging
from app import create_app

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Criar aplicação
app = create_app()

# Handler de erro global
@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Erro 500: {e}")
    return {"error": "Erro interno do servidor"}, 500

if __name__ == "__main__":
    # Flask dev server
    app.run(host="127.0.0.1", port=5000, debug=True)