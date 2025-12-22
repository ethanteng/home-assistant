#!/usr/bin/env python3
import os
from flask import Flask, Response, jsonify
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# Environment variables (required)
# -------------------------------------------------------------------
# export EBMUD_EMAIL="you@example.com"
# export EBMUD_PASSWORD="supersecret"
# -------------------------------------------------------------------

EBMUD_USERNAME = os.environ["EBMUD_EMAIL"]
EBMUD_PASSWORD = os.environ["EBMUD_PASSWORD"]

LOGIN_URL = "https://cas.ebmud.com/cas/login"
DOWNLOAD_URL = "https://ebmud.watersmart.com/index.php/Download/usage?combined=0"

app = Flask(__name__)


def fetch_csv_via_browser() -> str:
    """
    Logs into EBMUD via CAS and downloads the WaterSmart usage CSV.
    Returns raw CSV text.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context()
        page = context.new_page()

        # ------------------------------------------------------------
        # 1) Go directly to CAS login (this is the real entry point)
        # ------------------------------------------------------------
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # Wait for actual fields seen in the browser
        page.locator("#username").wait_for(state="visible", timeout=15_000)
        page.locator("#username").fill(EBMUD_USERNAME)

        page.locator("#password").fill(EBMUD_PASSWORD)

        page.locator('button[type="submit"]').click()

        # ------------------------------------------------------------
        # 2) Let CAS → SAML → WaterSmart redirects finish
        # ------------------------------------------------------------
        #page.wait_for_load_state("networkidle", timeout=30_000)
        page.wait_for_url("**/index.php/**", timeout=30_000)

        # Debug checkpoint after login
        page.screenshot(
            path="/tmp/ebmud_after_login.png",
            full_page=True,
        )

        # ------------------------------------------------------------
        # 3) Download CSV directly
        # ------------------------------------------------------------
        response = page.goto(DOWNLOAD_URL, wait_until="networkidle")

        if not response or response.status != 200:
            page.screenshot(
                path="/tmp/ebmud_download_failed.png",
                full_page=True,
            )
            raise RuntimeError(
                f"CSV download failed: "
                f"{response.status if response else 'no response'}"
            )

        csv_text = response.text()

        browser.close()
        return csv_text


# -------------------------------------------------------------------
# Flask routes
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8081,
        debug=True,
    )
