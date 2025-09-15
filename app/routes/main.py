"""
Rotas principais da aplicação
"""

from flask import Blueprint, render_template, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Página principal da aplicação"""
    max_size_mb = int(current_app.config.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024) / (1024 * 1024))
    return render_template('front.html', max_size_mb=max_size_mb)
