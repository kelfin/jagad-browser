#!/usr/bin/env python3
"""Jagad shadow-tree tool.

A "shadow tree" is a tiny subset of the Chromium source: only the files that
Jagad's patches touch, fetched at the exact CHROMIUM_VERSION tag from
chromium.googlesource.com (gitiles). It lets us verify and author patches
without a 100 GB checkout.

Commands:
  shadow.py files              List Chromium files the series modifies.
  shadow.py fetch [PATH...]    Download pristine copies into the cache.
  shadow.py check              Apply the whole series to a fresh shadow tree.
  shadow.py start [PATH...]    Make a work tree (series applied) for editing,
                               including extra PATHs you are about to touch.
  shadow.py finish NAME SUBJ   Commit the work tree as patches/NNNN-NAME.patch
                               and append it to patches/series.

Environment:
  JAGAD_SHADOW_CACHE  cache dir (default: <repo>/.shadow/<tag>)
  JAGAD_WORK          work tree dir (default: <repo>/.shadow/work)
"""
from __future__ import annotations

import base64
import concurrent.futures as cf
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PATCHES = REPO / "patches"
SERIES = PATCHES / "series"
GITILES = "https://chromium.googlesource.com/chromium/src/+/refs/tags/{tag}/{path}?format=TEXT"
AUTHOR = ["-c", "user.name=Jagad", "-c", "user.email=jagad@localhost"]


def tag() -> str:
    return (REPO / "CHROMIUM_VERSION").read_text().strip()


def cache_dir() -> Path:
    return Path(os.environ.get("JAGAD_SHADOW_CACHE", REPO / ".shadow" / tag()))


def work_dir() -> Path:
    return Path(os.environ.get("JAGAD_WORK", REPO / ".shadow" / "work"))


def series() -> list[Path]:
    """Patch files in apply order (comments and blank lines ignored)."""
    if not SERIES.exists():
        return []
    out = []
    for line in SERIES.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(PATCHES / line)
    return out


_DIFF_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)$")


def touched_files(patch: Path) -> tuple[set[str], set[str]]:
    """Return (pre-existing files modified, files created) by a patch."""
    modified, created = set(), set()
    current = None
    for line in patch.read_text(errors="replace").splitlines():
        m = _DIFF_RE.match(line)
        if m:
            current = m.group(1)
            modified.add(current)
        elif line.startswith("new file mode") and current:
            modified.discard(current)
            created.add(current)
    return modified, created


def upstream_files(extra: list[str] | None = None) -> list[str]:
    """Pristine Chromium files needed to apply the series (+ extra)."""
    needed, created = set(), set()
    for p in series():
        mod, new = touched_files(p)
        needed |= {f for f in mod if f not in created}
        created |= new
    needed |= set(extra or [])
    return sorted(needed)


def _download(path: str) -> str | None:
    dest = cache_dir() / path
    if dest.exists():
        return None
    url = GITILES.format(tag=tag(), path=path)
    err: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = base64.b64decode(r.read())
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return f"{path}: not found at {tag()}"
            err = e
        except Exception as e:  # noqa: BLE001 - network flakiness
            err = e
        time.sleep(2 ** attempt)
    return f"{path}: {err}"


def fetch(paths: list[str]) -> None:
    with cf.ThreadPoolExecutor(12) as ex:
        errors = [e for e in ex.map(_download, paths) if e]
    if errors:
        sys.exit("fetch failed:\n  " + "\n  ".join(errors))


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *AUTHOR, *args], cwd=cwd, text=True,
                          capture_output=True)


def build_tree(dest: Path, extra: list[str] | None = None) -> None:
    """Fresh git repo at dest: pristine files committed, then series applied."""
    files = upstream_files(extra)
    fetch(files)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for f in files:
        (dest / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cache_dir() / f, dest / f)
    _git(dest, "init", "-q")
    _git(dest, "add", "-A")
    _git(dest, "commit", "-q", "--allow-empty", "-m", f"chromium {tag()}")
    for p in series():
        r = _git(dest, "am", "-q", "--3way", "--keep-cr", str(p))
        if r.returncode != 0:
            _git(dest, "am", "--abort")
            raise SystemExit(f"FAIL {p.name}\n{r.stdout}{r.stderr}")


def cmd_check() -> None:
    with tempfile.TemporaryDirectory() as td:
        build_tree(Path(td) / "src")
    for p in series():
        print(f"ok   {p.name}")
    print(f"{len(series())} patches apply cleanly to Chromium {tag()}")


def cmd_finish(name: str, subject: str) -> None:
    wd = work_dir()
    _git(wd, "add", "-A")
    r = _git(wd, "commit", "-q", "-m", subject)
    if r.returncode != 0:
        sys.exit(r.stdout + r.stderr)
    num = 1 + max((int(p.name[:4]) for p in PATCHES.glob("[0-9][0-9][0-9][0-9]-*.patch")),
                  default=0)
    out = PATCHES / f"{num:04d}-{name}.patch"
    r = _git(wd, "format-patch", "-1", "--zero-commit", "--no-signature",
             "--stdout", "HEAD")
    if r.returncode != 0:
        sys.exit(r.stderr)
    out.write_text(r.stdout)
    with SERIES.open("a") as s:
        s.write(out.name + "\n")
    print(out.relative_to(REPO))


def main(argv: list[str]) -> None:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    if cmd == "files":
        print("\n".join(upstream_files()))
    elif cmd == "fetch":
        fetch(upstream_files(rest))
    elif cmd == "check":
        cmd_check()
    elif cmd == "start":
        build_tree(work_dir(), rest)
        print(work_dir())
    elif cmd == "finish":
        if len(rest) != 2:
            sys.exit("usage: shadow.py finish NAME SUBJECT")
        cmd_finish(*rest)
    else:
        sys.exit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    main(sys.argv[1:])
