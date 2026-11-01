"""Checks on args/tabs9u.gn."""
import re

import shadow


def parse_gn_args(text: str) -> dict[str, str]:
    args = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"^(\w+)\s*=\s*(.+)$", line)
        assert m, f"unparseable line: {line!r}"
        args[m.group(1)] = m.group(2).strip()
    return args


def args(repo):
    return parse_gn_args((repo / "args/tabs9u.gn").read_text())


def test_required_args(repo):
    a = args(repo)
    assert a["target_os"] == '"android"'
    assert a["target_cpu"] == '"arm64"'
    assert a["is_official_build"] == "true"
    assert a["is_debug"] == "false"
    assert a["is_desktop_android"] == "true"  # extensions
    assert a["chrome_public_manifest_package"] == '"com.kelfin.jagad"'


def test_no_google_api_keys(repo):
    a = args(repo)
    for k in ("google_api_key", "google_default_client_id",
              "google_default_client_secret"):
        assert a[k] == '""'


def test_jagad_args_are_declared_by_the_series(repo):
    declared = set()
    for p in shadow.series():
        declared |= set(re.findall(r"^\+\s*(jagad_\w+)\s*=", p.read_text(), re.M))
    used = {k for k in args(repo) if k.startswith("jagad_")}
    assert used, "expected jagad_* args in tabs9u.gn"
    assert used <= declared, f"undeclared: {used - declared}"


def test_cpu_tuning_is_safe_for_snapdragon_8_gen_2(repo):
    a = args(repo)
    march = a["jagad_arm64_march"].strip('"')
    base = march.split("+")[0]
    # All cores (X3/A715/A710/A510) are Armv9.0; anything up to v8.5 is safe.
    assert base in {"armv8-a", "armv8.2-a", "armv8.4-a", "armv8.5-a", "armv9-a"}
    assert a["jagad_arm64_mtune"].strip('"').startswith("cortex-")


def test_chromium_version_is_a_tag(repo):
    v = (repo / "CHROMIUM_VERSION").read_text().strip()
    assert re.fullmatch(r"\d+\.0\.\d+\.\d+", v)
