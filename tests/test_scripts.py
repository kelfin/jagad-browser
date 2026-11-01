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


def test_sync_dry_run_shallow(repo, tmp_path):
    env = {"PATH": "/usr/bin:/bin", "CHROMIUM_SRC": str(tmp_path / "chromium/src")}
    r = subprocess.run(["bash", str(repo / "scripts/sync.sh"), "--shallow", "--dry-run"],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    tag = (repo / "CHROMIUM_VERSION").read_text().strip()
    assert "+ fetch --nohooks --no-history android" in r.stdout
    assert f"--no-history --nohooks --revision src@refs/tags/{tag}" in r.stdout
    assert "+ gclient runhooks" in r.stdout
    assert not (tmp_path / "chromium").exists()  # dry run touches nothing


def test_sync_dry_run_full_and_custom_tag(repo, tmp_path):
    env = {"PATH": "/usr/bin:/bin", "CHROMIUM_SRC": str(tmp_path / "src")}
    r = subprocess.run(["bash", str(repo / "scripts/sync.sh"), "--dry-run", "1.2.3.4"],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "refs/tags/1.2.3.4:refs/tags/1.2.3.4" in r.stdout
    assert "--with_branch_heads" in r.stdout


def test_sync_rejects_unknown_option(repo):
    r = subprocess.run(["bash", str(repo / "scripts/sync.sh"), "--bogus"],
                       capture_output=True, text=True)
    assert r.returncode == 2


def test_make_keystore_refuses_to_overwrite(repo, tmp_path):
    ks = tmp_path / "jagad.jks"
    ks.write_text("existing")
    r = subprocess.run(["bash", str(repo / "scripts/make_keystore.sh"), str(ks)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "refusing" in r.stderr
    assert ks.read_text() == "existing"


def test_build_script_appends_extra_args(repo):
    text = (repo / "scripts/build.sh").read_text()
    assert "JAGAD_ARGS_EXTRA" in text
    assert text.index("JAGAD_ARGS_EXTRA") < text.index("gn gen")
