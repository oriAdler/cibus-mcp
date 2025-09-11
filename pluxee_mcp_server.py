from typing import Any
import os
import json
from urllib.parse import quote
import httpx
from mcp.server.fastmcp import FastMCP

from helpers import (
    BASE_URL,
    build_headers,
    ensure_token,
    maybe_store_area_hash,
    AREA_HASH_FILE,
)

mcp = FastMCP("pluxee")

async def _headers() -> dict[str, str]:
    return await build_headers()

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
        info = r.json()
        try:
            await maybe_store_area_hash(info if isinstance(info, dict) else {})
        except Exception:
            pass
        return info

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

@mcp.tool()
async def get_nearby_restaurants(lang: str = "he") -> str:
    """List nearby restaurants using the stored area hash. Returns raw JSON string.
    If the area hash is missing, fetch user info to compute it, then retry.
    """
    await _get_user_info()  # ensures token and attempts to store area hash

    area_hash = os.environ.get("PLUXEE_AREA_HASH", "").strip()
    if not area_hash and AREA_HASH_FILE.exists():
        try:
            area_hash = AREA_HASH_FILE.read_text().strip()
        except Exception:
            area_hash = ""

    if not area_hash:
        return json.dumps({
            "error": "missing_area_hash",
            "message": "Area hash not found. Ensure you've logged in and that we could resolve your default address."
        })

    query = f"hash={quote(area_hash)}&lang={quote(lang)}"
    url = f"{BASE_URL}/api/rest_scan.py?{query}"
    headers = await _headers()
    headers["accept-language"] = lang
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 401:
            await ensure_token(force_refresh=True)
            r = await client.get(url, headers=headers)
        r.raise_for_status()
        return json.dumps(r.json())

@mcp.tool()
async def get_restaurant_menu(
    restaurant_id: int,
    lang: str = "he",
    order_type: int = 1,
    element_type_deep: int = 16,
) -> str:
    """Fetch menu tree for a specific restaurant. Returns raw JSON string.
    Uses user's company id and default address id automatically.
    """
    info = await _get_user_info()

    # Resolve company id
    comp_id: int | None = None
    for key in ("comp_id", "company_id"):
        v = info.get(key)
        if isinstance(v, int):
            comp_id = v
            break
        if isinstance(v, str) and v.isdigit():
            comp_id = int(v)
            break

    # Resolve address id (prefer default, then business/private)
    addr_id: int | None = None
    for key in ("default_addr_id", "biz_addr_id", "private_addr_id"):
        v = info.get(key)
        if isinstance(v, int) and v > 0:
            addr_id = v
            break

    if not comp_id or not addr_id:
        return json.dumps({
            "error": "missing_ids",
            "message": "Could not determine company or address id from user info. Please login and try again."
        })

    query = (
        f"restaurant_id={quote(str(restaurant_id))}"
        f"&comp_id={quote(str(comp_id))}"
        f"&order_type={quote(str(order_type))}"
        f"&element_type_deep={quote(str(element_type_deep))}"
        f"&lang={quote(lang)}"
        f"&address_id={quote(str(addr_id))}"
    )
    url = f"{BASE_URL}/api/rest_menu_tree.py?{query}"

    headers = await _headers()
    headers["accept-language"] = lang

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 401:
            await ensure_token(force_refresh=True)
            r = await client.get(url, headers=headers)
        r.raise_for_status()
        return json.dumps(r.json())

if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport) 