import os
import tempfile
import pytest

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

pytestmark = pytest.mark.skipif(sync_playwright is None, reason="Playwright not installed")

# Two public demo pages:
# - Size validation: ExpandTesting (500KB limit)
# - Type validation: Blueimp (images only)
SIZE_URL = "https://practice.expandtesting.com/upload"
TYPE_URL = "https://blueimp.github.io/jQuery-File-Upload/"


def test_oversized_file_shows_clear_error():
    with tempfile.TemporaryDirectory() as tmp:
        big_path = os.path.join(tmp, "big.pdf")
        with open(big_path, "wb") as f:
            f.write(b"a" * (700 * 1024))  # ~700KB

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(SIZE_URL, wait_until="domcontentloaded")
            page.set_input_files("input[type=file]", big_path)
            page.get_by_role("button", name="Upload").click()
            page.wait_for_timeout(1200)
            text = page.locator("body").inner_text().lower()
            assert any(m in text for m in ["less than 500kb", "500kb", "500 kb"]), (
                "Expected a clear message about the 500KB limit"
            )
            browser.close()


def test_small_file_upload_success_feedback():
    with tempfile.TemporaryDirectory() as tmp:
        small_path = os.path.join(tmp, "small.txt")
        with open(small_path, "wb") as f:
            f.write(b"hello world\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(SIZE_URL, wait_until="domcontentloaded")
            page.set_input_files("input[type=file]", small_path)
            page.get_by_role("button", name="Upload").click()
            page.wait_for_timeout(1200)
            text = page.locator("body").inner_text().lower()
            assert any(m in text for m in ["uploaded", os.path.basename(small_path).lower(), "success"]), (
                f"Expected success feedback, got: {text[:400]}"
            )
            browser.close()


def test_wrong_file_type_shows_error_message():
    """Upload a non-image file to an image-only uploader and expect a clear error."""
    with tempfile.TemporaryDirectory() as tmp:
        bad_path = os.path.join(tmp, "not_an_image.txt")
        with open(bad_path, "wb") as f:
            f.write(b"just some text\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(TYPE_URL, wait_until="domcontentloaded")
            # Blueimp demo uses an <input type=file> (id="fileupload")
            page.set_input_files("input[type=file]", bad_path)
            page.wait_for_timeout(1500)
            text = page.locator("body").inner_text().lower()
            # Typical error phrases shown by Blueimp when type is not allowed
            markers = ["not allowed", "only image files", "file type"]
            assert any(m in text for m in markers), (
                f"Expected a clear 'type not allowed' message, got: {text[:400]}"
            )
            browser.close()
