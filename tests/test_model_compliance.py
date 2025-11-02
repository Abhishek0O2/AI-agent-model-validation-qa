# tests/test_model_compliance.py
import json
import pytest

# Set of valid classification labels that the model is allowed to return
LABEL_WHITELIST = {"urgent", "elevated_risk", "needs_review", None}

# --- P0/P1: Compliance & contract --------------------------------------------

@pytest.mark.p0
def test_schema_minimum_and_model_version(session, cfg):
    """Validates that model response contains all required fields and follows schema constraints.
    
    Steps:
    1. Construct API endpoint URL from configuration
    2. Send POST request with a typical patient case (exertional chest pain)
    3. Verify HTTP 200 response code
    4. Check presence of all required fields (class, confidence, explanations, warnings)
    5. Validate data types (lists for explanations/warnings)
    6. Verify confidence is in valid range [0,1]
    7. Confirm model version is present and non-empty
    """
    # Build the API endpoint URL
    url = f"{cfg['base']}{cfg['path']}"
    
    # Prepare test payload with typical patient presentation
    payload = {"patient_id": "c-happy", "age": 62, "sex": "female",
               "chief_complaint": "Exertional chest discomfort for 2 weeks, worse on stairs."}
    
    # Make API request with timeout
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    
    # Parse and validate response
    b = r.json()
    assert "class" in b and "confidence" in b and "explanations" in b and "warnings" in b
    assert isinstance(b["explanations"], list) and isinstance(b["warnings"], list)
    assert 0.0 <= b["confidence"] <= 1.0
    assert "model_version" in b and b["model_version"]

@pytest.mark.p1
def test_no_phi_echo_name_phone(session, cfg):
    """Ensures that names and phone numbers in input are not echoed in the response payload.

    Steps:
    1. Construct API endpoint URL from configuration
    2. Create a test complaint containing a name and phone number
    3. Submit request with the PHI-containing complaint
    4. Verify HTTP 200 success response
    5. Convert full response to JSON string
    6. Assert that neither the name nor phone number appears anywhere in the response

    This test reduces PHI leakage risk by ensuring sensitive identifiers are not reflected in outputs.
    """
    
    # Build API endpoint URL
    url = f"{cfg['base']}{cfg['path']}"
    
    # Prepare complaint with name and phone number
    name = "Anita Rao"
    phone = "9876543210"
    complaint = f"I, {name}, {phone}, am experiencing chest pain."
    payload = {"patient_id": "c-phi", "age": 47, "sex": "female", "chief_complaint": complaint}
    
    # Make API request
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    
    # Check response doesn't contain name or phone number
    dump = json.dumps(r.json(), ensure_ascii=False).lower()
    assert name.lower().split()[0] not in dump  # first name
    assert name.lower().split()[1] not in dump  # last name
    assert phone not in dump  # phone digits


@pytest.mark.p0
def test_label_whitelist(session, cfg):
    """Verifies that model only returns approved classification labels.
    
    Steps:
    1. Construct API endpoint URL from configuration
    2. Submit a test case with chest pain symptoms
    3. Verify successful HTTP 200 response
    4. Extract classification label from response
    5. Validate label is in the approved whitelist
    
    This is a critical safety check to ensure model outputs
    remain within the approved decision space.
    """
    # Build API endpoint URL
    url = f"{cfg['base']}{cfg['path']}"
    
    # Prepare test case with cardiac symptoms
    payload = {"patient_id": "c-label", "age": 50, "sex": "male",
               "chief_complaint": "Chest tightness on exertion"}
    
    # Make API request
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    
    # Verify classification is allowed
    cls = r.json()["class"]
    assert cls in LABEL_WHITELIST

@pytest.mark.p1
def test_explanations_must_be_present_on_200(session, cfg):
    """Validates that model provides explanations for its decisions.
    
    Steps:
    1. Construct API endpoint URL from configuration
    2. Submit a test case with cardiac symptoms
    3. Verify HTTP 200 success response
    4. Extract explanations from response
    5. Validate explanations exist and are properly structured
    6. Check that at least one feature-based explanation is provided
    
    This test ensures transparency and interpretability of model decisions,
    which is crucial for clinical decision support.
    """
    # Build API endpoint URL
    url = f"{cfg['base']}{cfg['path']}"
    
    # Prepare test case requiring explanation
    payload = {"patient_id": "c-xpl", "age": 61, "sex": "female",
               "chief_complaint": "Exertional chest pressure climbing stairs"}
    
    # Make API request
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    
    # Validate explanations
    expl = r.json().get("explanations", [])
    assert isinstance(expl, list) and len(expl) > 0
    assert "feature" in expl[0]  # minimal relevance check

@pytest.mark.p1
def test_input_validation_bad_type_422(session, cfg):
    """Verifies proper error handling for invalid input types.
    
    Steps:
    1. Construct API endpoint URL from configuration
    2. Prepare payload with incorrect data type (string for age)
    3. Submit request with explicit content-type header
    4. Verify HTTP 422 Unprocessable Entity response
    5. Check error message mentions the specific invalid field
    
    This test ensures the API properly validates inputs and provides
    clear error messages to help clients fix their requests.
    """
    # Build API endpoint URL
    url = f"{cfg['base']}{cfg['path']}"
    
    # Prepare payload with invalid age type
    bad = {"patient_id": "c-422", "age": "sixty two", "chief_complaint": "exertional chest pain"}
    
    # Make API request with explicit JSON content type
    r = session.post(url, data=json.dumps(bad), headers={"Content-Type": "application/json"}, timeout=cfg["timeout"])
    
    # Verify proper error response
    assert r.status_code == 422
    assert "age" in r.text.lower()  # should mention the problematic field

@pytest.mark.p1
def test_response_does_not_echo_full_input_text(session, cfg):
    """Tests prevention of PHI leakage in model responses.
    
    Steps:
    1. Construct API endpoint URL from configuration
    2. Create a test complaint with non-English text to ensure UTF-8 handling
    3. Submit request with the test complaint
    4. Verify HTTP 200 success response
    5. Convert full response to JSON string with UTF-8 support
    6. Verify original complaint text is not present in response
    
    This test is crucial for PHI (Protected Health Information) protection,
    ensuring the model doesn't accidentally expose sensitive patient information
    by echoing back the full input text in its response.
    """
    # Build API endpoint URL
    url = f"{cfg['base']}{cfg['path']}"
    
    # Prepare multilingual test complaint
    complaint = "Kal se chest tightness ho raha, walking pe zyada."
    payload = {"patient_id": "c-echo", "age": 45, "sex": "female", "chief_complaint": complaint}
    
    # Make API request
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    
    # Check response doesn't contain raw complaint text
    dump = json.dumps(r.json(), ensure_ascii=False).lower()
    assert complaint.lower() not in dump  # response should not mirror raw complaint text