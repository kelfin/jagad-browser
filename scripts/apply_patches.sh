#!/usr/bin/env bash
# Applies the patches listed in patches/series, in order, onto the Chromium checkout.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
cd "$SRC"
while IFS= read -r line || [ -n "$line" ]; do
  p="${line%%#*}"
  p="$(echo "$p" | xargs)"
  [ -z "$p" ] && continue
  echo ">> $p"
  git am --3way "$ROOT/patches/$p"
done < "$ROOT/patches/series"
