#!/bin/zsh
set -euo pipefail

SOURCE_DIR="${0:A:h:h}"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/skills/tech-company-report-ppt"
VALIDATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to install the vendored editppt runtime" >&2
  exit 2
fi
uv tool install --force --editable "$SOURCE_DIR/cli/editppt"
EDITPPT_PYTHON="$HOME/.local/share/uv/tools/image-to-editable-ppt-cli/bin/python"
"$EDITPPT_PYTHON" "$VALIDATOR" "$SOURCE_DIR"
python3 "$SOURCE_DIR/scripts/huawei_ppt.py" doctor

TEMP_LINK="${TARGET_DIR}.new.$$"
ln -s "$SOURCE_DIR" "$TEMP_LINK"
if [[ -e "$TARGET_DIR" || -L "$TARGET_DIR" ]]; then
  BACKUP="${TARGET_DIR}.backup.$(date +%Y%m%d%H%M%S)"
  mv "$TARGET_DIR" "$BACKUP"
fi
mv "$TEMP_LINK" "$TARGET_DIR"
echo "Installed: $TARGET_DIR -> $SOURCE_DIR"
