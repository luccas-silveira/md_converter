"""
Rotas para monitoramento de progresso via Server-Sent Events
"""

from flask import Blueprint, Response
import threading
import time
import logging
import json

logger = logging.getLogger(__name__)

progress_bp = Blueprint('progress', __name__)

# Progress tracking
progress_data = {}
progress_lock = threading.Lock()


STALE_THRESHOLD = 600  # 10 minutes


def update_progress(session_id: str, percentage: int, message: str):
    """Update progress for a specific session"""
    now = time.time()
    with progress_lock:
        progress_data[session_id] = {
            'percentage': percentage,
            'message': message,
            'timestamp': now
        }
        # Cleanup stale entries to prevent memory leak
        stale_ids = [
            sid for sid, data in progress_data.items()
            if now - data['timestamp'] > STALE_THRESHOLD
        ]
        for sid in stale_ids:
            del progress_data[sid]
    if stale_ids:
        logger.info(f"Cleaned up {len(stale_ids)} stale progress entries")
    logger.info(f"Progress updated - Session: {session_id}, {percentage}%: {message}")


def get_progress(session_id: str):
    """Get progress for a specific session"""
    with progress_lock:
        return progress_data.get(session_id)


@progress_bp.route('/progress/<session_id>')
def progress_stream(session_id):
    """Server-Sent Events endpoint for progress updates"""
    def generate():
        # Initialize with 0% if no progress exists yet
        if not get_progress(session_id):
            update_progress(session_id, 0, "Conectando...")

        start_time = time.time()
        timeout = 300  # 5 minutes timeout

        try:
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.warning(f"SSE connection timeout for session {session_id}")
                    break

                progress = get_progress(session_id)
                if progress:
                    # Usar json.dumps para garantir JSON válido
                    data = {
                        'percentage': progress['percentage'],
                        'message': progress['message']
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                    # If completed, stop streaming
                    if progress['percentage'] >= 100:
                        break
                time.sleep(0.5)
        finally:
            with progress_lock:
                if session_id in progress_data:
                    del progress_data[session_id]

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    })