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

## Build on GitHub (larger runner)
Chromium needs ~150 GB of disk and 64 GB of RAM, so Jagad is built by the
`build` workflow on a GitHub **larger runner**.

**One-time setup**
1. Larger runners are only available to **organizations** on GitHub Team or Enterprise Cloud.
   Create an organization, choose the Team plan, and transfer this repository to it
   (Repository → Settings → Transfer).
2. In the organization, go to Settings → Actions → Runners → **New runner** → *New GitHub-hosted runner*.
   Pick **Ubuntu, 64-core** (256 GB RAM, ~2 TB SSD) and set its name/label to `jagad-64core`.
   Give this repository access to it. You pay per minute; a first build takes roughly 2–4 hours.
3. Create the signing key on your own computer. It needs a JDK.
   ```bash
   scripts/make_keystore.sh ~/jagad.jks
   ```
   Then add the three secrets it prints under Repository → Settings → Secrets and variables → Actions.
   **Back up `~/jagad.jks` and its password.** Every update must be signed with the same key.

**Each build**
- Go to Actions → **build** → *Run workflow*.
  - `profile=official` gives the release build.
  - If it hits GitHub's 6-hour limit, run once with `profile=fast`, which skips LTO and PGO.
- When the run finishes, download the **jagad-apk** artifact, or turn on `release` to publish it as a GitHub Release.
- Install it:
  ```bash
  adb install -r Jagad-156.0.8078.79.apk
  ```
  You can also open the APK on the tablet.
- If the build fails, download **jagad-build-logs** and share `build.log`, and the patches will be fixed.

The same workflow runs on a self-hosted machine instead (any Linux x86_64 with 32+ cores, 64 GB RAM and 300 GB disk).
Register it as a runner and enter its label in `runner_label`.

## Build locally
```bash
export CHROMIUM_SRC=$HOME/chromium/src
scripts/sync.sh --shallow  # checks out CHROMIUM_VERSION without git history
"$CHROMIUM_SRC/build/install-build-deps.sh" --android
scripts/apply_patches.sh
scripts/build.sh           # also generates the adblock ruleset
KEYSTORE=~/jagad.jks KS_ALIAS=jagad scripts/sign.sh $CHROMIUM_SRC/out/TabS9U/apks/ChromePublic.apk
```

## Installing uBlock Origin
- **uBlock Origin Lite (MV3):** install from the Chrome Web Store.
- **Full uBlock Origin (MV2, kept working by patch 0002):** download `uBlock0_*.chromium.zip` from the uBlock Origin GitHub releases and unzip it, for example with Samsung My Files. Then open `chrome://extensions`, turn on Developer mode, tap **Load unpacked** and pick the folder.

## Patches
See [patches/STATUS.md](patches/STATUS.md). The patches apply cleanly but **haven't been compiled yet**.
