#!/usr/bin/env bash
# Usage: KEYSTORE=... KS_ALIAS=... scripts/sign.sh path/to.apk
set -euo pipefail
APK="${1:?apk path}"
apksigner sign --ks "${KEYSTORE:?}" --ks-key-alias "${KS_ALIAS:?}" \
  --out "${APK%.apk}-signed.apk" "$APK"
apksigner verify "${APK%.apk}-signed.apk"
