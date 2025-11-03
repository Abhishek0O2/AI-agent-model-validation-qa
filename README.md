# AI Agent Model Validation QA

A comprehensive QA automation suite for validating AI model APIs with focus on **safety-critical medical decision support systems**. This framework ensures model compliance, robustness, and PHI (Protected Health Information) protection through systematic testing.

## 🎯 Overview

This test suite validates a cardiac risk assessment model API across multiple dimensions:
- **Compliance & Contract Testing** - Schema validation, label whitelisting, explainability
- **Safety-Critical Scenarios** - Adverse symptoms, exertional patterns, out-of-distribution detection
- **Robustness Testing** - Multilingual input, text noise, format variations
- **PHI Protection** - Ensures no sensitive information leakage in responses
- **Edge Cases** - Invalid inputs, low-signal cases, confidence gradients

## 📋 Test Priority Levels

- **P0 (Critical)**: Safety-critical tests that must always pass
- **P1 (High)**: Important quality and robustness tests
- **P2 (Medium)**: Edge cases and validation clarity tests

## 🏗️ Project Structure

```
AI-agent-model-validation-qa/
├── tests/
│   ├── test_model_compliance.py      # P0/P1: Schema, PHI, compliance tests (6 tests)
│   ├── test_model_variations.py      # P0/P1/P2: Robustness & variations (22 tests)
│   └── test_model_integration.py     # Integration & happy path tests
├── mock_services/
│   └── mock_server.py                # FastAPI mock server for testing
├── scripts/
│   └── generate_regression_report.py # Generate detailed HTML test reports
├── conftest.py                        # Pytest fixtures & configuration
├── pytest.ini                         # Pytest settings & markers
├── requirements.txt                   # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Abhishek0O2/AI-agent-model-validation-qa.git
   cd AI-agent-model-validation-qa
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Running Tests

### Start Mock Server

The test suite includes an auto-starting mock server, but you can also start it manually:

```powershell
# Windows PowerShell
.venv\Scripts\python.exe -m uvicorn mock_server:app --app-dir mock_services --host 0.0.0.0 --port 8000

# Linux/Mac
python -m uvicorn mock_server:app --app-dir mock_services --host 0.0.0.0 --port 8000
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run with HTML report
pytest -v --html=reports/pytest_report.html --self-contained-html

# Run specific priority level
pytest -v -m p0  # Only critical tests
pytest -v -m p1  # Only high-priority tests
```

### Run Specific Test Files

```bash
# Compliance tests only
pytest tests/test_model_compliance.py -v

# Variation tests only
pytest tests/test_model_variations.py -v

# Integration tests only
pytest tests/test_model_integration.py -v
```

## 📊 Test Coverage

### Compliance Tests (`test_model_compliance.py`) - 6 tests

| Test | Priority | Description |
|------|----------|-------------|
| `test_schema_minimum_and_model_version` | P0 | Validates required response fields and schema |
| `test_label_whitelist` | P0 | Ensures only approved classification labels |
| `test_no_phi_echo_name_phone` | P1 | Prevents PHI (names/phone) in responses |
| `test_explanations_must_be_present_on_200` | P1 | Requires model explanations for transparency |
| `test_input_validation_bad_type_422` | P1 | Validates proper error handling (422) |
| `test_response_does_not_echo_full_input_text` | P1 | Prevents echoing sensitive complaint text |

### Variation Tests (`test_model_variations.py`) - 22 tests

| Category | Tests | Description |
|----------|-------|-------------|
| **Safety-Critical** | 3 | Adverse phrases, exertional symptoms, OOD detection |
| **Language Robustness** | 4 | Hinglish, typos, synonyms, emojis, casing |
| **Data Format Variations** | 9 | Dates, units, gender/sex, numeric formats |
| **Low-Signal & Validation** | 2 | Vague inputs, invalid types |
| **Confidence Scoring** | 1 | Symptom severity gradient |
| **Edge Cases** | 3 | Long narratives, missing fields |

## 🔧 Configuration

### Environment Variables

```bash
# Model API Configuration
MODEL_URL=http://localhost:8000              # Base URL for model API
MODEL_INFER_PATH=/v1/model/infer            # Inference endpoint path
REQUEST_TIMEOUT_S=10                         # Request timeout in seconds
CONFIDENCE_FLOOR=0.7                         # Minimum confidence threshold
USE_MOCK=1                                   # Use mock server (1=yes, 0=no)
```

### Pytest Markers

Defined in `pytest.ini`:
- `p0`: Safety-critical tests
- `p1`: High priority quality tests
- `p2`: Robustness/edge tests

## 📈 Continuous Integration

Tests run automatically on GitHub Actions:
- ✅ On every push to `main`
- ✅ On pull requests
- ✅ Generates HTML test reports as artifacts

### View CI Results

1. Go to **Actions** tab in GitHub repository
2. Select the latest workflow run
3. Download test reports from **Artifacts**

## 🛡️ Key Validation Areas

### 1. **Schema Compliance**
- Required fields: `class`, `confidence`, `explanations`, `warnings`, `model_version`
- Confidence must be in range [0, 1]
- Proper data types for all fields

### 2. **PHI Protection**
- No echoing of patient names
- No reflection of phone numbers
- No verbatim complaint text in responses

### 3. **Label Whitelisting**
Approved classification labels:
- `urgent` - Immediate escalation needed
- `elevated_risk` - Higher risk, requires attention
- `needs_review` - Insufficient confidence/data
- `null` - No classification

### 4. **Explainability**
- All successful responses must include explanations
- Explanations must reference clinical features
- Feature weights should be present

### 5. **Out-of-Distribution Detection**
- Pediatric cases flagged when sent to adult model
- Low confidence scores for OOD cases
- Clear warnings about unsupported domains

## 📝 Test Data Examples

### Valid Request
```json
{
  "patient_id": "pt-1001",
  "age": 62,
  "sex": "female",
  "chief_complaint": "Exertional chest discomfort for 2 weeks, worse on stairs",
  "vitals": {
    "bp_systolic": 128,
    "bp_diastolic": 82,
    "hr": 78
  }
}
```

### Expected Response
```json
{
  "class": "elevated_risk",
  "confidence": 0.82,
  "explanations": [
    {"feature": "chest", "weight": 0.6}
  ],
  "warnings": [],
  "model_version": "mock-fastapi-1.0"
}
```

## 🐛 Troubleshooting

### Tests fail with connection error
**Problem**: `ConnectionError: Could not connect to model server`

**Solution**:
```bash
# Ensure mock server is running
python -m uvicorn mock_server:app --app-dir mock_services --host 0.0.0.0 --port 8000
```

### ImportError: No module named 'fastapi'
**Problem**: Missing dependencies

**Solution**:
```bash
pip install -r requirements.txt
```

### Port 8000 already in use
**Problem**: Another process using port 8000

**Solution**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JSON Schema Validation](https://json-schema.org/)

## 🐳 Docker Setup (Optional)

For a fully containerized testing environment, Docker Compose is available as an alternative to the native Python setup.

### Prerequisites
- Docker Desktop or Docker Engine
- Docker Compose

### Quick Start with Docker

```bash
# Build the Docker images
docker-compose build

# Run all tests
docker-compose up tests

# Run tests with HTML reports
docker-compose run --rm tests pytest -v --html=reports/pytest_report.html --self-contained-html

# Run only P0 critical tests
docker-compose run --rm tests pytest -v -m p0

# Start mock server only (in background)
docker-compose up -d mock-server
```

### Interactive Docker Testing

```bash
# Start a shell in the test container
docker-compose run --rm tests /bin/bash

# Then run tests interactively
pytest -v
pytest tests/test_model_compliance.py -v
exit
```

### Docker CI/CD Workflow

A separate GitHub Actions workflow (`.github/workflows/docker-tests.yml`) is available for Docker-based testing:

**To manually trigger Docker tests:**
1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **"Docker-based Model Tests"** workflow
4. Click **"Run workflow"** button
5. Optionally specify a test marker (p0, p1, p2)
6. Click **"Run workflow"**

**Or use GitHub CLI:**
```bash
gh workflow run docker-tests.yml
```

### Docker vs Native Python

| Aspect | Native Python | Docker |
|--------|--------------|--------|
| **Setup Time** | Fast | Medium (build time) |
| **Consistency** | Depends on local env | 100% consistent |
| **CI/CD** | Auto-runs on push | Manual trigger only |
| **Use Case** | Daily development | Production validation |
| **Isolation** | Virtual environment | Full containerization |

### Clean Up Docker Resources

```bash
# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-test`)
3. Add tests following the P0/P1/P2 priority system
4. Ensure all tests pass (`pytest -v`)
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

**Abhishek** - [GitHub](https://github.com/Abhishek0O2)

---

**Test Results**: 29 tests | All Passing ✅ | Coverage: Compliance, Safety, Robustness, PHI Protection
