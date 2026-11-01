#!/usr/bin/env bash
# Usage: scripts/sync.sh [chromium-tag]   (defaults to ./CHROMIUM_VERSION)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-$(cat "$ROOT/CHROMIUM_VERSION")}"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
if [ ! -d "$SRC" ]; then
  mkdir -p "$(dirname "$SRC")" && cd "$(dirname "$SRC")"
  fetch --nohooks android
fi
cd "$SRC"
git fetch origin "refs/tags/$TAG:refs/tags/$TAG"
git checkout -B fork "tags/$TAG"
gclient sync -D --with_branch_heads --with_tags
