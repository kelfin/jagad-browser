# Jagad roadmap: Chromium fork for Android, tuned for the Galaxy Tab S9 Ultra

> **Progress (Nov 2026):** the patches for Phases 0–4 are written and apply cleanly to 156.0.8078.79. They haven't been compiled yet.
> For what is done, what was already upstream and what is deferred, see [patches/STATUS.md](../patches/STATUS.md).

## Context
The goal is a personal Chromium-based Android browser that:
1. is built and tuned for the Galaxy Tab S9 Ultra (Snapdragon 8 Gen 2 "for Galaxy", Adreno 740, 12–16 GB RAM, 14.6" 2960×1848 120 Hz OLED, S Pen, DeX, Android 14+/One UI);
2. can install extensions, especially **uBlock Origin**;
3. works with the **Android password manager**: Google Password Manager, Samsung Pass, Bitwarden and other apps, through Android Autofill and Credential Manager.

The working directory is empty, so this is a roadmap from scratch, not a change to existing code.

### Three things to know before starting
- **Extensions on Android:** Upstream Chromium now has a "desktop Android" build (`is_desktop_android = true` in GN). It compiles the desktop extensions system for Android and is under active development. Build on this instead of porting Kiwi's old, now-unmaintained extension patches. Fall back to the Kiwi or Edge-Canary approach only if upstream is missing something you need.
- **uBlock Origin is a Manifest V2 extension, and upstream Chromium removed MV2 support (around M138–139).** You have two options:
  - (a) Keep MV2 alive with a maintained patch set. Projects such as Helium, Supermium and ungoogled-chromium carry these. Expect to rebase them every release.
  - (b) Ship **uBlock Origin Lite** (the MV3 version) plus a built-in network-level adblock engine.
  - **Recommendation:** do (b) first because it is reliable, then add (a) as a stretch goal so full uBO keeps working.
- **Password manager:** A fork **cannot** use Chrome's built-in Google Password Manager integration. It depends on Google-signed GMS APIs and Google API keys. It **can** use:
  - the **Android Autofill framework** (Chromium's "Autofill using another service" mode, built on `components/android_autofill`). This covers Google, Samsung Pass, Bitwarden, 1Password and similar apps.
  - **Android Credential Manager**, for passkeys and WebAuthn.

## Build environment (prerequisite)
- Use a Linux x86_64 build host with at least 16 cores (32+ is better), 64 GB RAM and 300 GB+ of NVMe storage. A first build takes hours, and incremental builds take minutes. This cloud container is not suitable, so use your own workstation or a cloud VM.
- Get the source with `depot_tools`, `fetch --nohooks android`, `gclient sync`, then `build/install-build-deps.sh --android`.
- **Pin the source to a Stable release tag** (currently 156.0.8078.79, see `CHROMIUM_VERSION`) and rebase every 4 weeks. Keep your changes as a **patch series** in your own repo, as Cromite and Bromite do, not as a long-lived fork branch. Rebasing patches is much easier.

## Phase 0 — Baseline build (week 1–2)
- Use these `args.gn` settings:
  ```
  target_os = "android"
  target_cpu = "arm64"
  is_official_build = true
  is_debug = false
  symbol_level = 1
  is_desktop_android = true        # enables extensions
  proprietary_codecs = true
  ffmpeg_branding = "Chrome"
  enable_nacl = false
  chrome_pgo_phase = 2             # use upstream PGO profiles
  use_thin_lto = true
  android_channel = "stable"
  system_webview_package_name = "" # don't build WebView
  google_api_key = "" google_default_client_id = "" google_default_client_secret = ""
  ```
- Build `chrome_public_bundle` or `chrome_public_apk`. Sign it with your own keystore and install it with `adb install`.
- Change the package name to `com.kelfin.jagad` via `chrome_public_manifest_package`, and the branding so it installs alongside Chrome.
- **Done when:** the browser launches on the tablet and you can install a CRX or unpacked extension.

## Phase 1 — Extensions + uBlock (week 2–4)
- Check that the extensions page, the Chrome Web Store install flow and loading unpacked extensions or CRX files work on the desktop-Android build. If installing from the Web Store is blocked, patch the Web Store install allow-list or add a "Load CRX from file" UI.
- Ship **uBO Lite** and test it on uBO's test pages and on real sites.
- Add a **built-in adblock engine** as a safety net. Options are Brave's `adblock-rust` component (it builds with Chromium's Rust toolchain), or Cromite's patched subresource-filter with EasyList and uBO filter lists.
- Stretch goal: port an **MV2 keep-alive patch set** so full uBO with dynamic filtering and the element picker runs.
- Add a toolbar extension menu (puzzle icon) and pin uBO next to the address bar.

## Phase 2 — Password manager & autofill (week 4–5)
- Set the default to "Autofill using another service" so Android Autofill is used. Test it with Google (through Autofill), Samsung Pass and Bitwarden on login, sign-up and change-password forms.
- Enable WebAuthn/passkeys through Android Credential Manager on Android 14+, and test passkey login on Google, GitHub and passkeys.io.
- Remove or hide the internal Google-account password-save prompts, which don't work in a fork, so users don't get two prompts for the same form.
- **Done when:** login fields show the Samsung Pass or Google suggestion strip and the keyboard inline suggestions, and saving a new password goes to the system password manager.

## Phase 3 — Tab S9 Ultra performance tuning (week 5–7)
- **CPU:** compile for `armv8.2-a+dotprod+fp16`, with tuning for Cortex-A715 or X3. The SoC mixes X3, A715, A710 and A510 cores, so don't use `-march=armv9` flags the A510 cluster may reject. Measure the effect; don't assume a gain.
- **GPU:** enable Vulkan for Skia Graphite and ANGLE if they are stable on Adreno 740, and keep GL as a fallback. Check `chrome://gpu`.
- **Display:** make sure scrolling runs at 120 Hz and the VRR/frame-rate hints work. Check scrolling smoothness with Perfetto.
- **Memory:** with 12–16 GB of RAM you can raise the number of live renderers and loosen tab discarding and low-memory thresholds, so background tabs aren't reloaded. Add a setting for this.
- **Startup:** use the upstream PGO profile plus an Android baseline profile, and remove unused components (Feed, NTP suggestions, Google sign-in, Lens).
- **Benchmarks:** compare against stock Chrome on Speedometer 3, JetStream 2, MotionMark, cold start time and memory with 30 tabs open.

## Phase 4 — Tablet-first features (week 7+)
These are the features most worth adding, highest value first:
1. **Desktop mode by default** with a per-site override, since the 14.6" screen fits desktop layouts.
2. **Desktop-style tab strip** with tab groups, plus optional **vertical tabs** in a side panel.
3. **Full keyboard and trackpad support** (Book Cover Keyboard): desktop shortcuts (Ctrl+T/W/L/Tab, Ctrl+Shift+T), right-click context menus, hover states.
4. **S Pen:** hover previews, pen-button gestures (back or new tab), and handwriting input in text fields (One UI already provides some of this, so check before adding).
5. **Split view inside the browser:** two tabs side by side, which fits the 16:10 screen. Also support Android multi-window and DeX resizing.
6. **Side panel:** reading list, bookmarks, history and extension side panels, as on desktop.
7. **Background media playback** and picture-in-picture for any video.
8. **Reader mode** and a text-reflow zoom setting.
9. **Privacy hardening patches**, taken from Cromite or ungoogled-chromium: no Google services, fingerprinting mitigations, DoH by default, clear data on exit.
10. **Sync without Google:** export and import of bookmarks and passwords, or a self-hosted option later (for example a WebDAV bookmark sync extension).
11. **Gesture navigation:** swipe between tabs, and pull to refresh as a setting.

## Phase 5 — Maintenance & distribution (ongoing)
- Set up CI on your build host (or a GitHub Actions self-hosted runner) to rebase patches, build and sign each Stable release.
- Publish APKs as GitHub Releases and install updates with **Obtainium**. Add an optional in-app update check.
- Security: track Chromium Stable security releases (roughly weekly) and rebuild quickly. A browser that falls behind on patches is a security risk, so this matters more than features.

## Repo layout to create
```
jagad-browser/
  patches/            # numbered .patch series applied on top of a Chromium tag
  args/tabs9u.gn      # build config above
  branding/           # icons, strings, package name
  scripts/            # sync.sh, apply_patches.sh, build.sh, sign.sh
  docs/ROADMAP.md
```

## Verification
- Install with `adb install` on the Tab S9 Ultra, then check `chrome://version`, `chrome://gpu` and `chrome://extensions`.
- uBO or uBO Lite blocks ads on its test pages; the built-in engine works with the extension disabled.
- Samsung Pass, Google and Bitwarden autofill appear on login forms, and passkey login works.
- Benchmarks and Perfetto traces are at least as good as stock Chrome on the same device.
- The browser keeps working after a Stable rebase, which shows the patch series rebases cleanly.
