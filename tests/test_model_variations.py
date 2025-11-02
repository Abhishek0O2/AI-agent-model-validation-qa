import json
import pytest

# ---------- P0: accurate, safety-critical interpretations ----------

@pytest.mark.p0
def test_adverse_phrase_triggers_urgent(session, cfg):
    """Adverse wording should escalate with high confidence and clear warning."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-A1",
        "chief_complaint": "Crushing chest pain right now with sweating.",
        "age": 58, "sex": "male"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    body = r.json()
    assert body["class"] in ("urgent", "elevated_risk")  # mock returns "urgent"
    assert body["confidence"] >= 0.9
    warnings = " ".join(body.get("warnings", [])).lower()
    assert ("urgent" in warnings) or ("escalation" in warnings) or ("emergency" in warnings)

@pytest.mark.p0
def test_exertional_chest_symptoms_elevate_risk(session, cfg):
    """Nuanced exertional description → elevated_risk with solid confidence."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-A2",
        "chief_complaint": "Exertional chest discomfort for 2 weeks, worse on stairs.",
        "age": 62, "sex": "female"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    body = r.json()
    assert body["class"] in ("elevated_risk", "urgent")
    assert body["confidence"] >= 0.75
    # Explanations should point to relevant features
    feats = " ".join([str(e.get("feature", "")) for e in body.get("explanations", [])]).lower()
    assert ("chest" in feats) or ("exert" in feats)

@pytest.mark.p0
def test_out_of_distribution_domain_flagged(session, cfg):
    """Adult cardiology model given pediatric oncology hint → needs review with OOD warning."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-A3",
        "chief_complaint": "Neutropenia during induction chemo; ANC 200.",
        "age": 7, "sex": "male",
        "domain_hint": "pediatric_oncology"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    b = r.json()
    assert b["class"] == "needs_review"
    assert b["confidence"] <= 0.5
    warnings = " ".join(b.get("warnings", [])).lower()
    assert ("out-of-distribution" in warnings) or ("unsupported domain" in warnings) or ("needs review" in warnings)

# ---------- P1: nuanced language & robustness to text noise ----------

@pytest.mark.p1
def test_codeswitching_hinglish_understood(session, cfg):
    """Code-switching (Hinglish) + medical keywords still interpreted correctly."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-B1",
        "chief_complaint": "Kal se chest tightness ho raha, walking pe zyada.",
        "age": 45, "sex": "female", "language": "hi-en"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    b = r.json()
    assert b["class"] in ("elevated_risk", "needs_review")  # mock gives elevated_risk due to 'chest'
    assert 0.0 <= b["confidence"] <= 1.0

@pytest.mark.p1
@pytest.mark.parametrize("text", [
    "heart burn with chest burning on exertion",  # synonym + trigger "exertion"
    "shorness of breath while climbing; chest pressure",  # misspelling + trigger "chest"
    "CHEST discomfort… esp. on stairs!!! 😖",  # casing + punctuation + emoji
])
def test_synonyms_typos_noise_still_work(session, cfg, text):
    url = f"{cfg['base']}{cfg['path']}"
    payload = {"patient_id": "pt-B2", "chief_complaint": text, "age": 54, "sex": "male"}
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    b = r.json()
    assert b["class"] in ("elevated_risk", "urgent", "needs_review")
    assert "confidence" in b

@pytest.mark.p1
def test_long_narrative_does_not_crash(session, cfg):
    """Very long narrative should be accepted or gracefully handled."""
    url = f"{cfg['base']}{cfg['path']}"
    long_text = ("Some context " * 2000) + " chest heaviness on exertion " + ("more text " * 2000)
    payload = {"patient_id": "pt-B3", "chief_complaint": long_text, "age": 60, "sex": "male"}
    r = session.post(url, json=payload, timeout=max(10, cfg["timeout"]))
    assert r.status_code in (200, 413, 422)
    if r.status_code == 200:
        b = r.json()
        assert "class" in b and "confidence" in b

# ---------- P1: variations in data formats ----------

@pytest.mark.p1
def test_units_and_numeric_variations(session, cfg):
    """Units/number variants present alongside text; service should not choke."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-C1",
        "age": 50, "sex": "male",
        "vitals": {"bp_systolic": 120, "bp_diastolic": 80, "hr": 72, "spo2": 98, "temp_c": 37.0},
        "chief_complaint": "Chest discomfort on exertion. Weight 165 lb, temp 100.4 F reported.",  # text mentions imperial
        "onset_date": "2025-02-01"  # ISO date
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    b = r.json()
    assert b["class"] in ("elevated_risk", "urgent", "needs_review")

@pytest.mark.p1
@pytest.mark.parametrize("onset", ["01/02/2025", "2025/02/01", "Feb 1, 2025", "3 days ago"])
def test_date_format_variations(session, cfg, onset):
    """Different date expressions should not break inference; ambiguity may lower confidence."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-C2",
        "age": 61, "sex": "female",
        "chief_complaint": "Chest tightness with exertion",
        "onset_date": onset
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code in (200, 422)  # service may accept as string or validate
    if r.status_code == 200:
        assert "class" in r.json()

@pytest.mark.p1
@pytest.mark.parametrize("sex_value", ["female", "F", "f", "prefer not to say", "nonbinary", None])
def test_categorical_boolean_variants(session, cfg, sex_value):
    """Category fuzzing: different representations of sex/gender should not error."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {
        "patient_id": "pt-C3",
        "age": 52, "sex": sex_value,
        "chief_complaint": "Chest pain when walking fast"
    }
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    assert "class" in r.json()

# ---------- P1/P2: low-signal & validation clarity ----------

@pytest.mark.p1
def test_low_signal_prompts_review(session, cfg):
    """Vague/conflicting input -> low confidence + 'needs review' warning."""
    url = f"{cfg['base']}{cfg['path']}"
    payload = {"patient_id": "pt-D1", "age": 40, "sex": "male", "chief_complaint": "sometimes fine sometimes dizzy idk"}
    r = session.post(url, json=payload, timeout=cfg["timeout"])
    assert r.status_code == 200
    b = r.json()
    assert b["class"] == "needs_review"
    assert b["confidence"] <= 0.5
    warnings = " ".join(b.get("warnings", [])).lower()
    assert ("low confidence" in warnings) or ("needs review" in warnings)

@pytest.mark.p2
def test_invalid_type_rejected_with_422(session, cfg):
    """Bad types (e.g., age as string) should get a precise 422 from Pydantic/FastAPI."""
    url = f"{cfg['base']}{cfg['path']}"
    bad_payload = {
        "patient_id": "pt-D2",
        "age": "sixty two",  # invalid type
        "chief_complaint": "exertional chest pain"
    }
    r = session.post(url, data=json.dumps(bad_payload), headers={"Content-Type": "application/json"}, timeout=cfg["timeout"])
    assert r.status_code == 422
    # Error body should mention 'age'
    assert "age" in r.text.lower()

# ---------- P1: accuracy near decision signals ----------

@pytest.mark.p1
def test_confidence_gradient_stronger_phrase_gives_higher_confidence(session, cfg):
    """Sanity: 'crushing chest pain' should score higher than generic 'chest on exertion'."""
    url = f"{cfg['base']}{cfg['path']}"
    payload1 = {"patient_id": "pt-E1", "chief_complaint": "Crushing chest pain right now", "age": 60}
    payload2 = {"patient_id": "pt-E2", "chief_complaint": "Chest discomfort on exertion", "age": 60}

    r1 = session.post(url, json=payload1, timeout=cfg["timeout"])
    r2 = session.post(url, json=payload2, timeout=cfg["timeout"])
    assert r1.status_code == r2.status_code == 200
    b1, b2 = r1.json(), r2.json()
    assert b1["confidence"] >= b2["confidence"]
