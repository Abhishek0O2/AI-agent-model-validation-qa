#!/usr/bin/env python3
"""Generate a concise regression HTML report from pytest JUnit XML output.

Usage:
    python scripts/generate_regression_report.py --junit reports/junit.xml --html reports/regression_report.html

The script collects total/passed/failed/skipped counts, lists failed tests with messages and tracebacks,
and adds a short recommendations section intended for regression triage.
"""
import argparse
import html
import os
import sys
import xml.etree.ElementTree as ET


def parse_junit(junit_path: str):
    if not os.path.exists(junit_path):
        raise FileNotFoundError(f"JUnit XML not found: {junit_path}")

    tree = ET.parse(junit_path)
    root = tree.getroot()

    # junit xml may have <testsuite> or <testsuites>
    suites = []
    if root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    elif root.tag == "testsuite":
        suites = [root]
    else:
        suites = list(root.findall("testsuite"))

    total = 0
    failures = 0
    errors = 0
    skipped = 0
    passed = 0
    failed_cases = []

    for s in suites:
        t = int(s.attrib.get("tests", 0))
        f = int(s.attrib.get("failures", 0))
        e = int(s.attrib.get("errors", 0))
        sk = int(s.attrib.get("skipped", 0) or s.attrib.get("skips", 0) or 0)
        total += t
        failures += f
        errors += e
        skipped += sk

        for case in s.findall("testcase"):
            name = case.attrib.get("name")
            classname = case.attrib.get("classname")
            time = case.attrib.get("time")
            # check for failure or error
            fail = case.find("failure")
            err = case.find("error")
            skip = case.find("skipped")
            if fail is not None or err is not None:
                content = (fail.text or "") if fail is not None else (err.text or "")
                failed_cases.append({
                    "name": name,
                    "classname": classname,
                    "time": time,
                    "content": content,
                    "type": "failure" if fail is not None else "error",
                })
            elif skip is not None:
                # nothing
                pass
            else:
                passed += 1

    # If passed wasn't filled from testcases, compute as remainder
    computed_passed = total - failures - errors - skipped
    if passed == 0:
        passed = computed_passed

    return {
        "total": total,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "failed_cases": failed_cases,
    }


def generate_html(summary: dict, junit_path: str, pytest_html_path: str = None):
    total = summary["total"]
    passed = summary["passed"]
    failures = summary["failures"]
    errors = summary["errors"]
    skipped = summary["skipped"]
    failed_cases = summary["failed_cases"]

    # Recommendations heuristics
    recs = []
    if failures + errors == 0:
        recs.append("All tests passed — baseline looks healthy. Recommend promoting this run as a regression baseline and gating merges on P0 tests.")
        recs.append("Keep the generated HTML and JUnit artifacts attached to the CI run for traceability.")
    else:
        recs.append("Prioritize triage of failing P0 tests immediately. Create reproducible bug tickets including the failing test name, input payload, and stack trace.")
        recs.append("If failures are flaky, rerun the tests to confirm. Consider isolating flaky tests and adding retries or marking as flaky until fixed.")
        recs.append("For each defect, add a regression test that reproduces the bug and include a short reproduction section in the ticket.")

    # Build HTML
    html_parts = [
        "<html><head><meta charset=\"utf-8\"><title>Regression Report</title>",
        "<style>body{font-family:Arial,Helvetica,sans-serif;padding:20px}h1{color:#222}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}th{background:#f4f4f4}</style>",
        "</head><body>",
        "<h1>Regression Test Report</h1>",
        f"<p><strong>Total tests:</strong> {total} &nbsp; <strong>Passed:</strong> {passed} &nbsp; <strong>Failures:</strong> {failures} &nbsp; <strong>Errors:</strong> {errors} &nbsp; <strong>Skipped:</strong> {skipped}</p>",
        f"<p><strong>JUnit XML:</strong> {html.escape(junit_path)}</p>",
    ]

    if pytest_html_path:
        html_parts.append(f"<p><strong>PyTest HTML:</strong> {html.escape(pytest_html_path)}</p>")

    # Defect summary
    html_parts.append("<h2>Defect summary</h2>")
    if not failed_cases:
        html_parts.append("<p>No failing tests detected.</p>")
    else:
        html_parts.append("<table><thead><tr><th>Test</th><th>Class</th><th>Type</th><th>Message / Trace</th></tr></thead><tbody>")
        for fcase in failed_cases:
            msg = html.escape((fcase.get("content") or "").strip())
            html_parts.append(
                "<tr>" +
                f"<td>{html.escape(fcase.get('name',''))}</td>" +
                f"<td>{html.escape(fcase.get('classname') or '')}</td>" +
                f"<td>{html.escape(fcase.get('type'))}</td>" +
                f"<td><pre style=\"white-space:pre-wrap;max-height:300px;overflow:auto\">{msg}</pre></td>" +
                "</tr>"
            )
        html_parts.append("</tbody></table>")

    # Recommendations
    html_parts.append("<h2>Recommendations for regression testing</h2>")
    html_parts.append("<ul>")
    for r in recs:
        html_parts.append(f"<li>{html.escape(r)}</li>")
    html_parts.append("</ul>")

    # Helpful next steps
    html_parts.append("<h3>Suggested next steps</h3>")
    html_parts.append("<ol>")
    html_parts.append("<li>Attach the full pytest HTML and JUnit XML to the bug tickets.</li>")
    html_parts.append("<li>If failures are environment-dependent, capture environment details and re-run with `-k <testname>` locally to reproduce.</li>")
    html_parts.append("<li>Prioritize fixing P0 tests; add regression tests for any resolved defects.</li>")
    html_parts.append("</ol>")

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", required=True, help="Path to junit xml file")
    parser.add_argument("--pytest-html", required=False, help="Path to pytest-html output (optional)")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    summary = parse_junit(args.junit)
    html_content = generate_html(summary, args.junit, args.pytest_html)

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html_content)

    print(f"Generated regression report: {args.out}")


if __name__ == "__main__":
    main()
