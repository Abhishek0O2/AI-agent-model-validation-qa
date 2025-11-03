import pytest
import requests

# This test simulates a user error scenario for uploading a medical chart
# with an incorrect format and excessive page count, and checks the API/UI response.
# Assumes an endpoint /v1/upload_chart exists for file uploads.

API_URL = "http://127.0.0.1:8000/v1/upload_chart"

@pytest.mark.p2
def test_upload_medical_chart_incorrect_format():
    """
    Attempt to upload a medical chart with an unsupported file format (e.g., .txt instead of .pdf).
    Expect a clear error message and proper status code.
    """
    files = {"file": ("chart.txt", b"This is not a PDF.", "text/plain")}
    response = requests.post(API_URL, files=files)
    assert response.status_code in (400, 422), f"Expected 400/422, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Error message missing in response"
    assert "format" in data["error"].lower(), "Error should mention format"
    # Optionally check for UI-specific fields if returned

@pytest.mark.p2
def test_upload_medical_chart_too_many_pages():
    """
    Attempt to upload a medical chart with too many pages (simulate by metadata or mock).
    Expect a clear error message and proper status code.
    """
    # Simulate a PDF file with excessive pages (here, just metadata for demo)
    files = {"file": ("chart.pdf", b"%PDF-1.4... (mock content)", "application/pdf")}
    # Add a custom header or param to indicate page count for testing
    response = requests.post(API_URL, files=files, data={"page_count": 101})
    assert response.status_code in (400, 422), f"Expected 400/422, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Error message missing in response"
    assert "page" in data["error"].lower(), "Error should mention page count"
    # Optionally check for UI-specific fields if returned

# Note: For true UI automation, use Selenium or Playwright to interact with the frontend.
# This test assumes API-level validation and error messaging is exposed for UI to consume.
