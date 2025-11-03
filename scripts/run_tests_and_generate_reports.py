#!/usr/bin/env python3
"""
Run pytest using repo configuration and generate narrative reports from JUnit results.

- Uses pytest.ini to write:
  - reports/report.html (self-contained HTML)
  - reports/junit.xml (JUnit XML)
- Generates:
  - reports/Model_Test_Report.md (key findings, defect summary, recommendations)
  - reports/regression_report.html (compact HTML regression summary)

Exit code mirrors pytest's exit code.
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
JUNIT = REPORTS / "junit.xml"
PYTEST_HTML = REPORTS / "report.html"
MD_OUT = REPORTS / "Model_Test_Report.md"
REG_HTML = REPORTS / "regression_report.html"


def run_pytest(env: dict | None = None) -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pytest"]
    print(f"Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env or os.environ.copy())
    return proc.returncode


def ensure_junit() -> None:
    if JUNIT.exists():
        return
    # Fallback: force-generate junit if missing for any reason
    print("JUnit not found after pytest run; generating explicitly...")
    subprocess.run([sys.executable, "-m", "pytest", f"--junitxml={JUNIT.as_posix()}"], cwd=str(ROOT), check=False)


def generate_markdown() -> None:
    script = ROOT / "scripts" / "generate_test_report.py"
    subprocess.run([sys.executable, str(script), "--junit", str(JUNIT), "--out", str(MD_OUT)], cwd=str(ROOT), check=False)


def generate_regression_html() -> None:
    script = ROOT / "scripts" / "generate_regression_report.py"
    args = [sys.executable, str(script), "--junit", str(JUNIT), "--out", str(REG_HTML)]
    if PYTEST_HTML.exists():
        args += ["--pytest-html", str(PYTEST_HTML)]
    subprocess.run(args, cwd=str(ROOT), check=False)


def main() -> int:
    # Default to good mock server unless overridden
    env = os.environ.copy()
    env.setdefault("USE_MOCK", "1")

    code = run_pytest(env)
    # Tiny wait to ensure file flush
    time.sleep(0.2)
    ensure_junit()
    generate_markdown()
    generate_regression_html()

    # Print a concise summary of artifacts
    print("\nArtifacts:")
    for p in [PYTEST_HTML, JUNIT, MD_OUT, REG_HTML]:
        print(f" - {p.relative_to(ROOT)} {'(missing)' if not p.exists() else ''}")

    return code


if __name__ == "__main__":
    sys.exit(main())
