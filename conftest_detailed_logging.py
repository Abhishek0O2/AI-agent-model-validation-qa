"""
Pytest plugin to capture detailed API request/response information for reporting.

This module hooks into pytest to capture:
- API URLs
- Request payloads (JSON)
- Response payloads (JSON)
- Response status codes
- Test outcomes

The data is stored in a JSON file for later report generation.
"""
import json
import os
from pathlib import Path
from datetime import datetime
import pytest

# Storage for test details
_test_details = []


class ResponseCapture:
    """Wrapper to capture response details."""
    
    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code
        self.url = response.url
        self.headers = dict(response.headers)
        try:
            self.json_data = response.json()
        except:
            self.json_data = None
        self.text = response.text[:1000] if len(response.text) > 1000 else response.text
        self.elapsed = response.elapsed.total_seconds()


def pytest_configure(config):
    """Initialize the detailed logging system."""
    global _test_details
    _test_details = []


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Capture test execution details including outcomes."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        test_data = {
            "test_name": item.nodeid,
            "test_function": item.name,
            "test_file": str(item.fspath),
            "outcome": report.outcome,
            "duration": report.duration,
            "timestamp": datetime.now().isoformat(),
            "markers": [m.name for m in item.iter_markers()],
            "api_calls": []
        }
        
        # Try to extract API call details from test item
        if hasattr(item, 'api_calls'):
            test_data["api_calls"] = item.api_calls
        
        # Add failure info if test failed
        if report.failed:
            test_data["failure_message"] = str(report.longrepr)
        
        _test_details.append(test_data)


def pytest_sessionfinish(session, exitstatus):
    """Save captured details to JSON file after test session."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    output_file = reports_dir / "test_details.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "exit_status": exitstatus,
            "total_tests": len(_test_details),
            "tests": _test_details
        }, f, indent=2, default=str)
    
    print(f"\n✓ Detailed test data saved to: {output_file}")


# Monkey-patch requests.Session to capture API calls
import requests

_original_post = requests.Session.post
_original_get = requests.Session.get

def _tracked_post(self, url, **kwargs):
    """Wrapper for Session.post to capture request/response details."""
    response = _original_post(self, url, **kwargs)
    
    # Capture the API call details
    api_call = {
        "method": "POST",
        "url": url,
        "request_payload": kwargs.get('json'),
        "request_data": kwargs.get('data'),
        "status_code": response.status_code,
        "elapsed_seconds": response.elapsed.total_seconds(),
    }
    
    try:
        api_call["response_payload"] = response.json()
    except:
        api_call["response_text"] = response.text[:500]
    
    # Store in thread-local or global context
    # This is a simplified approach; in production, use contextvars
    if not hasattr(self, '_captured_calls'):
        self._captured_calls = []
    self._captured_calls.append(api_call)
    
    return response

def _tracked_get(self, url, **kwargs):
    """Wrapper for Session.get to capture request/response details."""
    response = _original_get(self, url, **kwargs)
    
    api_call = {
        "method": "GET",
        "url": url,
        "request_params": kwargs.get('params'),
        "status_code": response.status_code,
        "elapsed_seconds": response.elapsed.total_seconds(),
    }
    
    try:
        api_call["response_payload"] = response.json()
    except:
        api_call["response_text"] = response.text[:500]
    
    if not hasattr(self, '_captured_calls'):
        self._captured_calls = []
    self._captured_calls.append(api_call)
    
    return response

# Apply monkey patches
requests.Session.post = _tracked_post
requests.Session.get = _tracked_get
