from __future__ import annotations
from typing import Any, Optional
import os
import json
import asyncio
import time
from pathlib import Path
import httpx

# Constants and shared state
BASE_URL: str = os.environ.get("PLUXEE_BASE_URL", "https://api.consumers.pluxee.co.il")
APPLICATION_ID: str = os.environ.get(
    "PLUXEE_APPLICATION_ID", "E5D5FEF5-A05E-4C64-AEBA-BA0CECA0E402"
)
PROFILE_DIR: Path = Path.home() / ".pluxee-profile"
TOKEN_FILE: Path = PROFILE_DIR / "token"
AREA_HASH_FILE: Path = PROFILE_DIR / "area_hash"
START_URL: str = "https://consumers.pluxee.co.il/"
COOKIE_DOMAINS: list[str] = [
    "https://api.consumers.pluxee.co.il",
    "https://consumers.pluxee.co.il",
]
TIMEOUT_SECONDS: int = 180

# Runtime variables (in-process), also mirrored to environment when set
TOKEN: str = os.environ.get("PLUXEE_TOKEN", "")
AREA_HASH: str = os.environ.get("PLUXEE_AREA_HASH", "")


async def build_headers() -> dict[str, str]:
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json; charset=utf-8",
        "application-id": APPLICATION_ID,
        "origin": "https://consumers.pluxee.co.il",
        "referer": "https://consumers.pluxee.co.il/",
    }
    if TOKEN:
        headers["cookie"] = f"token={TOKEN}"
    return headers


def _find_token_cookie_sync(context) -> Optional[str]:
    for domain in COOKIE_DOMAINS:
        try:
            for c in context.cookies(domain):
                if c.get("name") == "token" and c.get("value"):
                    return c.get("value")
        except Exception:
            pass
    return None


async def _obtain_token_via_playwright() -> str:
    def _sync_flow() -> str:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            raise RuntimeError(
                "Playwright not installed. Install with: pip install playwright && playwright install"
            )
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(str(PROFILE_DIR), headless=False)
            try:
                page = ctx.new_page()
                page.goto(START_URL)
                deadline = time.time() + TIMEOUT_SECONDS
                token: Optional[str] = None
                while time.time() < deadline and not token:
                    token = _find_token_cookie_sync(ctx)
                    if token:
                        break
                    time.sleep(1)
                if not token:
                    raise RuntimeError(
                        "Token not found. Complete login/OTP in the opened browser and retry."
                    )
                return token
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass

    return await asyncio.to_thread(_sync_flow)


async def ensure_token(force_refresh: bool = False) -> str:
    global TOKEN
    if not force_refresh and TOKEN:
        return TOKEN

    # 1) Env var
    env_token = os.environ.get("PLUXEE_TOKEN", "").strip()
    if env_token and not force_refresh:
        TOKEN = env_token
        return TOKEN

    # 2) Persisted file
    if TOKEN_FILE.exists() and not force_refresh:
        try:
            file_token = TOKEN_FILE.read_text().strip()
            if file_token:
                TOKEN = file_token
                return TOKEN
        except Exception:
            pass

    # 3) Interactive login via Playwright
    new_token = await _obtain_token_via_playwright()
    TOKEN = new_token
    try:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(TOKEN)
    except Exception:
        # Non-fatal if we cannot persist
        pass
    return TOKEN


async def maybe_store_area_hash(user_info: dict[str, Any]) -> None:
    """Populate AREA_HASH once: env → file → compute via main.py(rest_scan)."""
    global AREA_HASH
    if AREA_HASH:
        return

    # Try persisted file
    if AREA_HASH_FILE.exists():
        try:
            file_hash = AREA_HASH_FILE.read_text().strip()
            if file_hash:
                AREA_HASH = file_hash
                os.environ["PLUXEE_AREA_HASH"] = AREA_HASH
                return
        except Exception:
            pass

    # Resolve address id from user info
    addr_id = None
    for key in ("default_addr_id", "biz_addr_id", "private_addr_id"):
        v = user_info.get(key)
        if isinstance(v, int) and v > 0:
            addr_id = v
            break
    if not addr_id:
        return

    payload = {
        "addr_id": addr_id,
        "order_type": 1,
        "radius": 9000,
        "type": "rest_scan",
        "get_hash": True,
        "has_15mins_grace": 0,
    }
    url = f"{BASE_URL}/api/main.py"
    headers = await build_headers()
    headers["accept-language"] = user_info.get("default_lang", "he")

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code == 401:
            await ensure_token(force_refresh=True)
            r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        try:
            data = r.json()
            if isinstance(data, dict):
                h = data.get("hash") or data.get("area_hash")
                if h:
                    AREA_HASH = str(h)
                    os.environ["PLUXEE_AREA_HASH"] = AREA_HASH
                    try:
                        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
                        AREA_HASH_FILE.write_text(AREA_HASH)
                    except Exception:
                        pass
        except Exception:
            pass 