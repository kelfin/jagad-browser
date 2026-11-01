import shutil
import subprocess

import pytest


def scripts(repo):
    return sorted((repo / "scripts").glob("*.sh"))


def test_scripts_are_executable_and_parse(repo):
    for s in scripts(repo):
        assert s.stat().st_mode & 0o111, f"{s.name} not executable"
        r = subprocess.run(["bash", "-n", str(s)], capture_output=True, text=True)
        assert r.returncode == 0, f"{s.name}: {r.stderr}"
        assert "set -euo pipefail" in s.read_text(), s.name


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
def test_shellcheck(repo):
    r = subprocess.run(["shellcheck", *map(str, scripts(repo))],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_build_script_generates_ruleset_before_gn(repo):
    text = (repo / "scripts/build.sh").read_text()
    assert text.index("build_ruleset.py") < text.index("gn gen")
