#!/usr/bin/env python3
import os
from flask import Flask, Response, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

# ---------------------------------------------------------
# Load environment variables from .env
# ---------------------------------------------------------
load_dotenv()

EBMUD_USERNAME = os.getenv("EBMUD_EMAIL")
EBMUD_PASSWORD = os.getenv("EBMUD_PASSWORD")

if not EBMUD_USERNAME or not EBMUD_PASSWORD:
    raise RuntimeError(
        "Missing credentials. Set EBMUD_EMAIL and EBMUD_PASSWORD in .env or environment."
    )

# ---------------------------------------------------------
# URLs
# ---------------------------------------------------------
CAS_LOGIN_URL = "https://cas.ebmud.com/cas/login"
WATERSMART_DOWNLOAD_URL = (
    "https://ebmud.watersmart.com/index.php/Download/usage?combined=0"
)

# ---------------------------------------------------------
# Flask app
# ---------------------------------------------------------
app = Flask(__name__)


def fetch_csv_via_browser() -> str:
    """
    Logs into EBMUD via CAS and downloads the WaterSmart usage CSV.
    Returns raw CSV text.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        context = browser.new_context()
        page = context.new_page()

        # -----------------------------------------------------
        # 1) Open CAS login
        # -----------------------------------------------------
        page.goto(CAS_LOGIN_URL, wait_until="domcontentloaded")

        # Hard wait for the actual login form
        page.locator("form#log_in_form").wait_for(timeout=20_000)

        # Debug: capture login page
        page.screenshot(path="/tmp/ebmud_login_page.png", full_page=True)

        # -----------------------------------------------------
        # 2) Fill credentials (CORRECT selectors)
        # -----------------------------------------------------
        page.fill("#username", EBMUD_USERNAME)
        page.fill("#upassword", EBMUD_PASSWORD)

        # Submit form
        page.click("form#log_in_form button[type='submit']")

        # -----------------------------------------------------
        # 3) Wait until we're authenticated on EBMUD
        # -----------------------------------------------------
        page.wait_for_load_state("networkidle", timeout=30_000)

        # CAS success usually lands us on /customers/account
        # We don't care exactly where — just that we're no longer on /cas/login
        current_url = page.url
        if "/cas/login" in current_url:
            page.screenshot(
                path="/tmp/ebmud_login_failed.png",
                full_page=True,
            )
            raise RuntimeError("Login failed: still on CAS login page")

        # Debug: confirm post-login state
        page.screenshot(path="/tmp/ebmud_after_login.png", full_page=True)

        # -----------------------------------------------------
        # 4) NOW explicitly go to WaterSmart
        # -----------------------------------------------------
        response = page.goto(
            WATERSMART_DOWNLOAD_URL,
            wait_until="networkidle",
        )

        # -----------------------------------------------------
        # 5) Download CSV
        # -----------------------------------------------------
        response = page.goto(
            WATERSMART_DOWNLOAD_URL,
            wait_until="networkidle",
        )

        if not response or response.status != 200:
            page.screenshot(
                path="/tmp/ebmud_download_failed.png",
                full_page=True,
            )
            raise RuntimeError(
                f"CSV download failed (status={response.status if response else 'none'})"
            )

        csv_text = response.text()

        browser.close()
        return csv_text


# ---------------------------------------------------------
# Flask route
# ---------------------------------------------------------
@app.route("/water/daily")
def daily_water():
    try:
        csv_data = fetch_csv_via_browser()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "inline; filename=ebmud_water_usage.csv"
            },
        )
    except Exception as e:
        return jsonify(
            {
                "error": "Failed to fetch EBMUD data",
                "details": str(e),
            }
        ), 500


# ---------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8081,
        debug=True,
    )
