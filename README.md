# Jagad

Jagad is a Chromium-based Android browser tuned for the **Galaxy Tab S9 Ultra**, with:
- extension support (uBlock Origin Lite now; full uBlock Origin as a stretch goal)
- autofill from the Android password manager (Google, Samsung Pass, Bitwarden) and passkeys
- a tablet-first interface (desktop mode, keyboard, S Pen, split view)

Tracks Chromium **156.0.8078.79** (see `CHROMIUM_VERSION`). The full plan is in [docs/ROADMAP.md](docs/ROADMAP.md).

## Layout
| Path | What |
|---|---|
| `CHROMIUM_VERSION` | Chromium tag the patches target |
| `args/tabs9u.gn` | GN build args for the Tab S9 Ultra |
| `patches/` | Numbered `git am` patches applied on top of Chromium |
| `branding/` | Icons (todo) |
| `scripts/` | sync, apply patches, build, sign |

## Build
You need a Linux x86_64 host with 16+ cores, 64 GB RAM, ~300 GB free disk and
[depot_tools](https://chromium.googlesource.com/chromium/tools/depot_tools) on `PATH`.

```bash
export CHROMIUM_SRC=$HOME/chromium/src
scripts/sync.sh            # checks out CHROMIUM_VERSION
scripts/apply_patches.sh
scripts/build.sh
KEYSTORE=~/jagad.jks KS_ALIAS=jagad scripts/sign.sh $CHROMIUM_SRC/out/TabS9U/apks/ChromePublic.apk
adb install -r $CHROMIUM_SRC/out/TabS9U/apks/ChromePublic-signed.apk
```

## Patches
| # | Patch | Status |
|---|---|---|
| 0001 | Product name → Jagad | applies cleanly to 156.0.8078.79 (not yet build-tested) |
