## Pluxee MCP Server

![Pluxee MCP Mascot](assets/mascot.png)

A minimal MCP server that exposes tools to interact with Pluxee (IL) APIs. It now runs as a plain Python script and includes an embedded login flow that acquires the Pluxee token via a local browser when needed.

### Tools
- **get_budget_summary()**: Returns `{budget, budget_balance, cycle}` as JSON string.
- **get_orders_history(from_date, to_date)**: Returns orders between dates (format `DD/MM/YYYY`).
- **login()**: Opens a browser window to authenticate and capture the `token` cookie. Use this if the token is missing/expired.

### Prerequisites
- **Python 3.11+**
- **Playwright and browsers**: `pip install playwright` and then `playwright install`
- **Cursor** with MCP enabled

### Setup (one-time)
From the repo root:
```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
# Playwright needs browser binaries
./.venv/bin/playwright install
```

### Run with Cursor
`/.cursor/mcp.json` is configured to use the venv Python directly:
```json
{
  "mcpServers": {
    "pluxee": {
      "type": "stdio",
      "command": "./.venv/bin/python",
      "args": ["pluxee_mcp_server.py"],
      "env": { "MCP_TRANSPORT": "stdio" },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```
**Important**: Open Cursor from this project folder (repo root) so the relative venv path (`./.venv/bin/python`) resolves. On first use of any tool, if no token is available, the server will open a browser window to let you log in. After successful login, the token is cached in `~/.pluxee-profile/token` for reuse.

### Troubleshooting
- **Playwright not installed**: Install with `pip install playwright` then `playwright install`.
- **Token not found**: Use the `login()` tool.
- **401 Unauthorized**: The server will prompt re-login by opening the browser once; if it persists, log out and log back in via `login()`.

### Security
- Do not commit tokens or secrets to the repo.
- Tokens are cached at `~/.pluxee-profile/token`. Delete this file to force re-login. 
