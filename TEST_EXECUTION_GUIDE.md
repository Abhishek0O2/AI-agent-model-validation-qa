# Test Execution Guide

## Quick Reference

### Run All Tests
```powershell
python -m pytest
```

### Run by Priority
```powershell
# P0: Safety-critical tests
python -m pytest -m p0 -v

# P1: High priority quality tests
python -m pytest -m p1 -v

# P2: Robustness/edge case tests
python -m pytest -m p2 -v
```

### Run Demonstration Tests
```powershell
# Functional demonstration (risk classification, validation)
python scripts/run_demo_tests.py

# Complete demo (functional + performance)
python scripts/run_complete_demo.py
```

### Run Performance Tests
```powershell
# All performance tests
python -m pytest -m performance -v -s

# Load tests only
python -m pytest -m load -v -s

# Specific performance test
python -m pytest tests/test_performance_load.py::test_demo_response_time_benchmarks -v -s
```

### Generate Reports
```powershell
# Generate all reports
python scripts/run_tests_and_generate_reports.py

# Generate detailed API report from existing test run
python scripts/generate_detailed_report.py
```

## Test Categories

### 🔴 P0 Tests (Safety-Critical)
- Schema validation
- Label whitelist compliance
- PHI leakage detection
- Out-of-distribution detection

### 🟡 P1 Tests (High Priority)
- Multilingual support
- Text noise handling (typos, synonyms)
- Date format variations
- Categorical value variations

### 🟢 P2 Tests (Robustness)
- Invalid input rejection
- Edge case handling
- Long input processing

### 🎯 Demo Tests
Showcase model capabilities:
- Risk classification (urgent, elevated, needs review)
- Invalid input handling
- Confidence scoring
- Performance benchmarks
- Load testing

### ⚡ Performance Tests
- Response time benchmarks (avg, p95, p99)
- Concurrent load handling (10+ users)
- Sustained load stability
- Throughput capacity testing

## Environment Variables

```powershell
# Use mock server (default for local testing)
$env:USE_MOCK="1"

# Model URL (for Docker/production)
$env:MODEL_URL="http://localhost:8000"

# Request timeout
$env:REQUEST_TIMEOUT_S="10"
```

## Generated Reports

After running tests, check `reports/` directory:

| File | Description |
|------|-------------|
| `detailed_report.html` | Comprehensive report with API request/response details |
| `demo_showcase_report.html` | Focused demo report for stakeholders |
| `complete_demo_report.html` | Full demo including performance tests |
| `report.html` | Standard pytest HTML report |
| `regression_report.html` | Regression test summary |
| `Model_Test_Report.md` | Markdown summary |
| `junit.xml` | JUnit XML for CI/CD |
| `test_details.json` | Raw API call data |

## Performance Metrics Explained

### Response Time Metrics
- **Average**: Mean response time across all requests
- **Median**: Middle value (50th percentile)
- **P95**: 95th percentile - 95% of requests faster than this
- **P99**: 99th percentile - 99% of requests faster than this
- **Std Dev**: Standard deviation (variability)

### Load Test Metrics
- **Throughput**: Requests per second (req/s)
- **Success Rate**: Percentage of successful requests
- **Concurrency**: Number of simultaneous users/requests
- **Degradation**: Performance change over time

### SLA Thresholds (Customizable)
- Average response time: < 1000ms
- P95 response time: < 2000ms
- Success rate: >= 95%
- Minimum throughput: >= 5 req/s

## Common Test Scenarios

### Quick Smoke Test (P0 only)
```powershell
$env:USE_MOCK="1"
python -m pytest -m p0 -v
```

### Full Validation Suite
```powershell
python scripts/run_tests_and_generate_reports.py
```

### Stakeholder Demo
```powershell
python scripts/run_complete_demo.py
# Then open: reports/complete_demo_report.html
```

### Performance Benchmarking
```powershell
$env:USE_MOCK="1"
python -m pytest -m performance -v -s --tb=short
```

### Load Testing Only
```powershell
python -m pytest tests/test_performance_load.py::test_demo_concurrent_load_handling -v -s
```

## Viewing Reports

### Open in Browser
```powershell
# Windows
Start-Process reports/detailed_report.html

# Alternative
Invoke-Item reports/detailed_report.html
```

### View JSON Data
```powershell
Get-Content reports/test_details.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

## Tips

1. **Run with `-s` flag** to see detailed output during tests
2. **Use `-v` for verbose** test names and progress
3. **Use `--tb=short`** for concise error tracebacks
4. **Check reports/** after every test run for detailed analysis
5. **Performance tests take longer** - use specific test selection when iterating
