"""Server-Sent Events (SSE) event bus.

A simple publish/subscribe system that pushes events to connected
SSE clients.  Thread-safe - publishers can call emit() from any thread
(sensor callbacks, recording helpers, presence monitor).

Usage:
    from modules.sse import emit, stream

    # Publish an event (from any thread):
    emit("sensor_state", {"armed": True, "triggered": False})

    # Flask endpoint (yields SSE text/event-stream):
    @app.route('/events')
    def events():
        return Response(stream(), mimetype='text/event-stream')
"""

import json
import logging
import queue
import threading
import time

log = logging.getLogger("sse")

# Each connected client gets its own queue.
# _clients is guarded by _clients_lock.
_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()

# Monotonic event ID for Last-Event-ID reconnection support
_event_id = 0
_event_id_lock = threading.Lock()

# Optional hook called when a new SSE client connects.
# Set via set_on_connect() to avoid circular imports.
_on_client_connect = None


def emit(event: str, data: dict | None = None) -> None:
    """Broadcast an event to all connected SSE clients.

    Args:
        event: Event type string (e.g. "sensor_state", "recording_state").
        data:  JSON-serialisable payload dict (optional).
    """
    global _event_id
    with _event_id_lock:
        _event_id += 1
        eid = _event_id

    payload = {"event": event, "data": data or {}, "time": time.time(), "id": eid}

    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(payload)
            except queue.Full:
                # Client queue full - drop oldest and push new
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    dead.append(q)

        for q in dead:
            _clients.remove(q)
        count = len(_clients)

    log.debug("SSE emit: %s (%d clients)", event, count)


def set_on_connect(callback):
    """Register a callback invoked when a new SSE client connects.

    Used to trigger an immediate presence poll so device statuses
    are fresh when the dashboard loads.  Avoids circular imports
    by letting main.py wire the callback after all modules load.
    """
    global _on_client_connect
    _on_client_connect = callback


def stream():
    """Generator that yields SSE-formatted events for one client.

    Each connected client gets its own queue.  The generator blocks on
    the queue and yields events as they arrive.  A heartbeat comment is
    sent every 15 seconds to keep the connection alive.
    """
    client_queue: queue.Queue = queue.Queue(maxsize=64)

    with _clients_lock:
        _clients.append(client_queue)

    log.info("SSE client connected (%d total)", len(_clients))

    # Notify hook (e.g. trigger immediate presence poll)
    if _on_client_connect:
        try:
            _on_client_connect()
        except Exception:
            pass

    try:
        # Send initial heartbeat so the client knows we're alive
        yield ": heartbeat\n\n"

        while True:
            try:
                payload = client_queue.get(timeout=15)
                line = f"id: {payload['id']}\nevent: {payload['event']}\ndata: {json.dumps(payload['data'])}\n\n"
                yield line
            except queue.Empty:
                # No events for 15s - send heartbeat to keep connection alive
                yield ": heartbeat\n\n"
    except GeneratorExit:
        pass
    finally:
        with _clients_lock:
            try:
                _clients.remove(client_queue)
            except ValueError:
                pass
        log.info("SSE client disconnected (%d remaining)", len(_clients))


def client_count() -> int:
    """Return number of connected SSE clients."""
    with _clients_lock:
        return len(_clients)
