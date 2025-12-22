#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # <-- makes .env reliable regardless of cwd

EBMUD_EMAIL = os.getenv("EBMUD_EMAIL")
EBMUD_PASSWORD = os.getenv("EBMUD_PASSWORD")
PORT = int(os.getenv("PORT", "8081"))
DEBUG = os.getenv("DEBUG", "0") == "1"

# This is the *real* target. If you're not authenticated, it redirects to CAS.
CSV_URL = "https://ebmud.watersmart.com/index.php/accountPreferences/download"

CACHE_PATH = Path(os.getenv("EBMUD_CACHE_PATH", "/tmp/ebmud_water_cache.json"))
CACHE_TTL_SECONDS = int(os.getenv("EBMUD_CACHE_TTL_SECONDS", "3600"))  # 1 hour


def require_env() -> None:
    missing = []
    if not EBMUD_EMAIL:
        missing.append("EBMUD_EMAIL")
    if not EBMUD_PASSWORD:
        missing.append("EBMUD_PASSWORD")
    if missing:
        raise RuntimeError(
            f"Missing required env var(s): {', '.join(missing)}. "
            f"Put them in {BASE_DIR / '.env'} or export them before running."
        )


# -------------------------------------------------------------------
# Cache helpers
# -------------------------------------------------------------------

def load_cache() -> Dict[str, Any] | None:
    try:
        if not CACHE_PATH.exists():
            return None
        raw = json.loads(CACHE_PATH.read_text())
        age = time.time() - float(raw.get("fetched_at", 0))
        if age > CACHE_TTL_SECONDS:
            return None
        return raw
    except Exception:
        return None


def save_cache(rows: List[Dict[str, Any]]) -> None:
    payload = {"fetched_at": time.time(), "rows": rows}
    CACHE_PATH.write_text(json.dumps(payload))


# -------------------------------------------------------------------
# CSV parsing
# -------------------------------------------------------------------

def parse_csv_text(csv_text: str) -> List[Dict[str, Any]]:
    # Watersmart exports sometimes have leading whitespace/newlines
    csv_text = csv_text.lstrip("\ufeff \n\r\t")

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for r in reader:
        # keep as strings; HA templates can cast as needed
        rows.append(dict(r))
    return rows


# -------------------------------------------------------------------
# Playwright fetch
# -------------------------------------------------------------------

def fetch_csv_via_browser() -> List[Dict[str, Any]]:
    require_env()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: go straight to the CSV URL (it will redirect to CAS if needed)
        page.goto(CSV_URL, wait_until="domcontentloaded")

        # If redirected to CAS login, complete login using selectors from your page source:
        # <input id="username" ...>
        # <input id="upassword" ...>
        if "cas.ebmud.com" in page.url:
            if DEBUG:
                page.screenshot(path="/tmp/ebmud_login_debug.png", full_page=True)

            try:
                page.locator("#username").wait_for(state="visible", timeout=30_000)
                page.locator("#username").fill(EBMUD_EMAIL)
                page.locator("#upassword").fill(EBMUD_PASSWORD)

                # Button is: <button type="submit" ...> Login
                page.locator('button[type="submit"]').click()

                # Let redirects finish (CAS -> watersmart)
                page.wait_for_load_state("networkidle", timeout=60_000)
            except PWTimeoutError as e:
                if DEBUG:
                    page.screenshot(path="/tmp/ebmud_login_timeout.png", full_page=True)
                raise RuntimeError(f"Timed out waiting for CAS login fields: {e}")

        # Step 2: now that cookies exist in the context, fetch CSV via the context request
        resp = context.request.get(CSV_URL)
        status = resp.status
        body = resp.text()

        if status != 200:
            raise RuntimeError(f"CSV fetch failed: HTTP {status}")

        # If we somehow got HTML instead of CSV, call it out loudly.
        # (This happens if auth didn't stick or the endpoint changed behavior.)
        if "<html" in body.lower():
            if DEBUG:
                Path("/tmp/ebmud_unexpected_html.html").write_text(body)
            raise RuntimeError("Expected CSV but received HTML (auth likely failed).")

        rows = parse_csv_text(body)
        browser.close()
        return rows


# -------------------------------------------------------------------
# Flask app
# -------------------------------------------------------------------

app = Flask(__name__)


@app.get("/water/daily")
def water_daily():
    cached = load_cache()
    if cached:
        return jsonify({"cached": True, **cached})

    try:
        rows = fetch_csv_via_browser()
        save_cache(rows)
        return jsonify({"cached": False, "fetched_at": time.time(), "rows": rows})
    except Exception as e:
        return jsonify({"cached": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Bind localhost; you can reverse proxy or tunnel via Tailscale if needed
    app.run(host="127.0.0.1", port=PORT, debug=DEBUG)
