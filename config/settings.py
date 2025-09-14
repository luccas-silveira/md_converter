"""
Configurações da aplicação
"""

import os
from pathlib import Path

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configurações do Flask
class Config:
    """Configuração base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Diretórios
    ASSETS_DIR = PROJECT_ROOT / 'assets'
    TEMPLATES_DIR = PROJECT_ROOT / 'app' / 'templates'
    PROMPTS_DIR = PROJECT_ROOT / 'prompts'

    # OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

    # Whisper
    WHISPER_MODEL = 'base'

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False

# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}