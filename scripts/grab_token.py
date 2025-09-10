#!/usr/bin/env python3
from pathlib import Path
import sys
import time
from typing import Optional

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    sys.stderr.write("Playwright not installed. Install with: pip install playwright && playwright install\n")
    raise

PROFILE_DIR = Path.home() / ".pluxee-profile"
START_URL = "https://consumers.pluxee.co.il/"
COOKIE_DOMAINS = [
    "https://api.consumers.pluxee.co.il",
    "https://consumers.pluxee.co.il",
]
TIMEOUT_SECONDS = 180


def _find_token_cookie(context) -> Optional[str]:
    for domain in COOKIE_DOMAINS:
        try:
            for c in context.cookies(domain):
                if c.get("name") == "token" and c.get("value"):
                    return c.get("value")
        except Exception:
            pass
    return None


def main() -> int:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=False
        )
        page = ctx.new_page()
        page.goto(START_URL)

        # Poll for token cookie up to TIMEOUT_SECONDS
        deadline = time.time() + TIMEOUT_SECONDS
        token: Optional[str] = None
        while time.time() < deadline and not token:
            token = _find_token_cookie(ctx)
            if token:
                break
            time.sleep(1)

        if token:
            print(token)
            try:
                ctx.close()
            except Exception:
                pass
            return 0
        else:
            sys.stderr.write("Token not found. Complete login/OTP in the opened browser and retry.\n")
            try:
                ctx.close()
            except Exception:
                pass
            return 1


if __name__ == "__main__":
    raise SystemExit(main()) 