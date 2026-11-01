"""Static checks on patches/series and the patch files themselves."""
import re
from pathlib import Path

import pytest

import shadow

PATCH_RE = re.compile(r"^(\d{4})-[A-Za-z0-9._-]+\.patch$")


def all_patches(repo: Path) -> list[Path]:
    return sorted(p for p in (repo / "patches").glob("*.patch"))


def test_series_lists_every_patch_exactly_once(repo):
    listed = [p.name for p in shadow.series()]
    on_disk = [p.name for p in all_patches(repo)]
    assert len(listed) == len(set(listed)), "duplicate entries in series"
    assert sorted(listed) == on_disk


def test_series_order_matches_numbering(repo):
    nums = [int(PATCH_RE.match(p.name).group(1)) for p in shadow.series()]
    assert nums == list(range(1, len(nums) + 1))


@pytest.mark.parametrize("patch", all_patches(Path(__file__).resolve().parent.parent),
                         ids=lambda p: p.name[:4])
def test_patch_is_well_formed(patch):
    text = patch.read_text()
    assert PATCH_RE.match(patch.name)
    assert text.startswith("From 0000000000000000000000000000000000000000 "), \
        "use --zero-commit so patches are reproducible"
    subject = re.search(r"^Subject: \[PATCH\] (.+)$", text, re.M)
    assert subject and subject.group(1).startswith("Jagad: ")
    assert "diff --git a/" in text
    # No secrets / local paths leaking into patches.
    assert "/home/" not in text and "/root/" not in text
    # Copyright headers of new files must not claim to be Chromium's.
    for new_file in re.findall(r"^diff --git a/(\S+) b/\S+\nnew file mode", text, re.M):
        assert new_file.startswith(("build/", "chrome/", "components/")), new_file


def test_touched_files_parses_new_and_modified(tmp_path):
    p = tmp_path / "x.patch"
    p.write_text(
        "diff --git a/a/old.cc b/a/old.cc\nindex 1..2 100644\n"
        "diff --git a/a/new.gni b/a/new.gni\nnew file mode 100644\n"
    )
    modified, created = shadow.touched_files(p)
    assert modified == {"a/old.cc"}
    assert created == {"a/new.gni"}


def test_upstream_files_excludes_files_created_by_series():
    files = shadow.upstream_files()
    assert "build/config/jagad.gni" not in files  # created by 0005
    assert "build/config/compiler/BUILD.gn" in files


# --- Content checks: each patch does what its subject says. -----------------

def _patch(name_part: str) -> str:
    matches = [p for p in shadow.series() if name_part in p.name]
    assert len(matches) == 1, name_part
    return matches[0].read_text()


def _added(text: str) -> str:
    return "\n".join(l[1:] for l in text.splitlines()
                     if l.startswith("+") and not l.startswith("+++"))


def test_every_jagad_feature_is_enabled_and_used():
    added = "\n".join(_added(p.read_text()) for p in shadow.series())
    defined = re.findall(r"BASE_FEATURE\((kJagad\w+),\s*base::(\w+)\)", added)
    assert defined, "expected Jagad features"
    for name, state in defined:
        assert state == "FEATURE_ENABLED_BY_DEFAULT", name
        uses = len(re.findall(rf"\b{name}\b", added))
        assert uses >= 3, f"{name} is declared but not used"  # decl + def + use


def test_branding_patch():
    added = _added(_patch("branding"))
    assert ">Jagad<" in added
    assert "PRODUCT_FULLNAME=Jagad" in added
    # The Chromium copyright line must be kept (BSD licence).
    assert "COPYRIGHT=" not in added


def test_adblock_resources_match_tool_outputs():
    import build_ruleset
    text = _added(_patch("built-in-adblock"))
    assert f"resources/jagad/{build_ruleset.RULESET_NAME}" in text
    assert f"resources/jagad/{build_ruleset.VERSION_NAME}" in text
    for rid in ("IDR_JAGAD_ADBLOCK_RULESET", "IDR_JAGAD_ADBLOCK_RULESET_VERSION"):
        assert text.count(rid) >= 2, rid  # declared in grd, used in installer


def test_autofill_default_is_platform_autofill():
    added = _added(_patch("Android-Autofill"))
    assert "RegisterBooleanPref(kAutofillUsingPlatformAutofill, true)" in added


def test_tablet_features_native_and_java_defaults_agree():
    text = _patch("tablet-features")
    added, removed = _added(text), "\n".join(
        l[1:] for l in text.splitlines() if l.startswith("-") and not l.startswith("---"))
    native_on = set(re.findall(r"BASE_FEATURE\((k\w+), base::FEATURE_ENABLED_BY_DEFAULT\)", added))
    native_off = set(re.findall(r"BASE_FEATURE\((k\w+), base::FEATURE_DISABLED_BY_DEFAULT\)", removed))
    assert native_on == native_off and len(native_on) >= 5
    assert "kAndroidVerticalTabs" in native_on
    # No Java cached flag may still default to false for a feature turned on.
    assert not re.search(r"Cached\w*\((?:ANDROID_VERTICAL_TABS|ANDROID_KEYBOARD_SHORTCUT_OPEN_FILE)"
                         r", false\)", added)


def test_cpu_tuning_args_only_apply_to_android_arm64():
    added = _added(_patch("cpu-tuning"))
    assert 'current_cpu == "arm64" && is_android && is_clang' in added
    assert 'jagad_arm64_march = ""' in added and 'jagad_arm64_mtune = ""' in added
