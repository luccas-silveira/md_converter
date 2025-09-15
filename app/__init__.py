"""
MDconverter - Aplicação Flask para conversão de Markdown para PDF
e processamento de resumos de reuniões com IA.
"""

from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import os

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)

    # Configurações (agora via variáveis de ambiente com defaults)
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 1024 * 1024 * 1024))
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = int(os.environ.get('SEND_FILE_MAX_AGE', 0))

    # Garantir que a pasta de upload exista (quando não é /tmp)
    try:
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        if str(upload_dir) not in ('/tmp', '/var/tmp'):
            upload_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Evitar falhar no boot por permissão; logs via servidor
        pass

    # Registrar blueprints/rotas com prefixo /relatorio
    from app.routes.main import main_bp
    from app.routes.conversion import conversion_bp
    from app.routes.progress import progress_bp

    app.register_blueprint(main_bp, url_prefix='/relatorio')
    app.register_blueprint(conversion_bp, url_prefix='/relatorio')
    app.register_blueprint(progress_bp, url_prefix='/relatorio')

    # Importar módulo de reunião condicionalmente
    try:
        from app.routes.meeting import meeting_bp
        app.register_blueprint(meeting_bp, url_prefix='/relatorio')
        print("✓ Módulo de reunião carregado com sucesso")
    except Exception as e:
        print(f"⚠️  Módulo de reunião não carregado: {e}")
        print("   A aplicação continuará funcionando sem recursos de IA")

    # Error handlers
    @app.errorhandler(413)
    def handle_file_too_large(e):
        max_mb = int(app.config.get('MAX_CONTENT_LENGTH', 0) / (1024 * 1024))
        return {
            "error": f"Arquivo muito grande. Tamanho máximo permitido: {max_mb}MB",
            "max_size_mb": max_mb
        }, 413

    @app.errorhandler(400)
    def handle_bad_request(e):
        return {"error": "Requisição inválida"}, 400

    @app.errorhandler(404)
    def handle_not_found(e):
        return {"error": "Endpoint não encontrado"}, 404

    @app.errorhandler(500)
    def handle_500(e):
        import traceback
        return {
            "error": "Erro interno do servidor",
            "traceback": traceback.format_exc() if app.debug else None
        }, 500

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e):
        max_mb = int(app.config.get('MAX_CONTENT_LENGTH', 0) / (1024 * 1024))
        return {
            "error": f"Arquivo muito grande. Tamanho máximo permitido: {max_mb}MB",
            "max_size_mb": max_mb
        }, 413

    # Healthcheck leve
    @app.get('/relatorio/healthz')
    def healthz():
        return jsonify({"status": "ok"}), 200

    return app
