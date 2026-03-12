"""
Packaging Tests — P-801 through P-809

Phase 8: Git Submodule Version Pinning

These tests verify that every artifact required by the submodule-pinning design
is present and correctly structured in the repository, without requiring a live
OPNsense VM or internet access.

All paths are resolved relative to the repository root so the tests run
correctly from any working directory (CI, local, worktree).

Test IDs:
  P-801  versions.env format — file exists, is shell-sourceable, has non-empty tags
  P-802  versions.env sync — vendor/ and src/ copies are byte-identical
  P-803  .gitmodules paths — vendor/rns-src and vendor/lxmf-src; no stale net/ paths
  P-804  pkg-install git dep check — check_dep git present
  P-805  pkg-install source install — no PyPI pull of rns/lxmf; uses clone_at_tag
  P-806  pkg-plist includes versions.env — file entry and @dir entry present
  P-807  Makefile PLUGIN_DEPENDS includes git
  P-808  Workflow submodule settings — explicit submodules: false where required;
         integration-test.yml has submodules: recursive
  P-809  CI versions.env sync check — static-analysis job has a diff step

Run with: pytest tests/packaging/ -m unit -v
"""
import os
import re
import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Repository root — resolved once relative to this file's location.
# This file lives at:  os-reticulum/tests/packaging/test_submodule_pinning.py
# Repo root is three directories up.
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", )
)

VENDOR_VERSIONS_ENV = os.path.join(REPO_ROOT, "vendor", "versions.env")
SRC_VERSIONS_ENV = os.path.join(
    REPO_ROOT,
    "os-reticulum", "src", "usr", "local", "share", "os-reticulum", "versions.env"
)
GITMODULES = os.path.join(REPO_ROOT, ".gitmodules")
PKG_INSTALL = os.path.join(REPO_ROOT, "os-reticulum", "pkg-install")
PKG_PLIST = os.path.join(REPO_ROOT, "os-reticulum", "pkg-plist")
MAKEFILE = os.path.join(REPO_ROOT, "os-reticulum", "Makefile")

WORKFLOWS_DIR = os.path.join(REPO_ROOT, ".github", "workflows")
WF_CI = os.path.join(WORKFLOWS_DIR, "ci.yml")
WF_LINT = os.path.join(WORKFLOWS_DIR, "lint.yml")
WF_TEST_UNIT = os.path.join(WORKFLOWS_DIR, "test-unit.yml")
WF_RELEASE = os.path.join(WORKFLOWS_DIR, "release.yml")
WF_INTEGRATION = os.path.join(WORKFLOWS_DIR, "integration-test.yml")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path: str) -> str:
    """Read a file and return its content as a string."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _parse_versions_env(content: str) -> dict:
    """
    Parse a shell-sourceable key=value file into a dict.

    Accepts lines of the form:
        KEY="value"
        KEY=value
        # comment lines are ignored
        blank lines are ignored

    Returns a dict mapping KEY -> value (quotes stripped).
    Raises ValueError for lines that cannot be parsed as key=value.
    """
    result = {}
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(
                f"Line {lineno} is not a valid key=value assignment: {raw_line!r}"
            )
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ValueError(
                f"Line {lineno} has an invalid shell identifier: {key!r}"
            )
        result[key] = value
    return result


# ---------------------------------------------------------------------------
# P-801: versions.env format
# ---------------------------------------------------------------------------

class TestP801VersionsEnvFormat:
    """
    P-801: Both copies of versions.env must exist, be parseable as shell
    key=value files, and define non-empty RNS_TAG and LXMF_TAG variables.
    """

    def test_vendor_versions_env_exists(self):
        assert os.path.isfile(VENDOR_VERSIONS_ENV), (
            f"vendor/versions.env not found at {VENDOR_VERSIONS_ENV}. "
            "Create it as part of Phase 8 Step 3."
        )

    def test_src_versions_env_exists(self):
        assert os.path.isfile(SRC_VERSIONS_ENV), (
            f"Deployed versions.env not found at {SRC_VERSIONS_ENV}. "
            "Create it as part of Phase 8 Step 5."
        )

    def test_vendor_versions_env_is_parseable(self):
        content = _read(VENDOR_VERSIONS_ENV)
        # Must not raise
        try:
            _parse_versions_env(content)
        except ValueError as exc:
            pytest.fail(f"vendor/versions.env is not valid shell key=value format: {exc}")

    def test_src_versions_env_is_parseable(self):
        content = _read(SRC_VERSIONS_ENV)
        try:
            _parse_versions_env(content)
        except ValueError as exc:
            pytest.fail(
                f"os-reticulum/src/.../versions.env is not valid shell key=value format: {exc}"
            )

    def test_vendor_versions_env_has_rns_tag(self):
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        assert "RNS_TAG" in parsed, (
            "vendor/versions.env must define RNS_TAG"
        )

    def test_vendor_versions_env_rns_tag_is_non_empty(self):
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        assert parsed.get("RNS_TAG", ""), (
            "vendor/versions.env: RNS_TAG must not be empty"
        )

    def test_vendor_versions_env_has_lxmf_tag(self):
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        assert "LXMF_TAG" in parsed, (
            "vendor/versions.env must define LXMF_TAG"
        )

    def test_vendor_versions_env_lxmf_tag_is_non_empty(self):
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        assert parsed.get("LXMF_TAG", ""), (
            "vendor/versions.env: LXMF_TAG must not be empty"
        )

    def test_vendor_versions_env_rns_tag_looks_like_semver(self):
        """Tag should look like a semver string (e.g. 0.8.9), not a branch name."""
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        tag = parsed.get("RNS_TAG", "")
        assert re.match(r"^\d+\.\d+", tag), (
            f"RNS_TAG {tag!r} does not look like a version tag (expected digits like 0.8.9)"
        )

    def test_vendor_versions_env_lxmf_tag_looks_like_semver(self):
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        tag = parsed.get("LXMF_TAG", "")
        assert re.match(r"^\d+\.\d+", tag), (
            f"LXMF_TAG {tag!r} does not look like a version tag (expected digits like 0.6.2)"
        )

    def test_vendor_versions_env_is_not_a_symlink(self):
        """
        The spec requires a regular file, not a symlink. A symlink to vendor/
        would dangle on the deployed OPNsense target where vendor/ does not exist.
        """
        assert not os.path.islink(SRC_VERSIONS_ENV), (
            f"{SRC_VERSIONS_ENV} must be a regular file copy, not a symlink. "
            "A symlink into vendor/ would dangle on the deployed target."
        )

    def test_versions_env_contains_only_known_keys(self):
        """
        The file should define exactly RNS_TAG and LXMF_TAG — no extra keys
        that could indicate a stale or malformed file.
        """
        content = _read(VENDOR_VERSIONS_ENV)
        parsed = _parse_versions_env(content)
        known_keys = {"RNS_TAG", "LXMF_TAG"}
        extra_keys = set(parsed.keys()) - known_keys
        assert not extra_keys, (
            f"vendor/versions.env has unexpected keys: {extra_keys}. "
            f"Expected only: {known_keys}"
        )


# ---------------------------------------------------------------------------
# P-802: versions.env sync
# ---------------------------------------------------------------------------

class TestP802VersionsEnvSync:
    """
    P-802: vendor/versions.env and the deployed src/ copy must be byte-identical.

    The spec mandates these two files are updated in the same commit every
    time the submodule pointer is advanced. CI enforces this with a diff check
    (P-809). This test catches drift in the local working tree.
    """

    def test_both_copies_have_identical_content(self):
        vendor_content = _read(VENDOR_VERSIONS_ENV)
        src_content = _read(SRC_VERSIONS_ENV)
        assert vendor_content == src_content, (
            "vendor/versions.env and "
            "os-reticulum/src/usr/local/share/os-reticulum/versions.env "
            "are out of sync.\n"
            "Fix: cp vendor/versions.env "
            "os-reticulum/src/usr/local/share/os-reticulum/versions.env"
        )

    def test_both_copies_define_same_rns_tag(self):
        """Belt-and-suspenders: even if whitespace differs, the tag values match."""
        vendor = _parse_versions_env(_read(VENDOR_VERSIONS_ENV))
        src = _parse_versions_env(_read(SRC_VERSIONS_ENV))
        assert vendor.get("RNS_TAG") == src.get("RNS_TAG"), (
            f"RNS_TAG mismatch: vendor={vendor.get('RNS_TAG')!r}, "
            f"src={src.get('RNS_TAG')!r}"
        )

    def test_both_copies_define_same_lxmf_tag(self):
        vendor = _parse_versions_env(_read(VENDOR_VERSIONS_ENV))
        src = _parse_versions_env(_read(SRC_VERSIONS_ENV))
        assert vendor.get("LXMF_TAG") == src.get("LXMF_TAG"), (
            f"LXMF_TAG mismatch: vendor={vendor.get('LXMF_TAG')!r}, "
            f"src={src.get('LXMF_TAG')!r}"
        )


# ---------------------------------------------------------------------------
# P-803: .gitmodules paths
# ---------------------------------------------------------------------------

class TestP803GitmodulesPaths:
    """
    P-803: .gitmodules must declare submodules at vendor/rns-src and
    vendor/lxmf-src. The stale net/reticulum/src/lib/ paths must not appear.
    """

    def test_gitmodules_exists(self):
        assert os.path.isfile(GITMODULES), (
            f".gitmodules not found at {GITMODULES}"
        )

    def test_gitmodules_declares_vendor_rns_src(self):
        content = _read(GITMODULES)
        assert "vendor/rns-src" in content, (
            ".gitmodules must declare a submodule with path vendor/rns-src. "
            "Update from net/reticulum/src/lib/rns-src (Phase 8 Step 1)."
        )

    def test_gitmodules_declares_vendor_lxmf_src(self):
        content = _read(GITMODULES)
        assert "vendor/lxmf-src" in content, (
            ".gitmodules must declare a submodule with path vendor/lxmf-src. "
            "Update from net/reticulum/src/lib/lxmf-src (Phase 8 Step 1)."
        )

    def test_gitmodules_does_not_contain_stale_net_rns_path(self):
        content = _read(GITMODULES)
        assert "net/reticulum/src/lib/rns-src" not in content, (
            ".gitmodules still contains the stale path "
            "net/reticulum/src/lib/rns-src. Replace with vendor/rns-src."
        )

    def test_gitmodules_does_not_contain_stale_net_lxmf_path(self):
        content = _read(GITMODULES)
        assert "net/reticulum/src/lib/lxmf-src" not in content, (
            ".gitmodules still contains the stale path "
            "net/reticulum/src/lib/lxmf-src. Replace with vendor/lxmf-src."
        )

    def test_gitmodules_rns_url_points_to_reticulum(self):
        """The rns-src submodule must point at markqvist/Reticulum."""
        content = _read(GITMODULES)
        # Extract the url line for the vendor/rns-src block.
        # The block is: [submodule "vendor/rns-src"] ... url = ...
        rns_block = re.search(
            r'\[submodule "vendor/rns-src"\].*?(?=\[submodule|\Z)',
            content,
            re.DOTALL,
        )
        assert rns_block, "No [submodule \"vendor/rns-src\"] block found in .gitmodules"
        block_text = rns_block.group(0)
        assert "markqvist/Reticulum" in block_text, (
            "vendor/rns-src submodule URL must point to markqvist/Reticulum. "
            f"Got block:\n{block_text}"
        )

    def test_gitmodules_lxmf_url_points_to_lxmf(self):
        """The lxmf-src submodule must point at markqvist/LXMF."""
        content = _read(GITMODULES)
        lxmf_block = re.search(
            r'\[submodule "vendor/lxmf-src"\].*?(?=\[submodule|\Z)',
            content,
            re.DOTALL,
        )
        assert lxmf_block, "No [submodule \"vendor/lxmf-src\"] block found in .gitmodules"
        block_text = lxmf_block.group(0)
        assert "markqvist/LXMF" in block_text, (
            "vendor/lxmf-src submodule URL must point to markqvist/LXMF. "
            f"Got block:\n{block_text}"
        )


# ---------------------------------------------------------------------------
# P-804: pkg-install has git dep check
# ---------------------------------------------------------------------------

class TestP804PkgInstallGitDepCheck:
    """
    P-804: pkg-install must call check_dep git before the clone_at_tag function
    is invoked. This catches the case where pkg-install is run directly (e.g.
    during development or OPNsense plugin testing) without pkg first resolving
    PLUGIN_DEPENDS.
    """

    def test_pkg_install_exists(self):
        assert os.path.isfile(PKG_INSTALL), (
            f"pkg-install not found at {PKG_INSTALL}"
        )

    def test_pkg_install_calls_check_dep_git(self):
        content = _read(PKG_INSTALL)
        assert "check_dep git" in content, (
            "pkg-install must call 'check_dep git' to guard against direct "
            "invocation without pkg resolving PLUGIN_DEPENDS first. "
            "Add: check_dep git \"Install with: pkg install git\" "
            "(Phase 8 Step 4)."
        )

    def test_check_dep_git_appears_before_clone_at_tag_definition(self):
        """
        The git dep check must appear before clone_at_tag is defined.
        Placing it after the function definition but before the first call
        is also acceptable, but the guard must exist early in the script
        to emit a clear error before any confusing 'command not found' output.
        """
        content = _read(PKG_INSTALL)
        dep_check_pos = content.find("check_dep git")
        # Match the actual function definition line, not a comment mentioning it
        clone_at_tag_def = re.search(r"^clone_at_tag\(\)", content, re.MULTILINE)
        assert dep_check_pos != -1, "check_dep git not found in pkg-install"
        # clone_at_tag() is the function definition; if it exists it should
        # come after the dep check, or dep check comes before first call site.
        if clone_at_tag_def is not None:
            assert dep_check_pos < clone_at_tag_def.start(), (
                "check_dep git should appear before the clone_at_tag function "
                "definition in pkg-install."
            )


# ---------------------------------------------------------------------------
# P-805: pkg-install uses clone_at_tag, not PyPI
# ---------------------------------------------------------------------------

class TestP805PkgInstallSourceInstall:
    """
    P-805: pkg-install must not pip-install rns or lxmf directly from PyPI.
    It must instead use clone_at_tag to fetch from GitHub and pip-install
    from the local clone. The VERSIONS_ENV and SRC_BASE variables must be
    present to indicate the Phase 8 install flow is in place.
    """

    def test_pkg_install_does_not_pip_install_rns_from_pypi(self):
        """
        The old 'pip install --upgrade rns lxmf' (or 'pip install rns') line
        must be removed. PyPI installs are non-deterministic.

        pip install of a local path (/usr/local/reticulum-src/reticulum) is
        allowed — that is the Phase 8 target flow.
        """
        content = _read(PKG_INSTALL)
        # Match actual pip install command lines where rns/lxmf appears as a
        # bare PyPI package name. Exclude:
        #  - comment lines (starting with #)
        #  - echo/error message lines (inside quotes)
        #  - pip install of local paths (contains / after the package name area)
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.strip().startswith("#")
        ]
        # Only look at lines that actually invoke pip (not echo/error strings)
        pip_command_lines = [
            line for line in non_comment_lines
            if re.search(r'(?:bin/)?pip["\s]', line)
            and not re.search(r'echo\s', line)
        ]
        pypi_install_pattern = re.compile(
            r"pip[\"']?\s+install\b(?!.*\$\{SRC_BASE\})(?!.*/)[^#\n]*\b(?:rns|lxmf)\b",
            re.IGNORECASE,
        )
        matches = [
            line.strip() for line in pip_command_lines
            if pypi_install_pattern.search(line)
        ]
        assert not matches, (
            "pkg-install still contains a PyPI pip install of rns/lxmf by name:\n"
            + "\n".join(matches)
            + "\nReplace with clone_at_tag + pip install from local path (Phase 8 Step 4)."
        )

    def test_pkg_install_defines_clone_at_tag_function(self):
        content = _read(PKG_INSTALL)
        assert "clone_at_tag" in content, (
            "pkg-install must define and use a clone_at_tag function "
            "(Phase 8 Step 4). Not found in pkg-install."
        )

    def test_pkg_install_references_versions_env_path(self):
        content = _read(PKG_INSTALL)
        assert "VERSIONS_ENV" in content, (
            "pkg-install must define VERSIONS_ENV pointing to the installed "
            "versions.env file (/usr/local/share/os-reticulum/versions.env). "
            "Not found in pkg-install (Phase 8 Step 4)."
        )

    def test_pkg_install_references_src_base(self):
        content = _read(PKG_INSTALL)
        assert "SRC_BASE" in content, (
            "pkg-install must define SRC_BASE for the clone destination "
            "(/usr/local/reticulum-src). Not found in pkg-install (Phase 8 Step 4)."
        )

    def test_pkg_install_sources_versions_env(self):
        """pkg-install must dot-source the VERSIONS_ENV file to load the tags."""
        content = _read(PKG_INSTALL)
        # Shell source: `. "${VERSIONS_ENV}"` or `. $VERSIONS_ENV`
        assert re.search(r'\.\s+["\$\{]*VERSIONS_ENV', content), (
            "pkg-install must source VERSIONS_ENV with: . \"${VERSIONS_ENV}\" "
            "(Phase 8 Step 4). This populates RNS_TAG and LXMF_TAG."
        )

    def test_pkg_install_checks_versions_env_exists_before_sourcing(self):
        """
        pkg-install must check that VERSIONS_ENV is present before sourcing it,
        to print a clear error message if the package is corrupt.
        """
        content = _read(PKG_INSTALL)
        assert re.search(r'\$\{?VERSIONS_ENV\}?.*not found|not found.*\$\{?VERSIONS_ENV\}?', content) or \
               re.search(r'!\s+\[\s+-f\s+["\$\{]*VERSIONS_ENV', content), (
            "pkg-install must check [ -f \"${VERSIONS_ENV}\" ] before sourcing it "
            "and print an actionable error if missing (Phase 8 Step 4)."
        )

    def test_pkg_install_uses_rns_tag_variable(self):
        """After sourcing versions.env, RNS_TAG must be used (e.g. in clone_at_tag call)."""
        content = _read(PKG_INSTALL)
        assert "RNS_TAG" in content, (
            "pkg-install must reference RNS_TAG after sourcing VERSIONS_ENV. "
            "It is used as the tag argument to clone_at_tag (Phase 8 Step 4)."
        )

    def test_pkg_install_uses_lxmf_tag_variable(self):
        content = _read(PKG_INSTALL)
        assert "LXMF_TAG" in content, (
            "pkg-install must reference LXMF_TAG after sourcing VERSIONS_ENV. "
            "It is used as the tag argument to clone_at_tag (Phase 8 Step 4)."
        )

    def test_pkg_install_version_recording_uses_tag_not_importlib(self):
        """
        Phase 8 replaces the importlib.metadata version-recording block with
        direct use of RNS_TAG / LXMF_TAG from versions.env, because git describe
        is unreliable on shallow clones.
        """
        content = _read(PKG_INSTALL)
        assert "importlib.metadata" not in content, (
            "pkg-install still uses importlib.metadata to record installed versions. "
            "Replace with: RNS_VER=\"${RNS_TAG}\" / LXMF_VER=\"${LXMF_TAG}\" "
            "(Phase 8 Step 4)."
        )


# ---------------------------------------------------------------------------
# P-806: pkg-plist includes versions.env
# ---------------------------------------------------------------------------

class TestP806PkgPlistVersionsEnv:
    """
    P-806: pkg-plist must list the deployed versions.env file and the @dir
    entry for /usr/local/share/os-reticulum. Both entries are required for
    correct FreeBSD pkg install and deinstall behavior.
    """

    def test_pkg_plist_exists(self):
        assert os.path.isfile(PKG_PLIST), (
            f"pkg-plist not found at {PKG_PLIST}"
        )

    def test_pkg_plist_has_versions_env_file_entry(self):
        content = _read(PKG_PLIST)
        assert "/usr/local/share/os-reticulum/versions.env" in content, (
            "pkg-plist must include the file entry "
            "/usr/local/share/os-reticulum/versions.env (Phase 8 Step 5). "
            "Without this the file is not deployed by pkg install."
        )

    def test_pkg_plist_has_dir_entry_for_share_os_reticulum(self):
        content = _read(PKG_PLIST)
        assert "@dir /usr/local/share/os-reticulum" in content, (
            "pkg-plist must include '@dir /usr/local/share/os-reticulum' "
            "(Phase 8 Step 5). Without this entry FreeBSD pkg fails to create "
            "the directory during install and leaves it orphaned on deinstall."
        )

    def test_pkg_plist_dir_entry_follows_file_entry(self):
        """
        The @dir entry must appear after the file entry. pkg processes plist
        lines in order; the directory must exist before or at the same time
        the file is placed, but the @dir entry is used for cleanup on removal
        and must appear after the file(s) it owns.
        """
        content = _read(PKG_PLIST)
        file_entry = "/usr/local/share/os-reticulum/versions.env"
        dir_entry = "@dir /usr/local/share/os-reticulum"
        file_pos = content.find(file_entry)
        dir_pos = content.find(dir_entry)
        assert file_pos != -1, f"File entry not found: {file_entry}"
        assert dir_pos != -1, f"Dir entry not found: {dir_entry}"
        assert file_pos < dir_pos, (
            f"@dir entry (pos={dir_pos}) must appear after the file entry "
            f"(pos={file_pos}) in pkg-plist."
        )


# ---------------------------------------------------------------------------
# P-807: Makefile PLUGIN_DEPENDS includes git
# ---------------------------------------------------------------------------

class TestP807MakefilePluginDepends:
    """
    P-807: The os-reticulum/Makefile must include 'git' in PLUGIN_DEPENDS so
    that FreeBSD pkg installs git before pkg-install runs under normal flow.
    """

    def test_makefile_exists(self):
        assert os.path.isfile(MAKEFILE), (
            f"Makefile not found at {MAKEFILE}"
        )

    def test_makefile_plugin_depends_includes_git(self):
        content = _read(MAKEFILE)
        # PLUGIN_DEPENDS line may use spaces or tabs and may span one line.
        # We need git to appear somewhere on the PLUGIN_DEPENDS line(s).
        plugin_depends_match = re.search(
            r"^PLUGIN_DEPENDS\s*=\s*(.+)$", content, re.MULTILINE
        )
        assert plugin_depends_match, (
            "PLUGIN_DEPENDS line not found in Makefile"
        )
        depends_value = plugin_depends_match.group(1)
        # git must appear as a standalone token (not as part of another package name)
        tokens = depends_value.split()
        assert "git" in tokens, (
            f"PLUGIN_DEPENDS does not include 'git'. Current value: {depends_value!r}. "
            "Add git to PLUGIN_DEPENDS (Phase 8 Step 6)."
        )

    def test_makefile_plugin_depends_still_includes_python(self):
        """Regression: adding git must not remove the Python dependency."""
        content = _read(MAKEFILE)
        assert "python311" in content, (
            "python311 was removed from PLUGIN_DEPENDS — this is a regression. "
            "Only git should have been added."
        )


# ---------------------------------------------------------------------------
# P-808: Workflow submodule settings
# ---------------------------------------------------------------------------

class TestP808WorkflowSubmoduleSettings:
    """
    P-808: Validate submodule checkout settings across all GitHub Actions
    workflow files.

    Required state after Phase 8:
      ci.yml       static-analysis: submodules: false (already set)
      ci.yml       unit-tests:      submodules: false (to be added)
      lint.yml     php, xml, shell, python jobs: submodules: false (to be added, all 4)
      test-unit.yml pytest job:     submodules: false (to be added)
      release.yml  release job:     submodules: false (to be added)
      integration-test.yml:         submodules: recursive (already set)
    """

    # --- ci.yml ---

    def test_ci_yml_exists(self):
        assert os.path.isfile(WF_CI), f"ci.yml not found at {WF_CI}"

    def test_ci_yml_static_analysis_has_submodules_false(self):
        """
        ci.yml static-analysis job already had submodules: false.
        This test guards against accidental removal.
        """
        content = _read(WF_CI)
        # Find the static-analysis job block and verify submodules: false is present.
        # We look for the pattern within the job rather than across the whole file,
        # since the unit-tests job checkout also needs it after Phase 8.
        static_analysis_block = re.search(
            r"static-analysis:.*?(?=\n\s{2}\w|\Z)",
            content,
            re.DOTALL,
        )
        assert static_analysis_block, "static-analysis job not found in ci.yml"
        block = static_analysis_block.group(0)
        assert "submodules: false" in block, (
            "ci.yml static-analysis job checkout must have 'submodules: false'. "
            "This was already set — guard against accidental removal."
        )

    def test_ci_yml_unit_tests_has_submodules_false(self):
        """
        ci.yml unit-tests job must have submodules: false on its checkout step.
        Unit tests don't import RNS/LXMF so submodule clones are unnecessary.
        """
        content = _read(WF_CI)
        unit_tests_block = re.search(
            r"unit-tests:.*?(?=\n\s{2}\w|\Z)",
            content,
            re.DOTALL,
        )
        assert unit_tests_block, "unit-tests job not found in ci.yml"
        block = unit_tests_block.group(0)
        assert "submodules: false" in block, (
            "ci.yml unit-tests job checkout must have 'submodules: false' "
            "(Phase 8 Step 8a). Without this, every unit-test run clones the "
            "full submodule history unnecessarily."
        )

    # --- lint.yml ---

    def test_lint_yml_exists(self):
        assert os.path.isfile(WF_LINT), f"lint.yml not found at {WF_LINT}"

    def test_lint_yml_php_job_has_submodules_false(self):
        content = _read(WF_LINT)
        php_block = re.search(
            r"^\s{2}php:.*?(?=^\s{2}\w|\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        assert php_block, "php job not found in lint.yml"
        assert "submodules: false" in php_block.group(0), (
            "lint.yml php job checkout must have 'submodules: false' (Phase 8 Step 8b)."
        )

    def test_lint_yml_xml_job_has_submodules_false(self):
        content = _read(WF_LINT)
        xml_block = re.search(
            r"^\s{2}xml:.*?(?=^\s{2}\w|\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        assert xml_block, "xml job not found in lint.yml"
        assert "submodules: false" in xml_block.group(0), (
            "lint.yml xml job checkout must have 'submodules: false' (Phase 8 Step 8b)."
        )

    def test_lint_yml_shell_job_has_submodules_false(self):
        content = _read(WF_LINT)
        shell_block = re.search(
            r"^\s{2}shell:.*?(?=^\s{2}\w|\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        assert shell_block, "shell job not found in lint.yml"
        assert "submodules: false" in shell_block.group(0), (
            "lint.yml shell job checkout must have 'submodules: false' (Phase 8 Step 8b)."
        )

    def test_lint_yml_python_job_has_submodules_false(self):
        content = _read(WF_LINT)
        python_block = re.search(
            r"^\s{2}python:.*?(?=^\s{2}\w|\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        assert python_block, "python job not found in lint.yml"
        assert "submodules: false" in python_block.group(0), (
            "lint.yml python job checkout must have 'submodules: false' (Phase 8 Step 8b)."
        )

    # --- test-unit.yml ---

    def test_test_unit_yml_exists(self):
        assert os.path.isfile(WF_TEST_UNIT), f"test-unit.yml not found at {WF_TEST_UNIT}"

    def test_test_unit_yml_pytest_job_has_submodules_false(self):
        content = _read(WF_TEST_UNIT)
        # test-unit.yml has a single job named 'pytest'
        pytest_block = re.search(
            r"^\s{2}pytest:.*?(?=^\s{2}\w|\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        assert pytest_block, "pytest job not found in test-unit.yml"
        assert "submodules: false" in pytest_block.group(0), (
            "test-unit.yml pytest job checkout must have 'submodules: false' "
            "(Phase 8 Step 8c)."
        )

    # --- release.yml ---

    def test_release_yml_exists(self):
        assert os.path.isfile(WF_RELEASE), f"release.yml not found at {WF_RELEASE}"

    def test_release_yml_has_submodules_false(self):
        content = _read(WF_RELEASE)
        assert "submodules: false" in content, (
            "release.yml checkout must have 'submodules: false' (Phase 8 Step 8d). "
            "The release archive includes only os-reticulum/; vendor/ is excluded "
            "structurally. Submodule clones waste time on release runners."
        )

    def test_release_yml_submodules_false_alongside_fetch_depth(self):
        """Both fetch-depth: 0 and submodules: false must coexist in the checkout."""
        content = _read(WF_RELEASE)
        checkout_block = re.search(
            r"uses:\s*actions/checkout@.*?(?=\s*-\s+(?:uses:|name:)|\Z)",
            content,
            re.DOTALL,
        )
        assert checkout_block, "actions/checkout step not found in release.yml"
        block = checkout_block.group(0)
        assert "fetch-depth: 0" in block, (
            "release.yml must still have fetch-depth: 0 — needed for version tagging."
        )
        assert "submodules: false" in block, (
            "release.yml checkout must add 'submodules: false' alongside fetch-depth: 0."
        )

    # --- integration-test.yml ---

    def test_integration_test_yml_exists(self):
        assert os.path.isfile(WF_INTEGRATION), (
            f"integration-test.yml not found at {WF_INTEGRATION}"
        )

    def test_integration_test_yml_has_submodules_recursive(self):
        """
        integration-test.yml needs the submodules populated so the deploy step
        can pip install from vendor/rns-src and vendor/lxmf-src. It must use
        submodules: recursive (already set — guard against removal).
        """
        content = _read(WF_INTEGRATION)
        assert "submodules: recursive" in content, (
            "integration-test.yml checkout must keep 'submodules: recursive'. "
            "The deploy step installs from vendor/rns-src and vendor/lxmf-src. "
            "Do not change this to 'false'."
        )

    def test_integration_test_yml_does_not_have_submodules_false(self):
        """
        Ensure integration-test.yml was not accidentally changed to
        submodules: false when other workflows were updated.
        """
        content = _read(WF_INTEGRATION)
        # submodules: false must not appear anywhere in this file
        assert "submodules: false" not in content, (
            "integration-test.yml must not have 'submodules: false'. "
            "It requires 'submodules: recursive' for the vendor/ source install."
        )


# ---------------------------------------------------------------------------
# P-809: CI versions.env sync check
# ---------------------------------------------------------------------------

class TestP809CiVersionsEnvSyncCheck:
    """
    P-809: The ci.yml static-analysis job must include a step that diffs the
    two versions.env copies and fails CI if they diverge. This catches the
    common mistake of advancing the submodule pointer without copying the
    updated vendor/versions.env to the src/ location.
    """

    def test_ci_yml_has_versions_env_sync_step(self):
        content = _read(WF_CI)
        # The step name or run block must reference versions.env sync/diff.
        # Accept any of: diff, versions.env sync, Check versions.env
        assert re.search(
            r"versions\.env",
            content,
        ), (
            "ci.yml static-analysis job has no step referencing versions.env. "
            "Add the versions.env sync check step (Phase 8 Step 8g)."
        )

    def test_ci_yml_sync_step_uses_diff(self):
        """
        The sync check must use diff (or equivalent) to compare the two copies.
        A step that only prints the contents without comparing would not catch drift.
        """
        content = _read(WF_CI)
        assert re.search(r"\bdiff\b.*versions\.env|versions\.env.*\bdiff\b", content, re.DOTALL), (
            "ci.yml must use 'diff' to compare vendor/versions.env with "
            "os-reticulum/src/usr/local/share/os-reticulum/versions.env. "
            "A print/cat step is not sufficient (Phase 8 Step 8g)."
        )

    def test_ci_yml_sync_step_references_vendor_path(self):
        content = _read(WF_CI)
        assert "vendor/versions.env" in content, (
            "ci.yml sync check must reference vendor/versions.env explicitly "
            "(Phase 8 Step 8g)."
        )

    def test_ci_yml_sync_step_references_src_path(self):
        content = _read(WF_CI)
        assert "os-reticulum/src/usr/local/share/os-reticulum/versions.env" in content, (
            "ci.yml sync check must reference the deployed src/ copy of "
            "versions.env explicitly (Phase 8 Step 8g)."
        )

    def test_ci_yml_sync_step_in_static_analysis_job(self):
        """
        The sync check belongs in the static-analysis job, not the unit-tests
        job. Static analysis runs first; catching drift early avoids wasting
        the unit-test job run.
        """
        content = _read(WF_CI)
        static_analysis_block = re.search(
            r"static-analysis:.*?(?=\n\s{2}\w|\Z)",
            content,
            re.DOTALL,
        )
        assert static_analysis_block, "static-analysis job not found in ci.yml"
        block = static_analysis_block.group(0)
        assert "versions.env" in block, (
            "versions.env sync check must be in the static-analysis job, "
            "not in the unit-tests job (Phase 8 Step 8g)."
        )
