#!/usr/bin/env bash
# Applies patches/*.patch (numbered, in order) onto the Chromium checkout.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
cd "$SRC"
shopt -s nullglob
for p in "$ROOT"/patches/*.patch; do
  echo ">> $(basename "$p")"
  git am --3way "$p"
done
