#!/usr/bin/env bash
# Build Jagad (chrome_public_apk) in $CHROMIUM_SRC/out/TabS9U.
#
# Environment:
#   CHROMIUM_SRC      Chromium checkout (default ~/chromium/src)
#   JAGAD_ARGS_EXTRA  extra GN args appended to args/tabs9u.gn, e.g. for a
#                     faster trial build:
#                     "is_official_build=false use_thin_lto=false symbol_level=0"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
OUT=out/TabS9U
cd "$SRC"

# Bundled adblock ruleset (patch 0003) must exist before grit runs.
python3 "$ROOT/tools/build_ruleset.py" --src "$SRC"

mkdir -p "$OUT"
cp "$ROOT/args/tabs9u.gn" "$OUT/args.gn"
if [ -n "${JAGAD_ARGS_EXTRA:-}" ]; then
  {
    echo ""
    echo "# From JAGAD_ARGS_EXTRA"
    for kv in $JAGAD_ARGS_EXTRA; do echo "$kv"; done
  } >> "$OUT/args.gn"
fi
gn gen "$OUT"
gn args "$OUT" --list --short | grep -E '^jagad_' || true
autoninja -C "$OUT" chrome_public_apk
echo "APK: $SRC/$OUT/apks/ChromePublic.apk"
