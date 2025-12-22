from playwright.sync_api import sync_playwright
import json
from pathlib import Path

OUT_DIR = Path("/tmp/ebmud_cas_debug")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOGIN_URL = "https://cas.ebmud.com/cas/login"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Opening {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="networkidle", timeout=60_000)

        # Screenshot for visual confirmation
        screenshot_path = OUT_DIR / "cas_login.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        # Save raw HTML
        html_path = OUT_DIR / "cas_login.html"
        html_path.write_text(page.content(), encoding="utf-8")

        # Extract all inputs
        inputs = page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll("input"));
                return inputs.map((el, idx) => ({
                    index: idx,
                    tag: el.tagName.toLowerCase(),
                    type: el.getAttribute("type"),
                    name: el.getAttribute("name"),
                    id: el.getAttribute("id"),
                    placeholder: el.getAttribute("placeholder"),
                    ariaLabel: el.getAttribute("aria-label"),
                    class: el.getAttribute("class"),
                    autocomplete: el.getAttribute("autocomplete"),
                    visible: !!(
                        el.offsetWidth ||
                        el.offsetHeight ||
                        el.getClientRects().length
                    )
                }));
            }
        """)

        print("\n=== Detected input fields ===\n")
        print(json.dumps(inputs, indent=2))

        fields_path = OUT_DIR / "cas_inputs.json"
        fields_path.write_text(json.dumps(inputs, indent=2), encoding="utf-8")

        print("\nArtifacts written to:")
        print(f"  {screenshot_path}")
        print(f"  {html_path}")
        print(f"  {fields_path}")

        browser.close()


if __name__ == "__main__":
    main()
