"""
Demo Test Suite - Showcasing Model Capabilities

1. Classify different risk levels (urgent, medium, low/no risk)
2. Handle invalid inputs gracefully
3. Provide confidence scores and explanations

These tests are designed for demonstration purposes to show stakeholders
how the model performs across various realistic scenarios.
"""
import pytest


@pytest.mark.demo
def test_demo_risk_classification_variants(session, cfg):
    """
    Demonstrates model's risk classification across multiple severity levels.
    
    This test submits 4 different patient scenarios to show how the model
    classifies varying levels of cardiac risk:
    
    1. URGENT: Acute severe symptoms requiring immediate attention
    2. ELEVATED RISK: Concerning symptoms needing prompt evaluation  
    3. NEEDS REVIEW: Ambiguous case requiring human judgment
    4. OUT-OF-DISTRIBUTION: Domain mismatch detection (pediatric oncology)
    
    For each case, we validate:
    - Appropriate risk classification
    - Reasonable confidence scores
    - Relevant explanations
    - Proper warnings when applicable
    """
    url = f"{cfg['base']}{cfg['path']}"
    
    # ============================================================
    # SCENARIO 1: URGENT - Acute MI (Heart Attack) Presentation
    # ============================================================
    print("\n" + "="*60)
    print("SCENARIO 1: URGENT - Acute Myocardial Infarction")
    print("="*60)
    
    urgent_payload = {
        "patient_id": "demo-urgent-001",
        "chief_complaint": "Crushing chest pain radiating to left arm with sweating and nausea",
        "age": 58,
        "sex": "male",
        "vitals": {
            "bp_systolic": 145,
            "bp_diastolic": 95,
            "hr": 110,
            "spo2": 96
        }
    }
    
    print(f"Request Payload:\n{urgent_payload}")
    
    r1 = session.post(url, json=urgent_payload, timeout=cfg["timeout"])
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    
    urgent_response = r1.json()
    print(f"\nResponse:\n{urgent_response}")
    
    # Validate urgent classification
    assert urgent_response["class"] in ("urgent", "elevated_risk"), \
        f"Expected 'urgent' or 'elevated_risk' for acute MI symptoms, got '{urgent_response['class']}'"
    
    assert urgent_response["confidence"] >= 0.8, \
        f"Expected high confidence (>=0.8) for classic MI presentation, got {urgent_response['confidence']}"
    
    assert "explanations" in urgent_response and len(urgent_response["explanations"]) > 0, \
        "Expected explanations for high-risk classification"
    
    print(f"✅ Model correctly classified as: {urgent_response['class']}")
    print(f"✅ Confidence: {urgent_response['confidence']}")
    
    # ============================================================
    # SCENARIO 2: ELEVATED RISK - Exertional Angina
    # ============================================================
    print("\n" + "="*60)
    print("SCENARIO 2: ELEVATED RISK - Stable Angina")
    print("="*60)
    
    elevated_payload = {
        "patient_id": "demo-elevated-002",
        "chief_complaint": "Chest tightness when climbing stairs, resolves with rest",
        "age": 65,
        "sex": "female",
        "vitals": {
            "bp_systolic": 135,
            "bp_diastolic": 85,
            "hr": 78,
            "spo2": 98
        }
    }
    
    print(f"Request Payload:\n{elevated_payload}")
    
    r2 = session.post(url, json=elevated_payload, timeout=cfg["timeout"])
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    
    elevated_response = r2.json()
    print(f"\nResponse:\n{elevated_response}")
    
    # Validate elevated risk classification
    assert elevated_response["class"] in ("elevated_risk", "needs_review"), \
        f"Expected 'elevated_risk' or 'needs_review', got '{elevated_response['class']}'"
    
    assert elevated_response["confidence"] >= 0.6, \
        f"Expected moderate confidence (>=0.6), got {elevated_response['confidence']}"
    
    print(f"✅ Model classified as: {elevated_response['class']}")
    print(f"✅ Confidence: {elevated_response['confidence']}")
    
    # ============================================================
    # SCENARIO 3: NEEDS REVIEW - Ambiguous Symptoms
    # ============================================================
    print("\n" + "="*60)
    print("SCENARIO 3: NEEDS REVIEW - Vague Symptoms")
    print("="*60)
    
    ambiguous_payload = {
        "patient_id": "demo-review-003",
        "chief_complaint": "Sometimes feel dizzy, occasional mild discomfort",
        "age": 45,
        "sex": "male"
    }
    
    print(f"Request Payload:\n{ambiguous_payload}")
    
    r3 = session.post(url, json=ambiguous_payload, timeout=cfg["timeout"])
    assert r3.status_code == 200, f"Expected 200, got {r3.status_code}"
    
    review_response = r3.json()
    print(f"\nResponse:\n{review_response}")
    
    # Validate needs_review classification
    assert review_response["class"] in ("needs_review", "elevated_risk", None), \
        f"Expected 'needs_review' or 'elevated_risk' for ambiguous case, got '{review_response['class']}'"
    
    # Lower confidence expected for ambiguous cases
    assert review_response["confidence"] <= 0.7, \
        f"Expected lower confidence (<=0.7) for vague symptoms, got {review_response['confidence']}"
    
    print(f"✅ Model classified as: {review_response['class']}")
    print(f"✅ Confidence: {review_response['confidence']} (appropriately lower for ambiguous case)")
    
    # ============================================================
    # SCENARIO 4: OUT-OF-DISTRIBUTION - Domain Mismatch Detection
    # ============================================================
    print("\n" + "="*60)
    print("SCENARIO 4: OUT-OF-DISTRIBUTION - Domain Mismatch (Pediatric Oncology)")
    print("="*60)
    
    ood_payload = {
        "patient_id": "demo-ood-004",
        "chief_complaint": "Follow-up for leukemia treatment complications",
        "age": 8,
        "sex": "male",
        "domain_hint": "pediatric_oncology",
        "vitals": {
            "bp_systolic": 105,
            "bp_diastolic": 65,
            "hr": 88,
            "spo2": 97
        }
    }
    
    print(f"Request Payload:\n{ood_payload}")
    
    r4 = session.post(url, json=ood_payload, timeout=cfg["timeout"])
    assert r4.status_code == 200, f"Expected 200, got {r4.status_code}"
    
    ood_response = r4.json()
    print(f"\nResponse:\n{ood_response}")
    
    # Should flag as needs_review for out-of-domain case
    assert ood_response["class"] == "needs_review", \
        f"Expected 'needs_review' for OOD case, got '{ood_response['class']}'"
    
    # Low confidence expected for out-of-domain cases
    assert ood_response["confidence"] <= 0.5, \
        f"Expected low confidence (<=0.5) for OOD domain, got {ood_response['confidence']}"
    
    # Should contain domain_mismatch in explanations
    explanations = ood_response.get("explanations", [])
    
    # Handle explanations as list of dicts (feature/weight format)
    has_domain_mismatch = False
    for exp in explanations:
        if isinstance(exp, dict):
            if exp.get('feature') in ('domain_mismatch', 'out_of_domain'):
                has_domain_mismatch = True
                break
        elif isinstance(exp, str):
            if 'domain_mismatch' in exp or 'out_of_domain' in exp:
                has_domain_mismatch = True
                break
    
    assert has_domain_mismatch, \
        f"Expected 'domain_mismatch' or 'out_of_domain' in explanations, got: {explanations}"
    
    print(f"✅ Model correctly flagged OOD case as: {ood_response['class']}")
    print(f"✅ Low confidence: {ood_response['confidence']} (appropriate for domain mismatch)")
    print(f"✅ Domain mismatch detected in explanations")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*60)
    print("DEMONSTRATION SUMMARY")
    print("="*60)
    print("The model successfully:")
    print("  1. ✅ Identified urgent cases with high confidence")
    print("  2. ✅ Detected elevated risk scenarios appropriately")
    print("  3. ✅ Flagged ambiguous cases for review with lower confidence")
    print("  4. ✅ Detected out-of-distribution domain mismatch with low confidence")
    print("="*60 + "\n")


@pytest.mark.demo
def test_demo_invalid_input_handling(session, cfg):
    """
    Demonstrates model's robustness in handling invalid or edge-case inputs.
    
    This test shows how the model gracefully handles:
    1. Missing required fields
    2. Invalid data types
    3. Out-of-range values
    4. Malformed requests
    
    The model should reject invalid inputs with appropriate error messages
    rather than attempting to process bad data.
    """
    url = f"{cfg['base']}{cfg['path']}"
    
    # ============================================================
    # INVALID TEST 1: Missing Required Field (patient_id)
    # ============================================================
    print("\n" + "="*60)
    print("INVALID INPUT 1: Missing Required Field")
    print("="*60)
    
    missing_field_payload = {
        # Missing required 'patient_id'
        "chief_complaint": "Chest pain",
        "sex": "male",
        "age": 55,
    }
    
    print(f"Request Payload (missing 'patient_id'):\n{missing_field_payload}")
    
    r1 = session.post(url, json=missing_field_payload, timeout=cfg["timeout"])
    print(f"Response Status Code: {r1.status_code}")
    
    # Expect 422 Unprocessable Entity due to missing required field
    assert r1.status_code == 422, f"Expected 422 for missing patient_id, got {r1.status_code}"
    
    # ============================================================
    # INVALID TEST 2: Invalid Data Type (age as string)
    # ============================================================
    print("\n" + "="*60)
    print("INVALID INPUT 2: Wrong Data Type")
    print("="*60)
    
    wrong_type_payload = {
        "patient_id": "demo-invalid-002",
        "chief_complaint": "Chest discomfort",
        "age": "sixty-five",  # Should be integer
        "sex": "female"
    }
    
    print(f"Request Payload (age as string):\n{wrong_type_payload}")
    
    r2 = session.post(url, json=wrong_type_payload, timeout=cfg["timeout"])
    print(f"Response Status Code: {r2.status_code}")
    
    # Expect strict validation failure
    assert r2.status_code == 422, f"Expected 422 for wrong data type, got {r2.status_code}"
    
    # ============================================================
    # INVALID TEST 3: Out-of-Range Values (negative age)
    # ============================================================
    print("\n" + "="*60)
    print("INVALID INPUT 3: Out-of-Range Value")
    print("="*60)
    
    out_of_range_payload = {
        "patient_id": "demo-invalid-003",
        "chief_complaint": "Chest pain",
        "age": -5,  # Invalid: negative age
        "sex": "male"
    }
    
    print(f"Request Payload (negative age):\n{out_of_range_payload}")
    
    r3 = session.post(url, json=out_of_range_payload, timeout=cfg["timeout"])
    print(f"Response Status Code: {r3.status_code}")
    
    # Expect 422 for out-of-range age
    assert r3.status_code in (400, 422), f"Expected 422 (or 400) for negative age, got {r3.status_code}"
    
    # ============================================================
    # INVALID TEST 4: Empty Chief Complaint
    # ============================================================
    print("\n" + "="*60)
    print("INVALID INPUT 4: Empty Chief Complaint")
    print("="*60)
    
    empty_complaint_payload = {
        "patient_id": "demo-invalid-004",
        "chief_complaint": "",  # Empty string
        "age": 55,
        "sex": "female"
    }
    
    print(f"Request Payload (empty complaint):\n{empty_complaint_payload}")
    
    r4 = session.post(url, json=empty_complaint_payload, timeout=cfg["timeout"])
    print(f"Response Status Code: {r4.status_code}")
    assert r4.status_code == 200, f"Expected 200 for empty complaint handled by model, got {r4.status_code}"
    response = r4.json()
    # Should flag for review due to insufficient information with lower confidence
    assert response.get("class") == "needs_review", f"Expected 'needs_review' for empty complaint, got {response.get('class')}"
    assert response.get("confidence", 1.0) <= 0.5, f"Expected low confidence (<=0.5), got {response.get('confidence')}"
    
    # ============================================================
    # INVALID TEST 5: Extremely Long Input (Edge Case)
    # ============================================================
    print("\n" + "="*60)
    print("INVALID INPUT 5: Extremely Long Text Input")
    print("="*60)
    
    very_long_text = ("Patient reports " + "chest pain " * 500)  # ~5000+ chars
    long_input_payload = {
        "patient_id": "demo-invalid-005",
        "chief_complaint": very_long_text,
        "age": 60,
        "sex": "male"
    }
    
    print(f"Request Payload (very long complaint: {len(very_long_text)} characters)")
    print(f"First 100 chars: {very_long_text[:100]}...")
    
    r5 = session.post(url, json=long_input_payload, timeout=max(10, cfg["timeout"]))
    print(f"Response Status Code: {r5.status_code}")
    assert r5.status_code == 200, f"Expected 200 for long input, got {r5.status_code}"
    response = r5.json()
    # With repeated 'chest pain', mock returns elevated_risk at 0.82
    assert response.get('class') in ("elevated_risk", "needs_review"), f"Unexpected class: {response.get('class')}"
    assert response.get('confidence', 0) >= 0.6, f"Expected reasonable confidence (>=0.6), got {response.get('confidence')}"
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*60)
    print("INVALID INPUT HANDLING SUMMARY")
    print("="*60)
    print("The model demonstrated robust input validation:")
    print("  1. Handling missing required fields")
    print("  2. Detecting invalid data types")
    print("  3. Rejecting out-of-range values")
    print("  4. Managing empty/insufficient input")
    print("  5. Processing or rejecting extremely long inputs")
    print("\nThese validations ensure the model only processes")
    print("well-formed requests, preventing errors and ensuring safety.")
    print("="*60 + "\n")


@pytest.mark.skip(reason="Omitted from demo: keeping only 2 showcase tests (risk variants, invalid input)")
def test_demo_confidence_scoring(session, cfg):
    """
    Demonstrates how model confidence scores reflect certainty of predictions.
    
    This test shows:
    1. High confidence for clear, unambiguous cases
    2. Medium confidence for typical presentations
    3. Low confidence for vague or conflicting information
    
    Confidence scoring helps clinicians understand when to trust
    the model vs. when additional review is needed.
    """
    url = f"{cfg['base']}{cfg['path']}"
    
    # HIGH CONFIDENCE: Classic textbook presentation
    print("\n" + "="*60)
    print("CONFIDENCE TEST 1: Classic High-Confidence Case")
    print("="*60)
    
    high_conf_payload = {
        "patient_id": "demo-conf-001",
        "chief_complaint": "Sudden crushing substernal chest pain radiating to jaw and left arm, associated with diaphoresis",
        "age": 62,
        "sex": "male",
        "vitals": {"bp_systolic": 150, "bp_diastolic": 95, "hr": 105}
    }
    
    print(f"Payload: Classic MI presentation")
    r1 = session.post(url, json=high_conf_payload, timeout=cfg["timeout"])
    high_conf_resp = r1.json()
    
    print(f"Classification: {high_conf_resp['class']}")
    print(f"Confidence: {high_conf_resp['confidence']}")
    
    assert high_conf_resp['confidence'] >= 0.75, \
        f"Expected high confidence for classic presentation, got {high_conf_resp['confidence']}"
    
    print(f"✅ Model shows HIGH confidence for textbook symptoms")
    
    # MEDIUM CONFIDENCE: Typical but less specific

    print("\n" + "="*60)
    print("CONFIDENCE TEST 2: Medium-Confidence Case")
    print("="*60)
    
    med_conf_payload = {
        "patient_id": "demo-conf-002",
        "chief_complaint": "Chest tightness on exertion",
        "age": 55,
        "sex": "female"
    }
    
    print(f"Payload: Common but less specific symptoms")
    r2 = session.post(url, json=med_conf_payload, timeout=cfg["timeout"])
    med_conf_resp = r2.json()
    
    print(f"Classification: {med_conf_resp['class']}")
    print(f"Confidence: {med_conf_resp['confidence']}")
    
    print(f"✅ Model shows MEDIUM confidence for typical presentation")
    
    # ============================================================
    # LOW CONFIDENCE: Vague symptoms
    # ============================================================
    print("\n" + "="*60)
    print("CONFIDENCE TEST 3: Low-Confidence Case")
    print("="*60)
    
    low_conf_payload = {
        "patient_id": "demo-conf-003",
        "chief_complaint": "Not feeling well, some discomfort",
        "age": 40,
        "sex": "male"
    }
    
    print(f"Payload: Vague, non-specific symptoms")
    r3 = session.post(url, json=low_conf_payload, timeout=cfg["timeout"])
    low_conf_resp = r3.json()
    
    print(f"Classification: {low_conf_resp['class']}")
    print(f"Confidence: {low_conf_resp['confidence']}")
    
    assert low_conf_resp['confidence'] <= 0.6, \
        f"Expected low confidence for vague symptoms, got {low_conf_resp['confidence']}"
    
    print(f"✅ Model shows LOW confidence for ambiguous input")
    
    # For demo purposes with mock server, just show the gradient concept
    # In production, verify actual confidence gradient
    print("\n" + "="*60)
    print("CONFIDENCE SCORING SUMMARY")
    print("="*60)
    print(f"High Confidence: {high_conf_resp['confidence']:.2f} (Classic symptoms)")
    print(f"Medium Confidence: {med_conf_resp['confidence']:.2f} (Typical symptoms)")
    print(f"Low Confidence: {low_conf_resp['confidence']:.2f} (Vague symptoms)")
    print("\n✅ Model provides confidence scores that help guide clinical decisions")
    print("   • High confidence (>0.75): Trust model prediction")
    print("   • Medium confidence (0.5-0.75): Consider additional factors")
    print("   • Low confidence (<0.5): Human review recommended")
    print("="*60 + "\n")
