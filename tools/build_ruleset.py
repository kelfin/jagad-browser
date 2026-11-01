#!/usr/bin/env python3
"""Build Jagad's bundled adblock ruleset (used by patch 0003).

Downloads filter lists (EasyList + EasyPrivacy by default), normalizes them,
converts them to Chromium's unindexed-ruleset format with Chromium's own
`ruleset_converter` tool, and writes:

  $CHROMIUM_SRC/chrome/browser/resources/jagad/adblock_ruleset.dat
  $CHROMIUM_SRC/chrome/browser/resources/jagad/adblock_ruleset_version.txt

The filter lists are third-party data (EasyList: GPLv3 / CC BY-SA 3.0); they
are downloaded at build time and never committed to this repo.

usage: build_ruleset.py [--src CHROMIUM_SRC] [--list URL_OR_PATH ...]
                        [--converter PATH] [--host-out out/Host]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_LISTS = [
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
]
OUT_REL = Path("chrome/browser/resources/jagad")
RULESET_NAME = "adblock_ruleset.dat"
VERSION_NAME = "adblock_ruleset_version.txt"


def read_list(source: str) -> str:
    """Return the text of a filter list from a URL or a local path."""
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=120) as r:
            raw = r.read()
    else:
        raw = Path(source).read_bytes()
    return raw.decode("utf-8-sig", errors="replace")


def normalize(text: str) -> list[str]:
    """Clean a filter list into rule lines Chromium's parser understands.

    Drops blank lines, comments (`!`), the `[Adblock Plus x.y]` header and
    uBO-only scriptlet / procedural rules that Chromium cannot use. Everything
    else is passed through; the converter itself skips rules it can't parse.
    """
    out = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line or line.startswith("!"):
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        if any(tok in line for tok in ("##+js(", "#$#", "#?#", "#@$#", "#@?#")):
            continue
        out.append(line)
    return out


def merge(lists: list[list[str]]) -> list[str]:
    """Concatenate lists, dropping exact duplicates but keeping order."""
    seen: set[str] = set()
    merged = []
    for rules in lists:
        for rule in rules:
            if rule not in seen:
                seen.add(rule)
                merged.append(rule)
    return merged


def ruleset_version(rules: list[str], today: dt.date | None = None) -> str:
    """Stable version string: date + short content hash.

    Used as the RulesetService content_version, so a changed list is always
    re-indexed on the device, and an unchanged one is not.
    """
    today = today or dt.date.today()
    digest = hashlib.sha256("\n".join(rules).encode()).hexdigest()[:12]
    return f"{today:%Y%m%d}.{digest}"


def converter_cmd(converter: Path, input_file: Path, output_file: Path) -> list[str]:
    return [
        str(converter),
        "--input_format=filter-list",
        "--output_format=unindexed-ruleset",
        f"--input_files={input_file}",
        f"--output_file={output_file}",
    ]


def ensure_converter(src: Path, host_out: str) -> Path:
    """Build Chromium's ruleset_converter for the host if it isn't built."""
    out = src / host_out
    exe = out / "ruleset_converter"
    if exe.exists():
        return exe
    if not (out / "args.gn").exists():
        out.mkdir(parents=True, exist_ok=True)
        (out / "args.gn").write_text("is_debug = false\nsymbol_level = 0\n")
        subprocess.run(["gn", "gen", str(out)], cwd=src, check=True)
    subprocess.run(["autoninja", "-C", str(out), "ruleset_converter"],
                   cwd=src, check=True)
    return exe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=os.environ.get(
        "CHROMIUM_SRC", str(Path.home() / "chromium/src")))
    ap.add_argument("--list", action="append", dest="lists",
                    help="filter list URL or path (repeatable)")
    ap.add_argument("--converter", help="path to a built ruleset_converter")
    ap.add_argument("--host-out", default="out/Host")
    a = ap.parse_args(argv)

    src = Path(a.src)
    out_dir = src / OUT_REL
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = a.lists or DEFAULT_LISTS
    rules = merge([normalize(read_list(s)) for s in sources])
    if not rules:
        print("no rules found in the filter lists", file=sys.stderr)
        return 1

    merged_txt = out_dir / "filter_list.txt"
    merged_txt.write_text("\n".join(rules) + "\n")

    converter = Path(a.converter) if a.converter else ensure_converter(src, a.host_out)
    subprocess.run(converter_cmd(converter, merged_txt, out_dir / RULESET_NAME),
                   check=True)
    merged_txt.unlink()

    version = ruleset_version(rules)
    (out_dir / VERSION_NAME).write_text(version + "\n")
    print(f"{len(rules)} rules -> {out_dir / RULESET_NAME} (version {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
