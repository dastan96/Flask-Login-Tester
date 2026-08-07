import os
import socket
import threading

import pytest
from werkzeug.serving import make_server

from app import app


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def login_ui_base_url():
    configured_url = os.environ.get("LOGIN_UI_BASE_URL")
    if configured_url:
        yield configured_url.rstrip("/")
        return

    app.config["TESTING"] = True
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
