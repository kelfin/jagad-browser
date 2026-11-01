"""Static checks on the GitHub workflows."""
import re

import pytest

yaml = pytest.importorskip("yaml")


def load(repo, name):
    text = (repo / ".github/workflows" / name).read_text()
    data = yaml.safe_load(text)
    # PyYAML parses the bare key `on` as boolean True.
    data["on"] = data.pop(True, data.get("on"))
    return text, data


def test_build_workflow_shape(repo):
    text, wf = load(repo, "build.yml")
    inputs = wf["on"]["workflow_dispatch"]["inputs"]
    assert {"runner_label", "profile", "run_tests", "release"} <= set(inputs)
    job = wf["jobs"]["build"]
    assert job["runs-on"] == "${{ inputs.runner_label }}"
    assert job["timeout-minutes"] <= 360  # GitHub-hosted job limit
    names = [s.get("name", "") for s in job["steps"]]
    order = ["Sync Chromium (shallow)", "Apply Jagad patches", "Build APK", "Sign APK"]
    assert [n for n in names if n in order] == order


def test_build_workflow_uses_repo_scripts(repo):
    text, _ = load(repo, "build.yml")
    for script in ("scripts/sync.sh --shallow", "scripts/apply_patches.sh",
                   "scripts/build.sh", "scripts/sign.sh"):
        assert script in text


def test_secrets_are_never_echoed(repo):
    text, wf = load(repo, "build.yml")
    for step in wf["jobs"]["build"]["steps"]:
        run = step.get("run", "")
        assert "secrets." not in run, f"secret inlined in run: {step.get('name')}"
        assert not re.search(r"echo\s+\"?\$(KEYSTORE_B64|KS_PASS)", run)
    assert "rm -f \"$RUNNER_TEMP/jagad.jks\"" in text


def test_fast_profile_args_are_valid_gn(repo):
    text, _ = load(repo, "build.yml")
    m = re.search(r"'(is_official_build=false[^']*)'", text)
    assert m
    for kv in m.group(1).split():
        assert re.fullmatch(r"\w+=(true|false|\d+)", kv), kv


def test_check_workflow_runs_tests(repo):
    text, wf = load(repo, "check.yml")
    assert "tools/shadow.py check" in text
    assert "pytest" in text
