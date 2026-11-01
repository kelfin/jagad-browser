import datetime as dt
import sys
from pathlib import Path

import pytest

import build_ruleset as br


def test_normalize_drops_comments_headers_and_uBO_only_rules():
    text = (
        "﻿[Adblock Plus 2.0]\r\n"
        "! Title: EasyList\n"
        "\n"
        "||ads.example.com^\n"
        "example.com##.banner\n"
        "example.com##+js(nowebrtc)\n"
        "example.com#$#abort-on-property-read x\n"
        "example.com#?#div:has(> .ad)\n"
        "@@||good.example.com^$document\n"
    )
    assert br.normalize(text) == [
        "||ads.example.com^",
        "example.com##.banner",
        "@@||good.example.com^$document",
    ]


def test_merge_dedupes_and_keeps_order():
    assert br.merge([["a", "b"], ["b", "c", "a"]]) == ["a", "b", "c"]


def test_ruleset_version_is_stable_and_content_sensitive():
    day = dt.date(2026, 11, 1)
    v1 = br.ruleset_version(["a", "b"], day)
    assert v1 == br.ruleset_version(["a", "b"], day)
    assert v1 != br.ruleset_version(["a", "c"], day)
    assert v1.startswith("20261101.") and len(v1.split(".")[1]) == 12


def test_converter_cmd():
    cmd = br.converter_cmd(Path("/x/conv"), Path("/in.txt"), Path("/out.dat"))
    assert cmd == ["/x/conv", "--input_format=filter-list",
                   "--output_format=unindexed-ruleset",
                   "--input_files=/in.txt", "--output_file=/out.dat"]


@pytest.fixture
def fake_converter(tmp_path) -> Path:
    """Stands in for Chromium's ruleset_converter: copies input to output."""
    conv = tmp_path / "ruleset_converter"
    conv.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "a = dict(x.lstrip('-').split('=', 1) for x in sys.argv[1:])\n"
        "assert a['input_format'] == 'filter-list'\n"
        "assert a['output_format'] == 'unindexed-ruleset'\n"
        "open(a['output_file'], 'w').write('RULESET:' + open(a['input_files']).read())\n"
    )
    conv.chmod(0o755)
    return conv


def test_main_writes_ruleset_and_version(tmp_path, fake_converter):
    l1 = tmp_path / "easylist.txt"
    l1.write_text("! comment\n||ads.example^\n")
    l2 = tmp_path / "easyprivacy.txt"
    l2.write_text("||track.example^\n||ads.example^\n")
    src = tmp_path / "src"
    rc = br.main(["--src", str(src), "--list", str(l1), "--list", str(l2),
                  "--converter", str(fake_converter)])
    assert rc == 0
    out = src / br.OUT_REL
    assert (out / br.RULESET_NAME).read_text() == \
        "RULESET:||ads.example^\n||track.example^\n"
    version = (out / br.VERSION_NAME).read_text().strip()
    assert version == br.ruleset_version(["||ads.example^", "||track.example^"])
    assert not (out / "filter_list.txt").exists()


def test_main_fails_on_empty_lists(tmp_path, fake_converter):
    empty = tmp_path / "empty.txt"
    empty.write_text("! nothing\n")
    rc = br.main(["--src", str(tmp_path / "src"), "--list", str(empty),
                  "--converter", str(fake_converter)])
    assert rc == 1


def test_read_list_sends_user_agent(monkeypatch):
    """easylist.to answers 403 to urllib's default User-Agent."""
    seen = {}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"||ads.example^\n"

    def fake_urlopen(req, timeout):
        seen["ua"] = req.get_header("User-agent")
        return Resp()

    monkeypatch.setattr(br.urllib.request, "urlopen", fake_urlopen)
    assert br.read_list("https://easylist.to/easylist/easylist.txt") == "||ads.example^\n"
    assert seen["ua"] and "Python-urllib" not in seen["ua"]
