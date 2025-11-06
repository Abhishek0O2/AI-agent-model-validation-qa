import os
import pytest
import requests
from jsonschema import validate
import subprocess, time, socket, sys
import json
from datetime import datetime
from threading import Lock

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

class TrackedSession(requests.Session):
    """Session wrapper that captures all API calls for reporting."""
    
    def __init__(self):
        super().__init__()
        self._captured_calls = []
    
    def post(self, url, **kwargs):
        """POST with request/response capture."""
        response = super().post(url, **kwargs)
        
        api_call = {
            "method": "POST",
            "url": url,
            "request_payload": kwargs.get('json'),
            "request_data": kwargs.get('data'),
            "status_code": response.status_code,
            "elapsed_seconds": round(response.elapsed.total_seconds(), 3),
        }
        
        try:
            api_call["response_payload"] = response.json()
        except:
            api_call["response_text"] = response.text[:500] if response.text else ""
        
        self._captured_calls.append(api_call)
        return response
    
    def get(self, url, **kwargs):
        """GET with request/response capture."""
        response = super().get(url, **kwargs)
        
        api_call = {
            "method": "GET",
            "url": url,
            "request_params": kwargs.get('params'),
            "status_code": response.status_code,
            "elapsed_seconds": round(response.elapsed.total_seconds(), 3),
        }
        
        try:
            api_call["response_payload"] = response.json()
        except:
            api_call["response_text"] = response.text[:500] if response.text else ""
        
        self._captured_calls.append(api_call)
        return response

@pytest.fixture(scope="session")
def session():
    s = TrackedSession()
    s._captured_calls = []
    yield s
    s.close()

# --- Global capture for API calls made outside the session() fixture (e.g., in threaded load tests) ---
_GLOBAL_API_CALLS = []
_GLOBAL_API_LOCK = Lock()

_orig_post = requests.Session.post
_orig_get = requests.Session.get

def _capture_and_call(method_name, self, url, **kwargs):
    # If this is our TrackedSession, let it capture and skip global capture to avoid duplicates
    try:
        if isinstance(self, TrackedSession):
            if method_name == "POST":
                return _orig_post(self, url, **kwargs)
            else:
                return _orig_get(self, url, **kwargs)
    except Exception:
        # If isinstance check fails for any reason, continue with global capture path
        pass
    resp = None
    if method_name == "POST":
        resp = _orig_post(self, url, **kwargs)
    else:
        resp = _orig_get(self, url, **kwargs)
    try:
        entry = {
            "method": method_name,
            "url": url,
            "request_payload": kwargs.get("json"),
            "request_data": kwargs.get("data"),
            "request_params": kwargs.get("params"),
            "status_code": resp.status_code,
            "elapsed_seconds": round(resp.elapsed.total_seconds(), 3),
        }
        try:
            entry["response_payload"] = resp.json()
        except Exception:
            entry["response_text"] = resp.text[:500] if getattr(resp, "text", None) else ""
    except Exception:
        entry = {"method": method_name, "url": url}
    with _GLOBAL_API_LOCK:
        _GLOBAL_API_CALLS.append(entry)
    return resp

def _patched_post(self, url, **kwargs):
    return _capture_and_call("POST", self, url, **kwargs)

def _patched_get(self, url, **kwargs):
    return _capture_and_call("GET", self, url, **kwargs)

# Apply global monkey patches so any requests.Session usage is captured
requests.Session.post = _patched_post
requests.Session.get = _patched_get

# Storage for detailed test information and per-test metrics
_test_details_store = []

# Storage for tracking assertions per API call
_current_test_assertions = []

def track_assertion(assertion_text, passed=True, related_response=None):
    """Track an assertion for the current test."""
    _current_test_assertions.append({
        "assertion": assertion_text,
        "passed": passed,
        "related_response": related_response
    })

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Capture test execution details including API calls and assertions."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        global _current_test_assertions
        
        # Get the session fixture if it was used
        captured_calls = []
        if 'session' in item.funcargs:
            session_obj = item.funcargs['session']
            if hasattr(session_obj, '_captured_calls'):
                captured_calls = list(session_obj._captured_calls)
                session_obj._captured_calls.clear()  # Clear for next test
        
        # Also include any globally captured calls (e.g., from concurrent threads)
        global_calls = []
        with _GLOBAL_API_LOCK:
            if _GLOBAL_API_CALLS:
                global_calls = list(_GLOBAL_API_CALLS)
                _GLOBAL_API_CALLS.clear()

        # Extract assertions from test source code using AST (robust to commas/line breaks)
        assertions = []
        source = None
        if hasattr(item, 'obj') and item.obj:
            import inspect, ast
            source = inspect.getsource(item.obj)
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assert):
                        try:
                            condition_text = ast.unparse(node.test)  # py3.9+
                        except Exception:
                            condition_text = str(getattr(node, 'test', ''))
                        assertions.append({
                            "condition": condition_text,
                            "passed": report.outcome == "passed",
                            "full_assertion": f"assert {condition_text}"
                        })
            except Exception:
                # Fallback: no assertions captured if parsing fails
                pass

        test_data = {
            "test_name": item.nodeid,
            "test_function": item.name,
            "test_module": item.module.__name__ if hasattr(item, 'module') else "",
            "outcome": report.outcome,
            "duration": report.duration,
            "timestamp": datetime.now().isoformat(),
            "markers": [m.name for m in item.iter_markers()],
            "api_calls": captured_calls + global_calls,
            "docstring": item.obj.__doc__ if hasattr(item, 'obj') and item.obj.__doc__ else "",
            "assertions": assertions,
            "source_code": source or ""
        }
        
        # attach collected assertions (no AST duplicate capture)
        if assertions:
            test_data["assertions"] = assertions
        
        # Include any metrics attached by tests via the 'recorder' fixture
        perf_metrics = getattr(item, "_perf_metrics", None)
        if perf_metrics is not None:
            test_data["metrics"] = perf_metrics
        
        if report.failed:
            test_data["failure_message"] = str(report.longrepr)
        
        _test_details_store.append(test_data)

def pytest_sessionfinish(session, exitstatus):
    """Save detailed test information to JSON.

    Honors REPORTS_DIR env var to allow separating artifacts for perf runs.
    """
    from pathlib import Path
    reports_base = os.getenv("REPORTS_DIR", "reports")
    reports_dir = Path(reports_base)
    reports_dir.mkdir(exist_ok=True)
    
    output_file = reports_dir / "test_details.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "exit_status": exitstatus,
            "total_tests": len(_test_details_store),
            "tests": _test_details_store
        }, f, indent=2, default=str)
    
    print(f"\n✓ Detailed API logs saved to: {output_file}")

# --- Fixture to allow tests to attach performance metrics to reports ---
@pytest.fixture
def recorder(request):
    class _Recorder:
        def __init__(self, item):
            self._item = item
            if not hasattr(self._item, "_perf_metrics"):
                setattr(self._item, "_perf_metrics", {})
        def metrics(self, data: dict):
            """Attach a dictionary of metrics to the current test."""
            m = getattr(self._item, "_perf_metrics", {})
            m.update(data or {})
            setattr(self._item, "_perf_metrics", m)
        def add(self, key: str, value):
            m = getattr(self._item, "_perf_metrics", {})
            m[key] = value
            setattr(self._item, "_perf_metrics", m)
    return _Recorder(request.node)

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