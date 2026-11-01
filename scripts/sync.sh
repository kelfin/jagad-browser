#!/usr/bin/env bash
# Check out Chromium at CHROMIUM_VERSION (or the given tag) in $CHROMIUM_SRC.
#
# Usage: scripts/sync.sh [--shallow] [--dry-run] [chromium-tag]
#   --shallow  no git history (CI: much faster, ~half the disk)
#   --dry-run  print the commands instead of running them
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHALLOW=0
DRY_RUN=0
TAG=""
for arg in "$@"; do
  case "$arg" in
    --shallow) SHALLOW=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) TAG="$arg" ;;
  esac
done
TAG="${TAG:-$(cat "$ROOT/CHROMIUM_VERSION")}"
SRC="${CHROMIUM_SRC:-$HOME/chromium/src}"
WORK="$(dirname "$SRC")"

run() {
  echo "+ $*"
  if [ "$DRY_RUN" = 0 ]; then "$@"; fi
}

if [ "$DRY_RUN" = 0 ]; then mkdir -p "$WORK"; fi
cd "$WORK" 2>/dev/null || true

if [ "$SHALLOW" = 1 ]; then
  if [ ! -d "$SRC" ]; then
    run fetch --nohooks --no-history android
  fi
  run gclient sync -D --no-history --nohooks --revision "src@refs/tags/$TAG"
  run gclient runhooks
else
  if [ ! -d "$SRC" ]; then
    run fetch --nohooks android
  fi
  run git -C "$SRC" fetch origin "refs/tags/$TAG:refs/tags/$TAG"
  run git -C "$SRC" checkout -B fork "tags/$TAG"
  run gclient sync -D --with_branch_heads --with_tags
fi
