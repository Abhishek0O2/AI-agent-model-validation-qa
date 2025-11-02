import os
import pytest
import requests
from jsonschema import validate
import subprocess, time, socket, sys

# Basic config for tests
MODEL_BASE_URL = os.getenv("MODEL_URL", "http://localhost:8000")
INFER_PATH = os.getenv("MODEL_INFER_PATH", "/v1/model/infer")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_S", "10"))
CONF_FLOOR = float(os.getenv("CONFIDENCE_FLOOR", "0.7"))

RESPONSE_SCHEMA_MIN = {
    "type": "object",
    "required": ["class", "confidence"],
    "properties": {
        "class": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "explanations": {"type": "array"},
        "warnings": {"type": "array"},
    },
}

def assert_min_response(body: dict):
    validate(instance=body, schema=RESPONSE_SCHEMA_MIN)

@pytest.fixture(scope="session")
def cfg():
    return {
        "base": MODEL_BASE_URL.rstrip("/"),
        "path": INFER_PATH,
        "timeout": REQUEST_TIMEOUT,
        "conf_floor": CONF_FLOOR,
    }

@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    yield s
    s.close()

# --- Auto-start FastAPI mock (uvicorn) ---
def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0

@pytest.fixture(scope="session", autouse=True)
def start_mock_server():
    use_mock = os.getenv("USE_MOCK", "1") == "1"
    if not use_mock:
        yield
        return

    proc = None
    if not _port_open("127.0.0.1", 8000):
        # The mock server lives in the "mock services" directory (space in name).
        # Use uvicorn's --app-dir so the module can be found without renaming the folder.
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "mock_server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--app-dir",
            "mock_services",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # wait up to 5s
        for _ in range(50):
            if _port_open("127.0.0.1", 8000):
                break
            time.sleep(0.1)

    os.environ.setdefault("MODEL_URL", "http://localhost:8000")
    os.environ.setdefault("MODEL_INFER_PATH", "/v1/model/infer")
    yield
    if proc:
        proc.terminate()