import pytest
import requests

from utils import assert_min_response

@pytest.mark.p0
def test_tc_m01_happy_path_schema(session, cfg):
    """
    TC-M01: Happy path — baseline correctness & schema presence

    """
    url=f"{cfg['base']}{cfg['path']}"
    payload={
        "patient_id": "pt-1001",
        "age": 62,
        "sex": "F",
        "vitals": {
            "bp_systolic": 128,
            "bp_diastolic": 82,
            "hr": 78,
            "spo2": 97,
            "temp_c": 36.9,
        },
        "onset_date": "2025-10-15",
        "comorbidities": ["hypertension"],
        "meds": ["atorvastatin"],
        "language": "en",
    }

    try:
        r = session.post(url, json=payload, timeout=cfg["timeout"])
        assert r.status_code == 200, f"Expected status code 200, got {r.status_code}"
    except requests.exceptions.ConnectionError as e:
        pytest.fail(
            f"Could not connect to model server at {url}. "
            "Is the mock server running? Start it with: "
            "python -m uvicorn mock_server:app --app-dir mock_services --host 0.0.0.0 --port 8000\n"
            f"Error: {str(e)}"
        )
    body=r.json()
    # Schema checks
    assert_min_response(body)