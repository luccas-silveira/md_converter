"""
MDconverter - Aplicação Flask para conversão de Markdown para PDF
e processamento de resumos de reuniões com IA.
"""

from flask import Flask
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import os

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)

    # Configurar prefixo para reverse proxy
    class ReverseProxied(object):
        def __init__(self, app, script_name=None, scheme=None, server=None):
            self.app = app
            self.script_name = script_name
            self.scheme = scheme
            self.server = server

        def __call__(self, environ, start_response):
            script_name = environ.get('HTTP_X_SCRIPT_NAME', '') or self.script_name
            if script_name:
                environ['SCRIPT_NAME'] = script_name
                path_info = environ['PATH_INFO']
                if path_info.startswith(script_name):
                    environ['PATH_INFO'] = path_info[len(script_name):]
            scheme = environ.get('HTTP_X_SCHEME', '') or self.scheme
            if scheme:
                environ['wsgi.url_scheme'] = scheme
            server = environ.get('HTTP_X_FORWARDED_SERVER', '') or self.server
            if server:
                environ['HTTP_HOST'] = server
            return self.app(environ, start_response)

    app.wsgi_app = ReverseProxied(app.wsgi_app, script_name='/relatorio')

    # Configurações
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_FOLDER'] = '/tmp'
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

    # Registrar blueprints/rotas
    from app.routes.main import main_bp
    from app.routes.conversion import conversion_bp
    from app.routes.progress import progress_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(conversion_bp)
    app.register_blueprint(progress_bp)

    # Importar módulo de reunião condicionalmente
    try:
        from app.routes.meeting import meeting_bp
        app.register_blueprint(meeting_bp)
        print("✓ Módulo de reunião carregado com sucesso")
    except Exception as e:
        print(f"⚠️  Módulo de reunião não carregado: {e}")
        print("   A aplicação continuará funcionando sem recursos de IA")

    # Error handlers
    @app.errorhandler(413)
    def handle_file_too_large(e):
        return {
            "error": "Arquivo muito grande. Tamanho máximo permitido: 100MB",
            "max_size_mb": 100
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
        return {
            "error": "Arquivo muito grande. Tamanho máximo permitido: 100MB",
            "max_size_mb": 100
        }, 413

    return app