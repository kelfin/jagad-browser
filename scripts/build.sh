#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
OUT=out/TabS9U
cd "$SRC"
# Bundled adblock ruleset (patch 0003) must exist before grit runs.
python3 "$ROOT/tools/build_ruleset.py" --src "$SRC"
mkdir -p "$OUT"
cp "$ROOT/args/tabs9u.gn" "$OUT/args.gn"
gn gen "$OUT"
autoninja -C "$OUT" chrome_public_apk
echo "APK: $SRC/$OUT/apks/ChromePublic.apk"
