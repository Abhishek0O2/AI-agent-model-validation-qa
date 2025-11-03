import json
import pytest

# ---------- P0: accurate, safety-critical interpretations ----------
# These tests validate the model's ability to correctly identify and
# handle high-risk medical situations with appropriate urgency.

@pytest.mark.p0
def test_adverse_phrase_triggers_urgent(session, cfg):
    """Tests model's ability to identify and escalate severe symptoms.
    
    Steps:
    1. Submit a case with clear high-risk indicators (crushing chest pain + sweating)
    2. Verify appropriate urgent/elevated classification
    3. Check for high confidence score (>=0.9)
    4. Validate presence of urgency-related warnings
    
    This is a critical safety test ensuring the model properly identifies
    and escalates potential acute cardiac events requiring immediate attention.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-A1",
        "chief_complaint": "Crushing chest pain right now with sweating.",
        "age": 58, "sex": "male"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    body = r.json()
    
    # Verify urgent or elevated classification
    assert body["class"] in ("urgent", "elevated_risk"), \
        f"Expected 'urgent' or 'elevated_risk' for severe symptoms, got '{body['class']}'"
    
    # Verify high confidence
    assert body["confidence"] >= 0.9, \
        f"Expected confidence >= 0.9 for clear adverse symptoms, got {body['confidence']}"
    
    # Verify warnings exist and contain urgency indicators
    assert "warnings" in body, "Response missing 'warnings' field"
    warnings = " ".join(body.get("warnings", [])).lower()
    assert len(body.get("warnings", [])) > 0, "Expected at least one warning for adverse symptoms"
    assert any(keyword in warnings for keyword in ["urgent", "escalation", "emergency"]), \
        f"Expected urgency-related warnings, got: {body.get('warnings', [])}"
    
    # Verify explanations reference relevant symptoms
    assert "explanations" in body and len(body["explanations"]) > 0, \
        "Expected explanations for high-risk classification"

@pytest.mark.p0
def test_exertional_chest_symptoms_elevate_risk(session, cfg):
    """Tests model's detection of exertional cardiac symptoms.
    
    Steps:
    1. Submit case with typical angina presentation (exertional symptoms)
    2. Verify appropriate risk elevation classification
    3. Confirm confidence level meets threshold (>=0.75)
    4. Validate that explanations reference relevant clinical features
    
    This test ensures the model correctly identifies classic angina patterns
    and provides appropriate risk stratification for cardiac symptoms that
    worsen with physical activity.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-A2",
        "chief_complaint": "Exertional chest discomfort for 2 weeks, worse on stairs.",
        "age": 62, "sex": "female"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    body = r.json()
    
    # Verify appropriate risk classification
    assert body["class"] in ("elevated_risk", "urgent"), \
        f"Expected 'elevated_risk' or 'urgent' for exertional symptoms, got '{body['class']}'"
    
    # Verify confidence threshold
    assert body["confidence"] >= 0.75, \
        f"Expected confidence >= 0.75 for classic angina pattern, got {body['confidence']}"
    
    # Validate explanations exist and reference relevant features
    assert "explanations" in body and len(body["explanations"]) > 0, \
        "Explanations required for elevated risk classification"
    
    feats = " ".join([str(e.get("feature", "")) for e in body.get("explanations", [])]).lower()
    assert len(feats) > 0, "Explanation features should not be empty"
    assert ("chest" in feats) or ("exert" in feats) or ("stairs" in feats), \
        f"Expected explanations to reference chest/exertion symptoms, got features: {feats}"

@pytest.mark.p0
def test_out_of_distribution_domain_flagged(session, cfg):
    """Tests model's ability to recognize and flag out-of-scope cases.
    
    Steps:
    1. Submit pediatric oncology case to adult cardiology model
    2. Verify case is marked for review rather than misclassified
    3. Check confidence is appropriately low (<=0.5)
    4. Validate presence of out-of-distribution warnings
    
    This safety test ensures the model recognizes when cases fall outside
    its training domain and appropriately flags them for human review
    rather than making potentially unsafe predictions.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-A3",
        "chief_complaint": "Neutropenia during induction chemo; ANC 200.",
        "age": 7, "sex": "male",
        "domain_hint": "pediatric_oncology"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    b = r.json()
    
    # Verify needs_review classification for OOD
    assert b["class"] == "needs_review", \
        f"Expected 'needs_review' for out-of-distribution case, got '{b['class']}'"
    
    # Verify low confidence
    assert b["confidence"] <= 0.5, \
        f"Expected low confidence (<= 0.5) for OOD case, got {b['confidence']}"
    
    # Verify OOD warnings present
    assert "warnings" in b and len(b["warnings"]) > 0, \
        "Expected warnings for out-of-distribution detection"
    
    warnings = " ".join(b.get("warnings", [])).lower()
    assert any(keyword in warnings for keyword in ["out-of-distribution", "unsupported", "domain", "review"]), \
        f"Expected OOD-related warnings, got: {b.get('warnings', [])}"
    
    # Verify explanations indicate domain mismatch
    if "explanations" in b and len(b["explanations"]) > 0:
        expl_text = " ".join([str(e.get("feature", "")) for e in b["explanations"]]).lower()
        assert "domain" in expl_text or "mismatch" in expl_text, \
            "Expected explanations to mention domain mismatch"

# ---------- P1: nuanced language & robustness to text noise ----------

@pytest.mark.p1
def test_codeswitching_hinglish_understood(session, cfg):
    """Tests model's ability to handle multilingual input (Hinglish).
    
    Steps:
    1. Submit complaint in mixed Hindi-English (Hinglish)
    2. Verify model can extract meaning despite language mixing
    3. Check classification is appropriate for symptoms
    4. Validate confidence score is within valid range
    
    This test ensures the model can handle real-world language patterns
    where patients mix English medical terms with their primary language,
    ensuring accurate interpretation regardless of linguistic variation.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-B1",
        "chief_complaint": "Kal se chest tightness ho raha, walking pe zyada.",
        "age": 45, "sex": "female", "language": "hi-en"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    b = r.json()
    
    # Verify valid classification despite language mixing
    assert b["class"] in ("elevated_risk", "needs_review"), \
        f"Expected valid classification for Hinglish input, got '{b['class']}'"
    
    # Verify confidence is valid
    assert "confidence" in b, "Response missing 'confidence' field"
    assert 0.0 <= b["confidence"] <= 1.0, \
        f"confidence {b['confidence']} outside valid range [0,1]"
    
    # Verify essential response fields present
    assert "explanations" in b, "Response missing 'explanations' field"
    assert "warnings" in b, "Response missing 'warnings' field"

@pytest.mark.p1
@pytest.mark.parametrize("text", [
    "heart burn with chest burning on exertion",  # synonym + trigger "exertion"
    "shorness of breath while climbing; chest pressure",  # misspelling + trigger "chest"
    "CHEST discomfort… esp. on stairs!!! 😖",  # casing + punctuation + emoji
])
def test_synonyms_typos_noise_still_work(session, cfg, text):
    """Tests model's robustness to various text irregularities.
    
    Steps:
    1. Test multiple variants of symptom descriptions with:
       - Common synonyms for symptoms
       - Typical spelling mistakes
       - Various text formats (case, punctuation, emojis)
    2. Verify model successfully processes each variant
    3. Validate classifications remain clinically appropriate
    4. Confirm confidence scores are provided
    
    This test ensures the model is robust to common real-world variations
    in how symptoms might be described, including typos, informal language,
    and modern text elements like emojis.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {"patient_id": "pt-B2", "chief_complaint": text, "age": 54, "sex": "male"}
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200 for text variant, got {r.status_code}"
    
    b = r.json()
    
    # Verify valid classification despite text noise
    assert b["class"] in ("elevated_risk", "urgent", "needs_review"), \
        f"Expected valid classification for noisy text, got '{b['class']}'"
    
    # Verify confidence field exists and is valid
    assert "confidence" in b, "Response missing 'confidence' field"
    assert isinstance(b["confidence"], (int, float)), f"confidence should be numeric, got {type(b['confidence'])}"
    assert 0.0 <= b["confidence"] <= 1.0, f"confidence {b['confidence']} outside [0,1]"
    
    # Verify response structure intact
    assert "explanations" in b and isinstance(b["explanations"], list), \
        "Response should include explanations list"

@pytest.mark.p1
def test_long_narrative_does_not_crash(session, cfg):
    """Tests model's handling of extremely long input texts.
    
    Steps:
    1. Construct a very long narrative (>4000 words)
    2. Include relevant symptoms within the long text
    3. Submit request with extended timeout
    4. Verify either:
       - Successful processing (200)
       - Proper length limit rejection (413)
       - Valid format error (422)
    5. For successful responses, verify required fields
    
    This test ensures the model either properly processes or gracefully
    handles extremely verbose patient descriptions without crashing or
    timing out inappropriately.
    """
    url = f"{cfg['base']}{cfg['path']}"
    long_text = ("Some context " * 2000) + " chest heaviness on exertion " + ("more text " * 2000)
    payload = {"patient_id": "pt-B3", "chief_complaint": long_text, "age": 60, "sex": "male"}
    
    r = session.post(url, json=payload, timeout=max(10, cfg["timeout"]))
    
    # Verify graceful handling - either success, payload too large, or validation error
    assert r.status_code in (200, 413, 422), \
        f"Expected 200/413/422 for long input, got {r.status_code}"
    
    # If successful, verify response structure
    if r.status_code == 200:
        b = r.json()
        assert "class" in b, "Successful response missing 'class' field"
        assert "confidence" in b, "Successful response missing 'confidence' field"
        assert isinstance(b["confidence"], (int, float)), \
            f"confidence should be numeric, got {type(b['confidence'])}"
        assert 0.0 <= b["confidence"] <= 1.0, \
            f"confidence {b['confidence']} outside valid range"
    
    # If rejected, verify appropriate error
    elif r.status_code in (413, 422):
        # Ensure error response provides some feedback
        assert len(r.text) > 0, "Error response should include error message"

# ---------- P1: variations in data formats ----------
# These tests validate the model's ability to handle different
# data formats and variations in how information is presented.

@pytest.mark.p1
def test_units_and_numeric_variations(session, cfg):
    """Tests model's handling of mixed units and numeric formats.
    
    Steps:
    1. Create payload with multiple vital measurements
    2. Include both metric (vitals) and imperial (text) units
    3. Add standardized and free-text measurements
    4. Include ISO-formatted dates
    5. Verify successful processing
    6. Validate appropriate risk classification
    
    This test ensures the model can handle real-world complexity where
    measurements may be provided in different units and formats within
    the same request.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-C1",
        "age": 50, "sex": "male",
        "vitals": {"bp_systolic": 120, "bp_diastolic": 80, "hr": 72, "spo2": 98, "temp_c": 37.0},
        "chief_complaint": "Chest discomfort on exertion. Weight 165 lb, temp 100.4 F reported.",  # text mentions imperial
        "onset_date": "2025-02-01"  # ISO date
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    b = r.json()
    
    # Verify valid classification
    assert "class" in b, "Response missing 'class' field"
    assert b["class"] in ("elevated_risk", "urgent", "needs_review"), \
        f"Expected valid classification, got '{b['class']}'"
    
    # Verify confidence and basic structure
    assert "confidence" in b, "Response missing 'confidence' field"
    assert 0.0 <= b["confidence"] <= 1.0, f"confidence {b['confidence']} outside [0,1]"
    
    # Verify explanations present for medical decision
    assert "explanations" in b and isinstance(b["explanations"], list), \
        "Medical assessment should include explanations"

@pytest.mark.p1
@pytest.mark.parametrize("onset", ["01/02/2025", "2025/02/01", "Feb 1, 2025", "3 days ago"])
def test_date_format_variations(session, cfg, onset):
    """Tests model's handling of various date format inputs.
    
    Steps:
    1. Test multiple date format variations:
       - US format (MM/DD/YYYY)
       - ISO-like format (YYYY/MM/DD)
       - Natural language (Month D, YYYY)
       - Relative dates ("3 days ago")
    2. Verify model either:
       - Successfully processes the date (200)
       - Properly rejects invalid formats (422)
    3. For successful cases, confirm classification
    
    This test ensures the model can handle various ways users might
    express dates, while maintaining appropriate validation.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-C2",
        "age": 61, "sex": "female",
        "chief_complaint": "Chest tightness with exertion",
        "onset_date": onset
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    
    # Either accepts the format (200) or properly rejects it (422)
    assert r.status_code in (200, 422), \
        f"Expected 200 (accepted) or 422 (validation error), got {r.status_code}"
    
    # If successful, verify response structure
    if r.status_code == 200:
        response = r.json()
        assert "class" in response, "Successful response missing 'class' field"
        assert "confidence" in response, "Successful response missing 'confidence' field"
        assert response["class"] in ("elevated_risk", "urgent", "needs_review", None), \
            f"Invalid classification: {response['class']}"
    
    # If rejected, error should mention date/onset
    elif r.status_code == 422:
        error_text = r.text.lower()
        assert any(keyword in error_text for keyword in ["onset", "date", "validation"]), \
            "Validation error should mention problematic field"

@pytest.mark.p1
@pytest.mark.parametrize("sex_value", ["female", "F", "f", "prefer not to say", "nonbinary", None])
def test_categorical_boolean_variants(session, cfg, sex_value):
    """Tests model's handling of diverse gender/sex representations.
    
    Steps:
    1. Test various sex/gender inputs:
       - Standard values (female/male)
       - Abbreviations (F/M)
       - Case variations (f/m)
       - Non-binary options
       - Privacy preferences
       - Missing values (None)
    2. Verify successful processing
    3. Confirm valid classification returned
    
    This test ensures the model handles gender/sex data inclusively
    and gracefully, respecting diverse gender expressions while
    maintaining clinical functionality.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-C3",
        "age": 52, "sex": sex_value,
        "chief_complaint": "Chest pain when walking fast"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Model should accept various sex/gender values, got {r.status_code}"
    
    response = r.json()
    
    # Verify valid classification regardless of sex value
    assert "class" in response, "Response missing 'class' field"
    assert response["class"] in ("elevated_risk", "urgent", "needs_review", None), \
        f"Invalid classification: {response['class']}"
    
    # Verify confidence present and valid
    assert "confidence" in response, "Response missing 'confidence' field"
    assert 0.0 <= response["confidence"] <= 1.0, \
        f"confidence {response['confidence']} outside [0,1]"
    
    # Verify complete response structure
    assert "explanations" in response and isinstance(response["explanations"], list), \
        "Response should include explanations"

# ---------- P1/P2: low-signal & validation clarity ----------
# These tests verify the model's behavior with unclear or invalid inputs,
# ensuring appropriate handling and clear error messaging.

@pytest.mark.p1
def test_low_signal_prompts_review(session, cfg):
    """Tests model's handling of vague or ambiguous inputs.
    
    Steps:
    1. Submit case with vague, non-specific symptoms
    2. Verify appropriate 'needs review' classification
    3. Confirm low confidence score (<=0.5)
    4. Validate presence of appropriate warning flags
    
    This test ensures the model appropriately identifies cases where
    the input information is too vague or conflicting for confident
    automated assessment.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload = {"patient_id": "pt-D1", "age": 40, "sex": "male", "chief_complaint": "sometimes fine sometimes dizzy idk"}
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    b = r.json()
    
    # Verify needs_review classification for low signal
    assert b["class"] == "needs_review", \
        f"Expected 'needs_review' for vague input, got '{b['class']}'"
    
    # Verify low confidence
    assert "confidence" in b, "Response missing 'confidence' field"
    assert b["confidence"] <= 0.5, \
        f"Expected low confidence (<= 0.5) for ambiguous input, got {b['confidence']}"
    
    # Verify appropriate warnings
    assert "warnings" in b and len(b["warnings"]) > 0, \
        "Expected warnings for low-signal input"
    
    warnings = " ".join(b.get("warnings", [])).lower()
    assert any(keyword in warnings for keyword in ["low confidence", "review", "insufficient"]), \
        f"Expected low-confidence warnings, got: {b.get('warnings', [])}"

@pytest.mark.p2
def test_invalid_type_rejected_with_422(session, cfg):
    """Tests proper validation errors for incorrect data types.
    
    Steps:
    1. Create payload with invalid data type (string for age)
    2. Submit request with explicit JSON content type
    3. Verify 422 Unprocessable Entity response
    4. Confirm error message identifies problematic field
    
    This test ensures the API provides clear, actionable error
    messages when clients submit data with incorrect types,
    facilitating easier debugging and integration.
    """
    url = f"{cfg['base']}{cfg['path']}"
    bad_payload = {
        "patient_id": "pt-D2",
        "age": "sixty two",  # invalid type
        "chief_complaint": "exertional chest pain"
    }
    r = session.post(url, data=json.dumps(bad_payload), headers={"Content-Type": "application/json"}, timeout=cfg["timeout"])
    
    # Verify 422 validation error
    assert r.status_code == 422, f"Expected 422 for invalid type, got {r.status_code}"
    
    # Verify error body mentions the problematic field
    error_text = r.text.lower()
    assert "age" in error_text, f"Error should mention 'age' field, got: {r.text[:200]}"
    
    # Verify error indicates type problem
    assert any(keyword in error_text for keyword in ["type", "validation", "invalid", "int", "integer"]), \
        f"Error should indicate type validation issue, got: {r.text[:200]}"
    
    # Ensure error response is properly formatted (JSON or meaningful text)
    assert len(r.text) > 0, "Error response should not be empty"

# ---------- P1: accuracy near decision signals ----------
# These tests verify that the model's confidence scores appropriately
# reflect the strength and clarity of clinical indicators.

@pytest.mark.p1
def test_confidence_gradient_stronger_phrase_gives_higher_confidence(session, cfg):
    """Tests model's confidence scaling with symptom severity.
    
    Steps:
    1. Submit two cases:
       - High severity: "crushing chest pain"
       - Lower severity: "chest discomfort on exertion"
    2. Use same age to control for demographics
    3. Compare confidence scores between cases
    4. Verify stronger symptoms yield higher confidence
    
    This test ensures the model's confidence scoring properly
    reflects the clinical significance and urgency of different
    symptom presentations.
    """
    url = f"{cfg['base']}{cfg['path']}"
    payload1 = {"patient_id": "pt-E1", "chief_complaint": "Crushing chest pain right now", "age": 60}
    payload2 = {"patient_id": "pt-E2", "chief_complaint": "Chest discomfort on exertion", "age": 60}

    r1 = session.post(url, json=payload1, timeout=cfg["timeout"])
    r2 = session.post(url, json=payload2, timeout=cfg["timeout"])
    
    # Verify both requests successful
    assert r1.status_code == r2.status_code == 200, \
        f"Expected both requests to succeed, got {r1.status_code}, {r2.status_code}"
    
    b1, b2 = r1.json(), r2.json()
    
    # Verify both have confidence scores
    assert "confidence" in b1, "First response missing 'confidence' field"
    assert "confidence" in b2, "Second response missing 'confidence' field"
    
    # Verify confidence gradient: stronger symptoms -> higher confidence
    assert b1["confidence"] >= b2["confidence"], \
        f"Crushing chest pain (conf={b1['confidence']}) should have >= confidence than chest discomfort (conf={b2['confidence']})"
    
    # Optionally verify more urgent classification for stronger symptoms
    if b1["class"] == "urgent" and b2["class"] != "urgent":
        # This is expected but not strictly required for this test
        pass
