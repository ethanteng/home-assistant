import os
import csv
import io
from flask import Flask, jsonify
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

EBMUD_USERNAME = os.environ["EBMUD_EMAIL"]
EBMUD_PASSWORD = os.environ["EBMUD_PASSWORD"]

LOGIN_URL = "https://cas.ebmud.com"
DOWNLOAD_URL = "https://ebmud.watersmart.com/index.php/accountPreferences/download"

app = Flask(__name__)


def fetch_csv_via_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # --- Login ---
        page.goto("https://www.ebmud.com/customer-login", wait_until="domcontentloaded")

        page.locator('input[name="email"]').wait_for(state="visible", timeout=15_000)
        page.locator('input[name="email"]').fill(EBMUD_USERNAME)
        page.locator('input[name="password"]').fill(EBMUD_PASSWORD)

        page.locator('button[type="submit"]').click()

        # Wait for auth to settle (cookie + redirect)
        page.wait_for_load_state("load")

        # --- Fetch CSV directly ---
        response = page.goto(DOWNLOAD_URL, wait_until="domcontentloaded")

        if not response or response.status != 200:
            raise RuntimeError(
                f"Failed to fetch CSV: HTTP {response.status if response else 'no response'}"
            )

        csv_text = response.text()

        browser.close()
        return csv_text


def parse_csv(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    if not rows:
        raise RuntimeError("CSV parsed successfully but contains no rows")

    latest = rows[-1]

    return {
        "rows": len(rows),
        "latest_date": latest.get("Date"),
        "latest_usage_gallons": latest.get("Usage (Gallons)"),
    }


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/water/daily")
def daily_water():
    csv_text = fetch_csv_via_browser()
    data = parse_csv(csv_text)

    return jsonify({
        "cached": False,
        **data,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=True)
