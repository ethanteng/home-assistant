#!/usr/bin/env python3
import os
from flask import Flask, Response, jsonify
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# Required environment variables
# -------------------------------------------------------------------
EBMUD_USERNAME = os.environ["EBMUD_EMAIL"]
EBMUD_PASSWORD = os.environ["EBMUD_PASSWORD"]

# -------------------------------------------------------------------
# URLs (confirmed real flow)
# -------------------------------------------------------------------
ENTRY_URL = "https://ebmud.waterinsight.com/index.php/trackUsage"
DOWNLOAD_PAGE_URL = "https://ebmud.watersmart.com/index.php/accountPreferences/download"

app = Flask(__name__)


def fetch_csv_via_browser() -> str:
    """
    Logs into EBMUD via CAS + SAML, enters WaterSmart correctly,
    navigates to the download page, and captures the CSV.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context()
        page = context.new_page()

        # ------------------------------------------------------------
        # 1) Entry point — this is CRITICAL
        # ------------------------------------------------------------
        page.goto(ENTRY_URL, wait_until="domcontentloaded")

        # ------------------------------------------------------------
        # 2) CAS login form
        # ------------------------------------------------------------
        page.locator("form#log_in_form").wait_for(timeout=20_000)

        page.fill("#username", EBMUD_USERNAME)
        page.fill("#upassword", EBMUD_PASSWORD)

        page.click("form#log_in_form button[type='submit']")

        # ------------------------------------------------------------
        # 3) Wait for SAML landing
        # ------------------------------------------------------------
        try:
            page.wait_for_url(
                lambda url: "ebmudSaml/landing" in url,
                timeout=30_000,
            )
        except TimeoutError:
            page.screenshot(path="/tmp/ebmud_saml_timeout.png", full_page=True)
            raise RuntimeError("Timed out waiting for SAML landing")

        # ------------------------------------------------------------
        # 4) Wait for real WaterSmart app
        # ------------------------------------------------------------
        try:
            page.wait_for_url(
                lambda url: "trackUsage" in url and "watersmart.com" in url,
                timeout=30_000,
            )
        except TimeoutError:
            page.screenshot(path="/tmp/ebmud_trackusage_timeout.png", full_page=True)
            raise RuntimeError("Timed out waiting for WaterSmart app")

        # ------------------------------------------------------------
        # 5) Go to download page (authenticated)
        # ------------------------------------------------------------
        page.goto(DOWNLOAD_PAGE_URL, wait_until="networkidle")

        # ------------------------------------------------------------
        # 6) Trigger CSV download and capture response
        # ------------------------------------------------------------
        with page.expect_download(timeout=30_000) as download_info:
            page.locator("a[href*='Download']").first.click()

        download = download_info.value
        csv_path = "/tmp/ebmud_water_usage.csv"
        download.save_as(csv_path)

        with open(csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()

        browser.close()
        return csv_text


# -------------------------------------------------------------------
# Flask route
# -------------------------------------------------------------------
@app.route("/water/daily")
def daily_water():
    try:
        #csv_data = fetch_csv_via_browser()
        CACHE_PATH = "/tmp/ebmud_cache.csv"

        if not os.path.exists(CACHE_PATH):
            raise RuntimeError("EBMUD cache missing — cron hasn’t run yet")

        with open(CACHE_PATH) as f:
            csv_data = f.read()

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


@app.route("/water/latest")
def latest_water():
    CACHE_PATH = "/tmp/ebmud_cache.csv"

    if not os.path.exists(CACHE_PATH):
        return jsonify({"error": "cache missing"}), 500

    with open(CACHE_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    latest = rows[0]  # most recent reading
    return jsonify(latest)


# -------------------------------------------------------------------
# Fetch and cache EBMUD CSV
# -------------------------------------------------------------------
def fetch_and_cache():
    csv_data = fetch_csv_via_browser()
    with open("/tmp/ebmud_cache.csv", "w") as f:
        f.write(csv_data)


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch_and_cache()
        print("EBMUD CSV fetched and cached")
    else:
        app.run(
            host="127.0.0.1",
            port=8081,
            debug=False,
        )