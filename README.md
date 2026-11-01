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
| `args/tabs9u.gn` | GN build settings for the Tab S9 Ultra |
| `patches/series` | Patch order; `patches/NNNN-*.patch` are `git am` patches |
| `patches/STATUS.md` | What each patch does, its tests and its risk, plus items already upstream or deferred |
| `tools/shadow.py` | Checks and writes patches against the real Chromium files, without a full checkout |
| `tools/build_ruleset.py` | Builds the bundled EasyList/EasyPrivacy adblock ruleset |
| `scripts/` | sync, apply patches, build, sign |
| `tests/` | pytest suite (runs in CI on every push) |

## Develop without a Chromium checkout
```bash
python3 tools/shadow.py check                 # every patch applies to CHROMIUM_VERSION
pip install pytest shellcheck-py && pytest tests
python3 tools/shadow.py start path/to/file.cc  # work tree in .shadow/work, series applied
# ...edit files in .shadow/work...
python3 tools/shadow.py finish Jagad-my-change "Jagad: my change"
```

## Build (needs a real build host)
You need Linux x86_64 with 32+ cores, 64 GB RAM, about 300 GB of free disk, and
[depot_tools](https://chromium.googlesource.com/chromium/tools/depot_tools) on `PATH`.

```bash
export CHROMIUM_SRC=$HOME/chromium/src
scripts/sync.sh            # checks out CHROMIUM_VERSION
scripts/apply_patches.sh
scripts/build.sh           # also generates the adblock ruleset
KEYSTORE=~/jagad.jks KS_ALIAS=jagad scripts/sign.sh $CHROMIUM_SRC/out/TabS9U/apks/ChromePublic.apk
adb install -r $CHROMIUM_SRC/out/TabS9U/apks/ChromePublic-signed.apk
```
Or run the `build` workflow on a self-hosted runner labelled `chromium`.

## Installing uBlock Origin
- **uBlock Origin Lite (MV3):** install from the Chrome Web Store.
- **Full uBlock Origin (MV2, kept working by patch 0002):** download `uBlock0_*.chromium.zip` from the uBlock Origin GitHub releases and unzip it, for example with Samsung My Files. Then open `chrome://extensions`, turn on Developer mode, tap **Load unpacked** and pick the folder.

## Patches
See [patches/STATUS.md](patches/STATUS.md). The patches apply cleanly but **haven't been compiled yet**.
