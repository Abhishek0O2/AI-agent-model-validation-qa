#!/usr/bin/env python3
"""
Generate a detailed HTML report with API request/response information.

This script reads test_details.json (generated during test execution)
and creates a comprehensive HTML report showing:
- Test case details
- API URLs called
- Request payloads
- Response payloads
- Test outcomes
- Timing information
"""
import argparse
import json
import html as html_module
from pathlib import Path
from datetime import datetime
import re


def load_test_details(json_path: str):
    """Load test details from JSON file."""
    if not Path(json_path).exists():
        raise FileNotFoundError(f"Test details JSON not found: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_json(data, max_lines=50):
    """Format JSON data for display with line limit."""
    if data is None:
        return "N/A"
    
    try:
        formatted = json.dumps(data, indent=2, sort_keys=True)
        lines = formatted.split('\n')
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f'\n... ({len(lines) - max_lines} more lines)'
        return formatted
    except:
        return str(data)


def get_outcome_color(outcome):
    """Return CSS color for test outcome."""
    colors = {
        'passed': '#28a745',
        'failed': '#dc3545',
        'skipped': '#ffc107',
        'error': '#dc3545'
    }
    return colors.get(outcome, '#6c757d')


def get_status_color(status_code):
    """Return CSS color for HTTP status code."""
    if 200 <= status_code < 300:
        return '#28a745'
    elif 400 <= status_code < 500:
        return '#ffc107'
    elif 500 <= status_code:
        return '#dc3545'
    return '#6c757d'


def generate_html_report(data: dict, output_path: str):
    """Generate comprehensive HTML report."""
    
    tests = data.get('tests', [])
    total_tests = data.get('total_tests', len(tests))
    timestamp = data.get('timestamp', 'Unknown')
    
    # Calculate statistics
    passed = sum(1 for t in tests if t.get('outcome') == 'passed')
    failed = sum(1 for t in tests if t.get('outcome') == 'failed')
    skipped = sum(1 for t in tests if t.get('outcome') == 'skipped')
    
    # Group by priority markers
    p0_tests = [t for t in tests if 'p0' in t.get('markers', [])]
    p1_tests = [t for t in tests if 'p1' in t.get('markers', [])]
    p2_tests = [t for t in tests if 'p2' in t.get('markers', [])]
    
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>Detailed Test Report with API Calls</title>",
        "  <style>",
        "    * { margin: 0; padding: 0; box-sizing: border-box; }",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; padding: 20px; background: #f5f5f5; }",
        "    .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }",
        "    h1 { color: #333; margin-bottom: 10px; font-size: 28px; }",
        "    h2 { color: #555; margin-top: 30px; margin-bottom: 15px; font-size: 22px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }",
        "    h3 { color: #666; margin-top: 20px; margin-bottom: 10px; font-size: 18px; }",
        "    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }",
        "    .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }",
        "    .stat-card h3 { color: white; font-size: 14px; text-transform: uppercase; margin: 0; }",
        "    .stat-card .value { font-size: 36px; font-weight: bold; margin: 10px 0; }",
        "    .stat-card.passed { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }",
        "    .stat-card.failed { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }",
        "    .stat-card.skipped { background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); }",
        "    .test-case { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px; margin: 15px 0; padding: 20px; }",
        "    .test-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }",
        "    .test-name { font-weight: bold; font-size: 16px; color: #333; }",
        "    .test-outcome { padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; color: white; }",
        "    .test-meta { color: #666; font-size: 13px; margin: 8px 0; }",
        "    .markers { display: inline-flex; gap: 5px; }",
        "    .marker { background: #e0e7ff; color: #4338ca; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; }",
        "    .marker.p0 { background: #fee2e2; color: #991b1b; }",
        "    .marker.p1 { background: #fef3c7; color: #92400e; }",
        "    .marker.p2 { background: #dbeafe; color: #1e40af; }",
        "    .api-call { background: white; border: 1px solid #d0d0d0; border-radius: 4px; margin: 10px 0; padding: 15px; }",
        "    .api-header { font-weight: bold; margin-bottom: 10px; color: #444; display: flex; justify-content: space-between; align-items: center; }",
        "    .http-method { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; color: white; margin-right: 8px; }",
        "    .method-post { background: #3b82f6; }",
        "    .method-get { background: #10b981; }",
        "    .status-code { padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; color: white; }",
        "    .api-url { color: #666; font-family: 'Courier New', monospace; font-size: 13px; margin: 5px 0; word-break: break-all; }",
        "    .payload-section { margin: 10px 0; }",
        "    .payload-label { font-weight: bold; color: #555; font-size: 13px; margin-bottom: 5px; }",
        "    pre { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px; overflow-x: auto; font-size: 12px; line-height: 1.5; }",
        "    details { margin: 10px 0; }",
        "    summary { cursor: pointer; font-weight: bold; color: #3b82f6; padding: 8px; background: #eff6ff; border-radius: 4px; user-select: none; }",
        "    summary:hover { background: #dbeafe; }",
        "    summary::marker { color: #3b82f6; }",
        "    details[open] summary { margin-bottom: 10px; }",
        "    .assertion-block { background: #f0fdf4; border: 1px solid #86efac; border-radius: 4px; padding: 10px; margin: 10px 0; }",
    "    .assertion-item { background: #d1fae5; border-left: 3px solid #065f46; padding: 8px; margin: 5px 0; border-radius: 3px; }",
    "    .assertion-item.failed { background: #fee2e2; border-left-color: #dc2626; }",
    "    .ea { margin-top:6px; font-size:12px; color:#374151; display:flex; gap:16px; flex-wrap:wrap; }",
    "    .ea .label { color:#6b7280; font-weight:600; margin-right:4px; }",
    "    .badge { display:inline-block; background:#e5e7eb; color:#374151; font-size:11px; padding:2px 6px; border-radius:999px; margin-left:6px; }",
        "    .docstring { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; margin: 10px 0; font-style: italic; color: #78350f; }",
        "    .failure-message { background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin: 10px 0; color: #7f1d1d; }",
        "    .timestamp { color: #999; font-size: 12px; }",
        "    .duration { color: #666; font-size: 12px; }",
        "    .no-api-calls { color: #999; font-style: italic; padding: 10px; }",
        "    .toc { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 20px; margin: 20px 0; }",
        "    .toc ul { list-style: none; }",
        "    .toc li { margin: 8px 0; }",
        "    .toc a { color: #3b82f6; text-decoration: none; }",
        "    .toc a:hover { text-decoration: underline; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class='container'>",
        f"    <h1>🔬 Detailed Test Report with API Calls</h1>",
        f"    <p class='timestamp'>Generated: {timestamp}</p>",
        "",
        "    <div class='summary'>",
        f"      <div class='stat-card'><h3>Total Tests</h3><div class='value'>{total_tests}</div></div>",
        f"      <div class='stat-card passed'><h3>Passed</h3><div class='value'>{passed}</div></div>",
        f"      <div class='stat-card failed'><h3>Failed</h3><div class='value'>{failed}</div></div>",
        f"      <div class='stat-card skipped'><h3>Skipped</h3><div class='value'>{skipped}</div></div>",
        "    </div>",
        "",
        "    <div class='toc'>",
        "      <h3>📋 Priority Breakdown</h3>",
        "      <ul>",
        f"        <li><strong>P0 Tests (Safety-Critical):</strong> {len(p0_tests)}</li>",
        f"        <li><strong>P1 Tests (High Priority):</strong> {len(p1_tests)}</li>",
        f"        <li><strong>P2 Tests (Robustness):</strong> {len(p2_tests)}</li>",
        "      </ul>",
        "    </div>",
    ]
    
    # Group tests by outcome for better organization
    for section_name, section_tests in [
        ("❌ Failed Tests", [t for t in tests if t.get('outcome') == 'failed']),
        ("✅ Passed Tests", [t for t in tests if t.get('outcome') == 'passed']),
        ("⊘ Skipped Tests", [t for t in tests if t.get('outcome') == 'skipped']),
    ]:
        if not section_tests:
            continue
        
        html_parts.append(f"    <h2>{section_name}</h2>")
        
        for test in section_tests:
            test_name = test.get('test_name', 'Unknown')
            test_func = test.get('test_function', '')
            outcome = test.get('outcome', 'unknown')
            duration = test.get('duration', 0)
            markers = test.get('markers', [])
            api_calls = test.get('api_calls', [])
            metrics = test.get('metrics')
            docstring = test.get('docstring', '').strip()
            failure_msg = test.get('failure_message', '')
            
            outcome_color = get_outcome_color(outcome)
            
            html_parts.append("    <div class='test-case'>")
            html_parts.append("      <div class='test-header'>")
            html_parts.append(f"        <div class='test-name'>{html_module.escape(test_func)}</div>")
            html_parts.append(f"        <span class='test-outcome' style='background-color: {outcome_color}'>{outcome}</span>")
            html_parts.append("      </div>")
            
            html_parts.append(f"      <div class='test-meta'>")
            html_parts.append(f"        <strong>Path:</strong> {html_module.escape(test_name)}<br>")
            html_parts.append(f"        <strong>Duration:</strong> {duration:.3f}s")
            
            if markers:
                html_parts.append("        &nbsp;&nbsp;|&nbsp;&nbsp;<strong>Markers:</strong> <div class='markers' style='display: inline-flex;'>")
                for marker in markers:
                    html_parts.append(f"          <span class='marker {marker}'>{marker}</span>")
                html_parts.append("        </div>")
            
            html_parts.append("      </div>")
            
            # Add docstring if present
            if docstring:
                clean_doc = '\n'.join(line.strip() for line in docstring.split('\n'))
                html_parts.append(f"      <div class='docstring'>{html_module.escape(clean_doc)}</div>")
            
            # Add failure message if test failed
            if failure_msg:
                html_parts.append(f"      <div class='failure-message'>")
                html_parts.append(f"        <strong>Failure Details:</strong><br>")
                html_parts.append(f"        <pre>{html_module.escape(failure_msg[:1000])}</pre>")
                html_parts.append(f"      </div>")
            
            # Parse assertions from test to match with API calls
            assertions = test.get('assertions', [])
            source_code = test.get('source_code', '') or ''

            # Heuristic mapping of assertion -> API call index using source code
            # 1) Map r1/r2/... variables to call indices
            call_var_to_index = {}
            for m in re.finditer(r"\b(r(?P<idx>\d+))\s*=\s*session\.(?:post|get)\s*\(", source_code):
                call_var_to_index[m.group(1)] = int(m.group('idx'))

            # 2) Map response variables like urgent_response = r1.json()
            response_var_to_index = {}
            for m in re.finditer(r"\b(?P<var>\w+_response)\s*=\s*r(?P<idx>\d+)\.json\s*\(", source_code):
                response_var_to_index[m.group('var')] = int(m.group('idx'))

            def assign_call_index(assertion_condition: str):
                if not assertion_condition:
                    return None
                # Direct rN reference
                m = re.search(r"\br(\d+)\b", assertion_condition)
                if m:
                    return int(m.group(1))
                # Response variable reference
                for var, idx_mapped in response_var_to_index.items():
                    if var in assertion_condition:
                        return idx_mapped
                # Call variable name (rare in conditions)
                for var, idx_mapped in call_var_to_index.items():
                    if var in assertion_condition:
                        return idx_mapped
                return None

            # Bucket assertions by API call index
            per_call_assertions = {i: [] for i in range(1, (len(api_calls) or 0) + 1)}
            unassigned_assertions = []
            for a in assertions:
                cond = a.get('condition') or a.get('assertion') or ''
                idx_for_a = assign_call_index(cond)
                if idx_for_a and idx_for_a in per_call_assertions:
                    per_call_assertions[idx_for_a].append(a)
                else:
                    unassigned_assertions.append(a)
            
            # Helper to derive expected/actual for common checks
            def _derive_expected_actual(condition: str, call_data: dict):
                if not condition:
                    return None, None
                resp = call_data.get('response_payload') or {}
                status = call_data.get('status_code')
                # Status code
                m = re.search(r"status_code\s*(==|!=|>=|<=|>|<)\s*(\d+)", condition)
                if m:
                    op, exp = m.group(1), m.group(2)
                    return f"status_code {op} {exp}", f"{status}"
                # Status code membership: status_code in (400, 422) or [400, 422]
                m = re.search(r"status_code\s+in\s*\(([^)]*)\)", condition)
                if m:
                    nums = [n.strip() for n in m.group(1).split(',') if n.strip()]
                    try:
                        nums = [int(n) for n in nums]
                    except Exception:
                        pass
                    return f"status_code in {nums}", f"{status}"
                m = re.search(r"status_code\s+in\s*\[([^\]]*)\]", condition)
                if m:
                    nums = [n.strip() for n in m.group(1).split(',') if n.strip()]
                    try:
                        nums = [int(n) for n in nums]
                    except Exception:
                        pass
                    return f"status_code in {nums}", f"{status}"
                # Class equality
                m = re.search(r"\[\"class\"\]\s*==\s*['\"]([^'\"]+)['\"]", condition)
                if m:
                    exp = m.group(1)
                    act = resp.get('class') if isinstance(resp, dict) else None
                    return f"class == '{exp}'", f"{act}"
                # Class inclusion
                m = re.search(r"\[\"class\"\]\s*in\s*\(([^)]*)\)", condition)
                if m:
                    options_raw = m.group(1)
                    opts = [o.strip().strip("'\"") for o in options_raw.split(',') if o.strip()]
                    act = resp.get('class') if isinstance(resp, dict) else None
                    return f"class in {opts}", f"{act}"
                # Confidence threshold
                m = re.search(r"confidence\"?\]?\s*(>=|<=|==|>|<)\s*([0-9]*\.?[0-9]+)", condition)
                if m:
                    op, exp = m.group(1), m.group(2)
                    act = resp.get('confidence') if isinstance(resp, dict) else None
                    return f"confidence {op} {exp}", f"{act}"
                # Explanations presence/length
                if '"explanations" in' in condition or "'explanations' in" in condition:
                    has = False
                    length = 0
                    if isinstance(resp, dict):
                        exps = resp.get('explanations')
                        if isinstance(exps, list):
                            length = len(exps)
                            has = length > 0
                        else:
                            has = exps is not None
                    return "explanations present", f"{has} (len={length})"
                m = re.search(r"len\(.*\[\"explanations\"\]\)\s*>\s*0", condition)
                if m:
                    length = 0
                    if isinstance(resp, dict):
                        exps = resp.get('explanations')
                        if isinstance(exps, list):
                            length = len(exps)
                    return "> 0 explanations", f"len={length}"
                return None, None

            # Add API calls with their related assertions
            if api_calls:
                # Deduplicate API calls (avoid duplicates from combined session/global capture)
                def _call_key(c):
                    try:
                        req = c.get('request_payload')
                        if req is None:
                            req = c.get('request_params') or c.get('request_data')
                        req_s = json.dumps(req, sort_keys=True, default=str)
                    except Exception:
                        req_s = str(req)
                    try:
                        resp_s = json.dumps(c.get('response_payload'), sort_keys=True, default=str)
                    except Exception:
                        resp_s = c.get('response_text') or ''
                    return (
                        c.get('method'),
                        c.get('url'),
                        c.get('status_code'),
                        req_s,
                        resp_s,
                    )

                deduped_calls = []
                seen = set()
                for c in api_calls:
                    k = _call_key(c)
                    if k in seen:
                        continue
                    seen.add(k)
                    deduped_calls.append(c)

                html_parts.append(f"      <h3>API Calls & Assertions ({len(deduped_calls)} calls)</h3>")
                for idx, call in enumerate(deduped_calls, 1):
                    method = call.get('method', 'UNKNOWN')
                    url = call.get('url', '')
                    status_code = call.get('status_code', 0)
                    elapsed = call.get('elapsed_seconds', 0)
                    request_payload = call.get('request_payload')
                    response_payload = call.get('response_payload')
                    response_text = call.get('response_text', '')
                    
                    status_color = get_status_color(status_code)
                    method_class = f"method-{method.lower()}"
                    
                    html_parts.append("      <div class='api-call'>")
                    html_parts.append("        <div class='api-header'>")
                    html_parts.append(f"          <div>")
                    html_parts.append(f"            <span class='http-method {method_class}'>{method}</span>")
                    html_parts.append(f"            Call #{idx}")
                    html_parts.append(f"          </div>")
                    html_parts.append(f"          <div>")
                    html_parts.append(f"            <span class='status-code' style='background-color: {status_color}'>Status: {status_code}</span>")
                    html_parts.append(f"            <span class='duration'> • {elapsed:.3f}s</span>")
                    html_parts.append(f"          </div>")
                    html_parts.append("        </div>")
                    html_parts.append(f"        <div class='api-url'><strong>URL:</strong> {html_module.escape(url)}</div>")
                    
                    # Request Payload - Collapsible
                    if request_payload:
                        html_parts.append("        <details>")
                        html_parts.append("          <summary>📤 Request Payload (click to expand)</summary>")
                        html_parts.append(f"          <pre>{html_module.escape(format_json(request_payload))}</pre>")
                        html_parts.append("        </details>")
                    
                    # Response Payload - Collapsible (closed by default)
                    if response_payload:
                        html_parts.append("        <details>")
                        html_parts.append("          <summary>📥 Response Payload (click to expand)</summary>")
                        html_parts.append(f"          <pre>{html_module.escape(format_json(response_payload))}</pre>")
                        html_parts.append("        </details>")
                    elif response_text:
                        html_parts.append("        <details>")
                        html_parts.append("          <summary>📥 Response (Text)</summary>")
                        html_parts.append(f"          <pre>{html_module.escape(response_text)}</pre>")
                        html_parts.append("        </details>")
                    
                    # Show only the assertions mapped to this API call
                    call_asserts = per_call_assertions.get(idx, []) if deduped_calls else []
                    # Deduplicate by condition string and drop items without a condition
                    seen_conditions = set()
                    filtered_asserts = []
                    for a in call_asserts:
                        cond = a.get('condition') or ''
                        if not cond:
                            continue
                        if cond in seen_conditions:
                            continue
                        seen_conditions.add(cond)
                        filtered_asserts.append(a)

                    if filtered_asserts:
                        html_parts.append("        <details>")
                        html_parts.append(f"          <summary>🔍 Test Assertions <span class='badge'>{len(filtered_asserts)}</span> (click to expand)</summary>")
                        html_parts.append("          <div class='assertion-block'>")

                        for assertion in filtered_asserts:
                            condition = assertion.get('condition', '')
                            passed = assertion.get('passed', True)
                            full_assertion = assertion.get('full_assertion', '')
                            
                            icon = "✅" if passed else "❌"
                            css_class = "" if passed else " failed"
                            
                            # Determine assertion type for better labeling
                            assertion_label = "ASSERTION"
                            if 'status_code' in condition or 'status' in condition.lower():
                                assertion_label = "STATUS CHECK"
                            elif 'confidence' in condition.lower():
                                assertion_label = "CONFIDENCE CHECK"
                            elif 'class' in condition.lower() or 'classification' in condition.lower():
                                assertion_label = "CLASSIFICATION CHECK"
                            elif 'explanation' in condition.lower():
                                assertion_label = "EXPLANATION CHECK"
                            elif 'warning' in condition.lower():
                                assertion_label = "WARNING CHECK"
                            
                            html_parts.append(f"          <div class='assertion-item{css_class}'>")
                            html_parts.append(f"            <div style='font-weight:bold;font-size:11px;color:#666;margin-bottom:3px'>{icon} {assertion_label}</div>")
                            html_parts.append(f"            <code style='color:#333;font-size:13px'>{html_module.escape(condition)}</code>")
                            exp, act = _derive_expected_actual(condition, call)
                            if exp or act is not None:
                                html_parts.append("            <div class='ea'>")
                                if exp:
                                    html_parts.append(f"              <div><span class='label'>Expected:</span> {html_module.escape(str(exp))}</div>")
                                if act is not None:
                                    html_parts.append(f"              <div><span class='label'>Actual:</span> {html_module.escape(str(act))}</div>")
                                html_parts.append("            </div>")
                            html_parts.append("          </div>")

                        html_parts.append("          </div>")
                        html_parts.append("        </details>")
                    else:
                        # Always render a consistent assertions section, even if none mapped
                        html_parts.append("        <details>")
                        html_parts.append("          <summary>🔍 Test Assertions <span class='badge'>0</span> (click to expand)</summary>")
                        html_parts.append("          <div class='assertion-block'>")
                        html_parts.append("            <div class='assertion-item' style='background:#eef2ff;border-left-color:#6366f1'>")
                        html_parts.append("              <div style='font-weight:bold;font-size:11px;color:#4f46e5;margin-bottom:3px'>ℹ️ No explicit assertions mapped to this API call</div>")
                        html_parts.append("              <div style='color:#374151;font-size:12px'>This call executed without a direct assert referencing rN or *_response in the test.</div>")
                        html_parts.append("            </div>")
                        html_parts.append("          </div>")
                        html_parts.append("        </details>")
                    # Do not show unassigned assertions to avoid noise
                    
                    html_parts.append("      </div>")
            else:
                html_parts.append("      <div class='no-api-calls'>No API calls captured for this test</div>")
            
            # Add Performance Metrics if present
            if metrics:
                html_parts.append("      <h3>Performance Metrics</h3>")
                html_parts.append("      <details>")
                html_parts.append("        <summary>📊 View Performance Metrics</summary>")
                html_parts.append("        <table style='width:100%;border-collapse:collapse;margin:10px 0'>")
                html_parts.append("        <thead><tr><th style='text-align:left;border:1px solid #ddd;padding:6px;background:#f4f4f4'>Metric</th><th style='text-align:left;border:1px solid #ddd;padding:6px;background:#f4f4f4'>Value</th></tr></thead><tbody>")
                for k, v in metrics.items():
                    pretty = v
                    if isinstance(v, (dict, list)):
                        pretty = format_json(v, max_lines=20)
                    html_parts.append(f"        <tr><td style='border:1px solid #ddd;padding:6px'>{html_module.escape(str(k))}</td><td style='border:1px solid #ddd;padding:6px'><pre style='margin:0'>{html_module.escape(str(pretty))}</pre></td></tr>")
                html_parts.append("        </tbody></table>")
                html_parts.append("      </details>")
            
            
            html_parts.append("    </div>")
    
    html_parts.extend([
        "  </div>",
        "</body>",
        "</html>"
    ])
    
    # Write to file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    
    print(f"✓ Detailed HTML report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate detailed HTML report with API call information")
    parser.add_argument("--json", default="reports/test_details.json", help="Path to test details JSON file")
    parser.add_argument("--out", default="reports/detailed_report.html", help="Output HTML path")
    args = parser.parse_args()
    
    try:
        data = load_test_details(args.json)
        generate_html_report(data, args.out)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure to run tests first to generate test_details.json")
        return 1
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
