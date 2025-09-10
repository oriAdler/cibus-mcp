from typing import Any, Optional
import os
import json
import asyncio
import time
from pathlib import Path
from urllib.parse import quote
import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("PLUXEE_BASE_URL", "https://api.consumers.pluxee.co.il")
TOKEN: str = os.environ.get("PLUXEE_TOKEN", "")

PROFILE_DIR = Path.home() / ".pluxee-profile"
START_URL = "https://consumers.pluxee.co.il/"
COOKIE_DOMAINS = [
    "https://api.consumers.pluxee.co.il",
    "https://consumers.pluxee.co.il",
]
TIMEOUT_SECONDS = 180

mcp = FastMCP("pluxee")

async def _headers() -> dict[str, str]:
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json; charset=utf-8",
        "application-id": "E5D5FEF5-A05E-4C64-AEBA-BA0CECA0E402",
        "origin": "https://consumers.pluxee.co.il",
        "referer": "https://consumers.pluxee.co.il/",
    }
    if TOKEN:
        headers["cookie"] = f"token={TOKEN}"
    return headers

# Token acquisition helpers

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
    token_file = PROFILE_DIR / "token"
    if token_file.exists() and not force_refresh:
        try:
            file_token = token_file.read_text().strip()
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
        token_file.write_text(TOKEN)
    except Exception:
        # Non-fatal if we cannot persist
        pass
    return TOKEN

@mcp.tool()
async def login() -> str:
    """Open a browser to log in and acquire a token. Returns a short status message."""
    await ensure_token(force_refresh=True)
    return "Login successful and token acquired."

async def _get_user_info() -> dict[str, Any]:
    await ensure_token()
    url = f"{BASE_URL}/api/prx_user_info.py?version=0"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=await _headers())
        if r.status_code == 401:
            # Try one refresh cycle, then fail
            await ensure_token(force_refresh=True)
            r = await client.get(url, headers=await _headers())
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def get_budget_summary() -> str:
    """Return budget summary as JSON string: {budget,budget_balance,cycle}."""
    info = await _get_user_info()
    summary = {
        "budget": info.get("budget"),
        "budget_balance": info.get("budget_balance"),
        "cycle": info.get("cycle"),
    }
    return json.dumps(summary)

@mcp.tool()
async def get_orders_history(from_date: str, to_date: str) -> str:
    """Return user's order history between from_date and to_date (format DD/MM/YYYY)."""
    await ensure_token()
    url = f"{BASE_URL}/api/main.py"
    payload = {"from_date": from_date, "to_date": to_date, "type": "prx_user_deals"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=await _headers(), json=payload)
        if r.status_code == 401:
            await ensure_token(force_refresh=True)
            r = await client.post(url, headers=await _headers(), json=payload)
        r.raise_for_status()
        return json.dumps(r.json())

if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport) 