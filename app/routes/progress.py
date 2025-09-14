"""
Rotas para monitoramento de progresso via Server-Sent Events
"""

from flask import Blueprint, Response
import threading
import time
import logging

logger = logging.getLogger(__name__)

progress_bp = Blueprint('progress', __name__)

# Progress tracking
progress_data = {}
progress_lock = threading.Lock()


def update_progress(session_id: str, percentage: int, message: str):
    """Update progress for a specific session"""
    with progress_lock:
        progress_data[session_id] = {
            'percentage': percentage,
            'message': message,
            'timestamp': time.time()
        }
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

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                logger.warning(f"SSE connection timeout for session {session_id}")
                break

            progress = get_progress(session_id)
            if progress:
                yield f"data: {{'percentage': {progress['percentage']}, 'message': '{progress['message']}'}}\n\n"

                # If completed, stop streaming
                if progress['percentage'] >= 100:
                    # Clean up old progress data
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