#!/usr/bin/env bash
# Usage: scripts/sync.sh <chromium-stable-tag>   e.g. 142.0.7444.xx
set -euo pipefail
TAG="${1:?chromium tag required}"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
if [ ! -d "$SRC" ]; then
  mkdir -p "$(dirname "$SRC")" && cd "$(dirname "$SRC")"
  fetch --nohooks android
fi
cd "$SRC"
git fetch origin "refs/tags/$TAG:refs/tags/$TAG"
git checkout -B fork "tags/$TAG"
gclient sync -D --with_branch_heads --with_tags
