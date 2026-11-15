import threading
import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.services.session_store import session_store
import sys
from pathlib import Path

# Anadir dev-tools al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "dev-tools"))
import mcp_server

_server_started = False

@pytest.fixture(scope="session", autouse=True)
def run_local_mcp_server():
    # Arranca el servidor MCP clon de dev-tools en un hilo para tests locales rapidos y sin limite de peticiones
    global _server_started
    test_port = 8005
    test_mcp_url = f"http://127.0.0.1:{test_port}/mcp"

    if not _server_started:
        def start_mcp():
            mcp_server.server.run(
                transport="streamable-http",
                host="127.0.0.1",
                port=test_port,
                streamable_http_path="/mcp"
            )

        t = threading.Thread(target=start_mcp, daemon=True)
        t.start()
        time.sleep(1)
        _server_started = True

    original_url = settings.MCP_URL
    original_token = settings.MCP_TOKEN

    # Apuntar al servidor MCP local de pruebas
    settings.MCP_URL = test_mcp_url
    settings.MCP_TOKEN = "test-token"

    yield

    # Restaurar valores originales
    settings.MCP_URL = original_url
    settings.MCP_TOKEN = original_token

@pytest.fixture(autouse=True)
def clean_session_store():
    # Limpia el almacen de sesiones antes de cada test para garantizar aislamiento
    session_store._sessions.clear()
    yield
    session_store._sessions.clear()

@pytest.fixture
def client():
    # Cliente de pruebas para FastAPI
    return TestClient(app)
