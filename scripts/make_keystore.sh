#!/usr/bin/env bash
# Create the Jagad signing keystore (run once, on your own computer).
#
# Usage: scripts/make_keystore.sh [path/to/jagad.jks] [alias]
#
# Keep the .jks file and its password safe: every Jagad update must be signed
# with the same key, or Android will refuse to install it over the old one.
# Never commit the keystore to git.
set -euo pipefail
KS="${1:-$HOME/jagad.jks}"
ALIAS="${2:-jagad}"

if [ -e "$KS" ]; then
  echo "$KS already exists; refusing to overwrite it." >&2
  exit 1
fi
command -v keytool >/dev/null || { echo "keytool not found (install a JDK)" >&2; exit 1; }

keytool -genkeypair -v -keystore "$KS" -alias "$ALIAS" \
  -keyalg RSA -keysize 4096 -validity 10000 \
  -dname "CN=Jagad, O=Jagad Browser"

B64="$KS.base64.txt"
base64 -w0 "$KS" > "$B64"
chmod 600 "$KS" "$B64"

cat <<EOF

Keystore created: $KS
Add these repository secrets (Settings > Secrets and variables > Actions):
  JAGAD_KEYSTORE_B64        contents of $B64
  JAGAD_KEY_ALIAS           $ALIAS
  JAGAD_KEYSTORE_PASSWORD   the password you just typed
Then delete $B64.
EOF
