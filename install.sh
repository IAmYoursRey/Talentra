#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:?Usage: ./install.sh /path/to/talentra}"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TARGET"

for item in GEMINI.md .agents TALENTRA; do
  src="$SOURCE/$item"
  dst="$TARGET/$item"
  if [ -e "$dst" ]; then
    echo "Backing up $dst -> $dst.backup-$STAMP"
    mv "$dst" "$dst.backup-$STAMP"
  fi
  cp -R "$src" "$dst"
done

echo "TALENTRA Antigravity kit installed into $TARGET"
echo "Reopen Antigravity and select 'talentra-orchestrator'."
