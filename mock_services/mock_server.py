from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------- Schemas ----------
class Vitals(BaseModel):
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    hr: Optional[int] = None
    spo2: Optional[int] = None
    temp_c: Optional[float] = None

class InferenceRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = None
    vitals: Optional[Vitals] = None
    chief_complaint: Optional[str] = None
    onset_date: Optional[str] = None
    comorbidities: Optional[List[str]] = None
    meds: Optional[List[str]] = None
    language: Optional[str] = None
    domain_hint: Optional[str] = None

class Explanation(BaseModel):
    feature: str
    weight: Optional[float] = None

class InferenceResponse(BaseModel):
    class_: Optional[str] = Field(None, alias="class")
    confidence: float = Field(..., ge=0, le=1)
    explanations: List[Explanation] = []
    warnings: List[str] = []
    model_version: str = "mock-fastapi-1.0"
    # pydantic v2 configuration
    model_config = {
        "populate_by_name": True,
        "protected_namespaces": (),
    }

# ---------- App ----------
app = FastAPI(title="Mock Model API", version="1.0.0")

@app.post("/v1/model/infer", response_model=InferenceResponse)
def infer(req: InferenceRequest):
    text = (req.chief_complaint or "").lower()
    # Prefer domain-hint based routing early (out-of-distribution)
    if req.domain_hint and "pediatric" in (req.domain_hint or "").lower():
        return InferenceResponse(
            **{
                "class": "needs_review",
                "confidence": 0.4,
                "explanations": [{"feature": "domain_mismatch", "weight": 0.1}],
                "warnings": ["out-of-distribution: unsupported domain", "needs review"],
            }
        )

    if "crushing chest pain" in text:
        return InferenceResponse(
            **{
                "class": "urgent",
                "confidence": 0.95,
                "explanations": [{"feature": "crushing chest pain", "weight": 0.9}],
                "warnings": ["urgent escalation"],
            }
        )
    # Match broader exertion variants (exert, exertion, exertional) and chest keywords
    if "chest" in text or "exert" in text:
        return InferenceResponse(
            **{
                "class": "elevated_risk",
                "confidence": 0.82,
                "explanations": [{"feature": "chest", "weight": 0.6}],
                "warnings": [],
            }
        )

    # (domain hint already handled earlier)

    return InferenceResponse(
        **{
            "class": "needs_review",
            "confidence": 0.45,
            "explanations": [{"feature": "low_signal", "weight": 0.1}],
            "warnings": ["low confidence—needs review"],
        }
    )


@app.post("/v1/upload_chart")
async def upload_chart(
    file: UploadFile = File(...),
    page_count: int | None = Form(None),
):
    """Simple mock upload endpoint to support UI/API tests.

    - Only accepts PDF files (by extension).
    - Rejects files with page_count > 100.
    Returns JSON with an 'error' key on validation failures to match tests.
    """
    filename = (file.filename or "").lower().strip()

    if not filename.endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Unsupported file format: only PDF allowed"},
        )

    if page_count is not None and page_count > 100:
        return JSONResponse(
            status_code=422,
            content={"error": "Too many pages: maximum allowed is 100"},
        )

    return {"status": "ok", "filename": filename, "page_count": page_count}
