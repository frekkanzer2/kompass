#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="Kompass"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"
REQ_FILE="requirements/dev.txt"
MCP_CFG_FILE="mcp.config.json"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "===== ${PROJECT_NAME} installer ====="

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "ERR > ${PYTHON_BIN} not found into PATH." >&2
  exit 1
}

if [ ! -d "$VENV_DIR" ]; then
  echo "INFO > Creating virtualenv in ${VENV_DIR}"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "INFO > Detected existing virtualenv ${VENV_DIR}, skipping creation"
fi

source "${VENV_DIR}/bin/activate"

echo "INFO > Updating pip"
pip install --upgrade pip
echo

if [ -f "$REQ_FILE" ]; then
  echo "INFO > Installing dependencies from ${REQ_FILE}"
  pip install -r "$REQ_FILE"
  echo
else
  echo "ALERT > ${REQ_FILE} file not found, skipping dependencies installation"
fi


VENV_PYTHON="${PROJECT_DIR}/${VENV_DIR}/bin/python"
MAIN_PY="${PROJECT_DIR}/main.py"

echo "INFO > Generating MCP configuration file in config folder"
mkdir -p "${PROJECT_DIR}"/config
cat > "${PROJECT_DIR}/config/${MCP_CFG_FILE}" <<EOF
{
  "mcpServers": {
    "kompass": {
      "command": "${VENV_PYTHON}",
      "args": ["${MAIN_PY}"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
EOF

echo "INFO > Installation completed successfully!"