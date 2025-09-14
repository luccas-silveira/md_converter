"""
Rotas principais da aplicação
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Página principal da aplicação"""
    return render_template('front.html')