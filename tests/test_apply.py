"""Integration: the series applies to the real Chromium files at CHROMIUM_VERSION.

Downloads only the touched files from chromium.googlesource.com (cached in
.shadow/ or $JAGAD_SHADOW_CACHE). Set JAGAD_OFFLINE=1 to skip.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

import shadow
from conftest import network_allowed

pytestmark = pytest.mark.skipif(not network_allowed(), reason="JAGAD_OFFLINE=1")


@pytest.fixture(scope="module")
def pristine_tree(tmp_path_factory) -> Path:
    """A git repo with the pristine Chromium files, series NOT applied."""
    files = shadow.upstream_files()
    shadow.fetch(files)
    dest = tmp_path_factory.mktemp("chromium") / "src"
    dest.mkdir()
    for f in files:
        (dest / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shadow.cache_dir() / f, dest / f)
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(git + ["init", "-q"], cwd=dest, check=True)
    subprocess.run(git + ["add", "-A"], cwd=dest, check=True)
    subprocess.run(git + ["commit", "-qm", "base"], cwd=dest, check=True)
    return dest


def test_series_applies_cleanly():
    with tempfile.TemporaryDirectory() as td:
        shadow.build_tree(Path(td) / "src")  # raises SystemExit on failure


def test_apply_patches_script_end_to_end(repo, pristine_tree):
    env = dict(os.environ, CHROMIUM_SRC=str(pristine_tree),
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run(["bash", str(repo / "scripts/apply_patches.sh")],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    log = subprocess.run(["git", "log", "--format=%s"], cwd=pristine_tree,
                         capture_output=True, text=True, check=True).stdout
    assert log.count("Jagad: ") == len(shadow.series())
    # Spot-check results in the patched tree.
    assert "kJagadKeepManifestV2" in (
        pristine_tree / "extensions/browser/manifest_v2_handler.cc").read_text()
    assert (pristine_tree / "build/config/jagad.gni").exists()
