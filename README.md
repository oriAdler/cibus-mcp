## Pluxee MCP Server

A minimal MCP server that exposes tools to interact with Pluxee (IL) APIs. It now runs as a plain Python script and includes an embedded login flow that acquires the Pluxee token via a local browser when needed.

<p align="center"><img src="assets/mascot.png" alt="Pluxee MCP Mascot" width="280"></p>

### Tools
- 💰 **get_budget_summary()**: Budget & balance info
- 📋 **get_orders_history(from_date, to_date)**: Order history (`DD/MM/YYYY`)
- 🏪 **get_nearby_restaurants()**: Nearby restaurants list
- 🍽️ **get_restaurant_menu(restaurant_id)**: Restaurant menu data
- 🔐 **login()**: Browser auth for token

### Prerequisites
- 🐍 **Python 3.11+**
- 🎭 **Playwright**: Already installed by the installer. If you skip `install.sh`, run: `pip install playwright && playwright install`
- 🖥️ **Cursor** or **Claude Code** with MCP enabled

### Quick install (Linux/macOS, no sudo)
From the repo root, run the installer to set up a venv, install dependencies, install Playwright browsers, and create the `pluxee-mcp` wrapper in `~/.local/bin`:
```bash
./install.sh
# if not executable: bash install.sh
```

### Run with Claude Code
After running the installer, you can add the server to Claude Code:
```bash
claude mcp add pluxee --scope user $HOME/.local/bin/pluxee-mcp
```
Verify it's connected:
```bash
claude mcp list
```

### Run with Cursor (global, any folder)
Create or edit `~/.cursor/mcp.json` and set `command` to the absolute path that the installer printed (line starting with `Absolute path:`). You can also print it any time with:
```bash
echo "$HOME/.local/bin/pluxee-mcp"
```
The installer also wrote a ready-to-copy example at `mcp.global.example.json`.

Use this structure, replacing the command value with your absolute path:
```json
{
  "mcpServers": {
    "pluxee": {
      "type": "stdio",
      "command": "<ABSOLUTE_PATH_FROM_INSTALLER>",
      "env": { "MCP_TRANSPORT": "stdio" },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```
Alternative if `~/.local/bin` is already on PATH:
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

### Troubleshooting
- **Playwright not installed**: Install with `pip install playwright` then `playwright install`.
- **Token not found**: Use the `login()` tool.
- **401 Unauthorized**: The server will prompt re-login by opening the browser once; if it persists, log out and log back in via `login()`.

### Security
- Do not commit tokens or secrets to the repo.
- Tokens are cached at `~/.pluxee-profile/token`. Delete this file to force re-login. 
