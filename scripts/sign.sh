#!/usr/bin/env bash
# Usage: KEYSTORE=... KS_ALIAS=... [KS_PASS=...] scripts/sign.sh path/to.apk
# Without KS_PASS, apksigner prompts for the keystore password.
set -euo pipefail
APK="${1:?apk path}"
OUT="${APK%.apk}-signed.apk"
PASS_ARGS=()
if [ -n "${KS_PASS:-}" ]; then
  PASS_ARGS=(--ks-pass env:KS_PASS)
fi
apksigner sign --ks "${KEYSTORE:?}" --ks-key-alias "${KS_ALIAS:?}" \
  "${PASS_ARGS[@]}" --out "$OUT" "$APK"
apksigner verify "$OUT"
echo "Signed: $OUT"
