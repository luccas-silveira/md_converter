"""
Rota opcional para gerar textos da capa (subtítulo e descrição) com IA.

Usa a API da DeepSeek (compatível com o SDK da OpenAI). É opt-in: o frontend
só chama este endpoint quando o usuário clica em "Gerar com IA". A conversão
normal (`/convert-md`) não depende disto.
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import json
import logging
import os

from openai import OpenAI

cover_ai_bp = Blueprint('cover_ai', __name__)
logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parent.parent.parent

# Limite de contexto: documento inteiro até este teto (protege o contexto do modelo).
MAX_DOC_CHARS = 50_000

DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')


@cover_ai_bp.route("/suggest-cover", methods=["POST"])
def suggest_cover():
    """Recebe o texto do documento e devolve {subtitulo, descricao} gerados por IA."""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return jsonify({"error": "IA indisponível: DEEPSEEK_API_KEY não configurada."}), 503

    document = (request.form.get('document') or '').strip()
    if not document:
        return jsonify({"error": "Documento vazio."}), 400

    try:
        prompt_template = (APP_ROOT / "prompts" / "prompt_capa.md").read_text(encoding="utf-8")
        prompt = prompt_template.replace('<<DOCUMENTO>>', document[:MAX_DOC_CHARS])

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=30)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=500,
        )
        data = json.loads(response.choices[0].message.content)
        # título: garante no máximo 2 palavras (defesa caso o modelo extrapole).
        titulo = " ".join((data.get("titulo") or "").strip().split()[:2])
        return jsonify({
            "titulo": titulo,
            "subtitulo": (data.get("subtitulo") or "").strip(),
            "descricao": (data.get("descricao") or "").strip(),
        }), 200

    except Exception as e:
        logger.error(f"Erro ao gerar capa com IA: {e}")
        return jsonify({"error": "Não foi possível gerar os textos. Preencha manualmente."}), 502
