## Pluxee MCP Server

A minimal MCP server that exposes tools to interact with Pluxee (IL) APIs. It now runs as a plain Python script and includes an embedded login flow that acquires the Pluxee token via a local browser when needed.

<p align="center"><img src="assets/mascot.png" alt="Pluxee MCP Mascot" width="280"></p>

### Tools
- **get_budget_summary()**: Returns `{budget, budget_balance, cycle}` as JSON string.
- **get_orders_history(from_date, to_date)**: Returns orders between dates (format `DD/MM/YYYY`).
- **get_nearby_restaurants()**: Lists nearby restaurants using stored area hash. Returns restaurant data as JSON.
- **get_restaurant_menu(restaurant_id)**: Fetches menu tree for a specific restaurant. Returns menu data as JSON.
- **login()**: Opens a browser window to authenticate and capture the `token` cookie. Use this if the token is missing/expired.

### Prerequisites
- **Python 3.11+**
- **Playwright and browsers**: `pip install playwright` and then `playwright install`
- **Cursor** with MCP enabled

### Quick install (any machine, no sudo)
From the repo root, run the installer to set up a venv, install dependencies, install Playwright browsers, and create the `pluxee-mcp` wrapper in `~/.local/bin`:
```bash
./install.sh
# if not executable: bash install.sh
```
If the installer adds `~/.local/bin` to your PATH, restart your shell (or `source ~/.bashrc` / `~/.zshrc`).



**Important**:  After successful login, the token is cached in `~/.pluxee-profile/token` for reuse.

### Run with Cursor (global, any folder)
Create or edit `~/.cursor/mcp.json` to point at the `pluxee-mcp` wrapper created by the installer. This lets you open Cursor from any directory:
```json
{
  "mcpServers": {
    "pluxee": {
      "type": "stdio",
      "command": "pluxee-mcp",
      "env": { "MCP_TRANSPORT": "stdio" },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```
With this global config, you can keep or remove the project-local `/.cursor/mcp.json`. The global one will work from any folder.

### Troubleshooting
- **Playwright not installed**: Install with `pip install playwright` then `playwright install`.
- **Token not found**: Use the `login()` tool.
- **401 Unauthorized**: The server will prompt re-login by opening the browser once; if it persists, log out and log back in via `login()`.

### Security
- Do not commit tokens or secrets to the repo.
- Tokens are cached at `~/.pluxee-profile/token`. Delete this file to force re-login. 
