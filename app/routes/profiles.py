"""
Perfis de "preparado por" para preenchimento rápido da capa.

NÃO são credenciais — apenas nome/email/telefone salvos para reuso no dropdown
da capa. Armazenados num JSON dentro do volume persistente (UPLOAD_FOLDER) e
compartilhados entre todos que usam a ferramenta.
"""

from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
import json
import threading
import uuid

profiles_bp = Blueprint('profiles', __name__)

# ponytail: lock por processo + escrita atômica (rename). Com WORKERS>1 dois
# processos ainda podem intercalar (last-writer-wins), mas o rename evita
# corromper o arquivo. Aceitável para uma ação administrativa rara. Upgrade:
# mover para um lock de arquivo (flock) ou um banco se virar concorrido.
_lock = threading.Lock()


def _path() -> Path:
    base = current_app.config.get('UPLOAD_FOLDER', '/tmp')
    return Path(base) / 'profiles.json'


def _load() -> list:
    p = _path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return []


def _save(profiles: list) -> None:
    p = _path()
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(p)  # rename atômico


@profiles_bp.get('/profiles')
def list_profiles():
    """Lista todos os perfis cadastrados."""
    with _lock:
        return jsonify(_load()), 200


@profiles_bp.post('/profiles')
def add_profile():
    """Cadastra um perfil {nome, email, telefone}. Nome é obrigatório."""
    data = request.get_json(silent=True) or request.form
    nome = (data.get('nome') or '').strip()
    email = (data.get('email') or '').strip()
    telefone = (data.get('telefone') or '').strip()
    if not nome:
        return jsonify({"error": "Nome é obrigatório."}), 400
    # Limite de tamanho: evita payloads absurdos no JSON compartilhado.
    if any(len(v) > 200 for v in (nome, email, telefone)):
        return jsonify({"error": "Campo muito longo (máx. 200 caracteres)."}), 400

    profile = {"id": uuid.uuid4().hex[:8], "nome": nome, "email": email, "telefone": telefone}
    with _lock:
        profiles = _load()
        profiles.append(profile)
        _save(profiles)
    return jsonify(profile), 201


@profiles_bp.delete('/profiles/<pid>')
def delete_profile(pid):
    """Remove um perfil pelo id."""
    with _lock:
        profiles = _load()
        kept = [p for p in profiles if p.get('id') != pid]
        if len(kept) == len(profiles):
            return jsonify({"error": "Perfil não encontrado."}), 404
        _save(kept)
    return jsonify({"ok": True}), 200
