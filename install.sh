#!/usr/bin/env bash
set -euo pipefail

# Portable installer for Pluxee MCP
# - Creates/updates a project-local venv
# - Installs Python deps and Playwright browsers
# - Creates ~/.local/bin/pluxee-mcp wrapper that points to this checkout
# - Ensures ~/.local/bin is on PATH (for current shell in future sessions)

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

echo "Created wrapper: $WRAPPER_PATH"

# Ensure ~/.local/bin on PATH for future shells
if ! echo ":$PATH:" | grep -q ":$HOME/.local/bin:"; then
	SHELL_NAME="$(basename "${SHELL:-bash}")"
	RC_FILE="$HOME/.bashrc"
	if [[ "$SHELL_NAME" == "zsh" ]]; then
		RC_FILE="$HOME/.zshrc"
	fi
	if [[ -f "$RC_FILE" ]]; then
		echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
		echo "Added ~/.local/bin to PATH in $RC_FILE. Restart your shell or run: source $RC_FILE"
	else
		# Fallback: create .bashrc if nothing suitable exists
		echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
		echo "Added ~/.local/bin to PATH in ~/.bashrc. Restart your shell or run: source ~/.bashrc"
	fi
fi

# Show where the command resolves now
if command -v pluxee-mcp >/dev/null 2>&1; then
	echo "pluxee-mcp is available at: $(command -v pluxee-mcp)"
else
	echo "Note: pluxee-mcp not yet on current PATH. After restarting your shell, it will be available."
fi

echo "Done. You can now configure Cursor globally to run 'pluxee-mcp' from any folder." 