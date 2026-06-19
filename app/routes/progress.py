"""
Rotas para monitoramento de progresso via Server-Sent Events.

O estado é mantido em memória no processo atual. Isso é suficiente para o
frontend local e para o Compose padrão com `WORKERS=1`, mas não cria
sincronização entre múltiplos workers.
"""

from flask import Blueprint, Response
import threading
import time
import logging
import json

logger = logging.getLogger(__name__)

progress_bp = Blueprint('progress', __name__)

# Estado efêmero por processo, indexado por session_id.
progress_data = {}
progress_lock = threading.Lock()


def update_progress(session_id: str, percentage: int, message: str):
    """Atualiza o progresso de uma sessão no armazenamento em memória."""
    with progress_lock:
        progress_data[session_id] = {
            'percentage': percentage,
            'message': message,
            'timestamp': time.time()
        }
    logger.info(f"Progress updated - Session: {session_id}, {percentage}%: {message}")


def get_progress(session_id: str):
    """Recupera o progresso atual de uma sessão."""
    with progress_lock:
        return progress_data.get(session_id)


@progress_bp.route('/progress/<session_id>')
def progress_stream(session_id):
    """Mantém um stream SSE simples com o progresso calculado pelo backend."""
    def generate():
        # Garante um payload inicial mesmo quando o POST ainda não atualizou a sessão.
        if not get_progress(session_id):
            update_progress(session_id, 0, "Conectando...")

        start_time = time.time()
        timeout = 300  # timeout em segundos para conexões esquecidas

        while True:
            # Fecha streams órfãos para evitar manter conexões abertas indefinidamente.
            if time.time() - start_time > timeout:
                logger.warning(f"SSE connection timeout for session {session_id}")
                break

            progress = get_progress(session_id)
            if progress:
                yield f"data: {json.dumps({'percentage': progress['percentage'], 'message': progress['message']}, ensure_ascii=False)}\n\n"

                # Ao concluir, limpa o estado efêmero da sessão.
                if progress['percentage'] >= 100:
                    with progress_lock:
                        if session_id in progress_data:
                            del progress_data[session_id]
                    break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    })
