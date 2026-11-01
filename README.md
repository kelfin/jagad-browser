# browser-fork
A Chromium fork for Android, tuned for the Galaxy Tab S9 Ultra. It supports extensions (uBO Lite / uBO) and autofill through the Android password manager.
See docs/ROADMAP.md.

Quick start (on a Linux build host with 64 GB RAM and 300 GB disk):
    scripts/sync.sh <stable-tag> && scripts/apply_patches.sh && scripts/build.sh
    scripts/sign.sh ~/chromium/src/out/TabS9U/apks/ChromePublic.apk
    adb install -r ChromePublic-signed.apk
