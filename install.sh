#!/usr/bin/env bash
set -euo pipefail

# Portable installer for Pluxee MCP
# - Creates/updates a project-local venv
# - Installs Python deps and Playwright browsers
# - Creates ~/.local/bin/pluxee-mcp wrapper that points to this checkout

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
WRAPPER_DIR="$HOME/.local/bin"
WRAPPER_PATH="$WRAPPER_DIR/pluxee-mcp"

# Detect a suitable Python (prefer 3.12/3.11, then fall back)
PYTHON_BIN=""
for cand in python3.12 python3.11 python3 python; do
	if command -v "$cand" >/dev/null 2>&1; then
		PYTHON_BIN="$cand"
		break
	fi
done
if [[ -z "$PYTHON_BIN" ]]; then
	echo "Error: Python 3.11+ is required but none was found in PATH." >&2
	exit 1
fi

# Ensure venv
if [[ ! -d "$VENV_DIR" ]]; then
	"$PYTHON_BIN" -m venv "$VENV_DIR"
fi
PIP="$VENV_DIR/bin/pip"
PY="$VENV_DIR/bin/python"

# Upgrade pip and install dependencies
"$PIP" install -U pip
if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
	"$PIP" install -r "$PROJECT_ROOT/requirements.txt"
fi

# Ensure Playwright and browsers (user-level)
if ! "$PY" -c "import playwright" >/dev/null 2>&1; then
	"$PIP" install playwright
fi
"$VENV_DIR/bin/playwright" install

# Create wrapper in ~/.local/bin
mkdir -p "$WRAPPER_DIR"
cat > "$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$VENV_DIR/bin/python" "$PROJECT_ROOT/pluxee_mcp_server.py"
EOF
chmod +x "$WRAPPER_PATH"

echo "Wrapper created. Copy this path into your ~/.cursor/mcp.json 'command' field:"
echo "$WRAPPER_PATH"

# Suggest ready-to-copy global Cursor config
read -r -d '' SNIPPET <<JSON
{
  "mcpServers": {
    "pluxee": {
      "type": "stdio",
      "command": "$WRAPPER_PATH",
      "env": { "MCP_TRANSPORT": "stdio" },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
JSON

echo "\nSuggested ~/.cursor/mcp.json content (uses your absolute path):"
echo "$SNIPPET"

# Write example file for convenience
EXAMPLE_FILE="$PROJECT_ROOT/mcp.global.example.json"
echo "$SNIPPET" > "$EXAMPLE_FILE"
echo "Wrote example to: $EXAMPLE_FILE"

echo "Done. Configure Cursor to use either:"
echo "  - Command name (if ~/.local/bin is already on PATH): pluxee-mcp"
echo "  - Absolute path: $WRAPPER_PATH" 