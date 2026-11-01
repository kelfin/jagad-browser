# Patch status

All patches target Chromium **156.0.8078.79** (`CHROMIUM_VERSION`).

**What is verified:** every patch applies cleanly to the real Chromium source files at that tag (`tools/shadow.py check`, CI `check.yml`). The patch contents and the Jagad tools are covered by `pytest tests/`.

**What is not verified yet:** none of the patches has been compiled, and no Chromium unit test has run. That needs a full Chromium build host; see `build.yml`. Treat each patch as untested until the build is green.

| # | Patch | What it does | Chromium tests to run | Risk |
|---|---|---|---|---|
| 0001 | branding-product-name | Renames the app to "Jagad" (app name, widget titles, product name file) | build only | low |
| 0002 | keep-Manifest-V2-extensions | New switch `kJagadKeepManifestV2`, on by default. MV2 extensions (full uBlock Origin) are never blocked or disabled, and the deprecation warnings are hidden | `unit_tests --gtest_filter='ManifestV2Handler*'` | medium¹ |
| 0003 | built-in-adblock | New switch `kJagadAdblock`, on by default. Blocks ads on every site with a bundled EasyList/EasyPrivacy ruleset instead of Google's download | `components_unittests --gtest_filter='SubresourceFilterFeaturesTest.*'` | medium² |
| 0004 | default-to-Android-Autofill | Android Autofill (Samsung Pass, Google, Bitwarden) is the default; passkeys go through Credential Manager | `components_unittests --gtest_filter='AutofillProfilePrefsTest.*'` | low |
| 0005 | arm64-cpu-tuning-args | New `jagad_arm64_march` / `jagad_arm64_mtune` build settings | `gn desc out/TabS9U //base cflags` | low |
| 0006 | enable-Skia-Graphite-on-Android | Skia Graphite (Dawn/Vulkan) on by default | check `chrome://gpu` on device | medium³ |
| 0007 | keep-background-tabs-alive-on-high-RAM | On devices with 11 GB+ RAM, background tabs aren't dropped when Jagad goes to the background | `content_junit_tests -f 'BindingManagerTest#*'` | low |
| 0008 | trim-Google-sign-in-and-Feed | Google sign-in prompts and the Discover feed are off by default | build only | medium⁴ |
| 0009 | tablet-features-on-by-default | Turns on upstream vertical tabs, side panel, tab-switcher drag and drop, Ctrl+O, desktop bookmark/history layouts, and pinned tabs surviving "close all" | build + manual test | medium⁵ |
| 0010 | block-third-party-cookies-by-default | Third-party cookies blocked by default | build + manual test | low |
| 0011 | quiet-adblock-UI | No "Ads blocked" pop-up for the built-in blocker; Page Info still allows ads per site | build + manual test | low |

¹ Upstream tests that expect the "MV2 is deprecated" install warning for unpacked extensions may need updating, for example in `unpacked_installer_*test`. Run them with `--disable-features=JagadKeepManifestV2` to confirm.
² `scripts/build.sh` runs `tools/build_ruleset.py` first. Grit fails if `chrome/browser/resources/jagad/adblock_ruleset.dat` is missing. Whether all-sites activation works on a fork without Safe Browsing keys still needs checking on a device.
³ If rendering glitches appear, turn it off at `chrome://flags/#skia-graphite`.
⁴ Android instrumentation tests that sign in must set `signin.allowed=true`.
⁵ These are upstream features in development. Each can be turned off in `chrome://flags`.

## Roadmap items that need no patch (already upstream in 156)

- **Extensions on Android:** the `is_desktop_android = true` build setting enables the full extension system: toolbar, menu, install dialog, `chrome://extensions`, Load unpacked (folder picker), and drag-and-drop of `.crx`/`.zip` in developer mode.
- **Desktop sites by default:** turned on automatically for ARM devices with a screen of 10 inches or more and 6.5 GB+ RAM (`DesktopSiteUtils`), with per-site exceptions.
- **Desktop-style tab strip and tab groups on tablets.**
- **Keyboard shortcuts and right-click menus** (`KeyboardShortcuts`); Ctrl+O comes from 0009.
- **S Pen handwriting into text fields,** including Samsung Direct Writing (`components/stylus_handwriting`).
- **Background media playback on large screens** (`kAndroidEnableBackgroundMediaLargeFormFactors`) and picture-in-picture for full-screen video.
- **Reader mode** ("simplified view" on article pages).
- **HTTPS upgrades and automatic secure DNS.**

## Deferred (not done; reasons)

- **Built-in split view (two tabs in one window).** Chrome's Android compositor assumes one active tab per window, so this would be a large new UI written without a compiler. Use Android split screen with two Jagad windows instead ("Open in new window", then drag), which upstream multi-window supports.
- **S Pen button / Air actions mapping.** Air actions are configured by the user in One UI and can map to Jagad's keyboard shortcuts. Remapping the pen button to right-click needs testing on a device first.
- **Bookmark import/export and sync without Google.** Android has no upstream UI for this. Use a sync extension instead (for example floccus with WebDAV, Nextcloud or Git). Passwords already live in Samsung Pass or Google through Android Autofill.
- **Pull-to-refresh setting and swipe between tabs.** These need new settings UI. Revisit once a build host is available.
- **`chrome://flags` entries for Jagad switches.** The histogram enum entries the flags system requires need a full checkout to generate.
