#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/new_plugin.sh <plugin_id> <plugin_kind>
#
# Example:
#   bash scripts/new_plugin.sh my_custom_ranker ranker

PLUGIN_ID="${1:-}"
PLUGIN_KIND="${2:-}"

if [[ -z "${PLUGIN_ID}" || -z "${PLUGIN_KIND}" ]]; then
  echo "Usage: bash scripts/new_plugin.sh <plugin_id> <plugin_kind>"
  exit 1
fi

BASE_DIR="backend/components/plugins/${PLUGIN_ID}"

if [[ -d "${BASE_DIR}" ]]; then
  echo "Error: plugin folder already exists: ${BASE_DIR}"
  exit 1
fi

mkdir -p "${BASE_DIR}"
touch "${BASE_DIR}/__init__.py"

cat > "${BASE_DIR}/plugin.py" <<PYEOF
# backend/components/plugins/${PLUGIN_ID}/plugin.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import PluginContext
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "${PLUGIN_ID}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "${PLUGIN_KIND}"
REQUIRES: list[str] = []
OPTIONAL = False


def register(container: KernelAppContainer, context: PluginContext) -> None:
    \"\"\"
    TODO:
    - create/register your component here
    - do not modify kernel internals
    \"\"\"
    pass
PYEOF

cat > "${BASE_DIR}/plugin.json" <<JSONEOF
{
  "plugin_id": "${PLUGIN_ID}",
  "version": "1.0.0",
  "kind": "${PLUGIN_KIND}",
  "requires": [],
  "optional": false,
  "sdk_version": "1.0",
  "entry_module": "backend.components.plugins.${PLUGIN_ID}.plugin",
  "entry_callable": "register"
}
JSONEOF

echo "Created plugin scaffold at: ${BASE_DIR}"
echo "Next steps:"
echo "1) implement register() in ${BASE_DIR}/plugin.py"
echo "2) validate SDK: python -m pytest tests/app/test_plugin_sdk_contract.py -v"
