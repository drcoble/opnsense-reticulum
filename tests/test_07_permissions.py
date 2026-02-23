"""Test 07: File permissions and ownership verification.

Checks that all config directories and scripts have correct ownership,
permissions, and group memberships.
"""

import pytest

pytestmark = pytest.mark.integration


class TestDirectoryPermissions:
    """Verify ownership and modes on all plugin directories."""

    EXPECTED_DIRS = [
        "/usr/local/etc/reticulum",
        "/usr/local/etc/lxmd",
        "/var/db/lxmd",
        "/var/db/lxmd/messagestore",
        "/var/log/reticulum",
    ]

    @pytest.mark.parametrize("path", EXPECTED_DIRS)
    def test_directory_ownership(self, ssh, path):
        """Directory owned by _reticulum:_reticulum."""
        stdout, _, rc = ssh(f"stat -f '%Su:%Sg' {path}")
        assert rc == 0, f"Directory {path} does not exist"
        assert stdout.strip() == "_reticulum:_reticulum", (
            f"{path} ownership is {stdout}, expected _reticulum:_reticulum"
        )

    @pytest.mark.parametrize("path", EXPECTED_DIRS)
    def test_directory_permissions(self, ssh, path):
        """Directory has mode 750."""
        stdout, _, rc = ssh(f"stat -f '%Lp' {path}")
        assert rc == 0, f"Directory {path} does not exist"
        assert stdout.strip() == "750", (
            f"{path} permissions are {stdout}, expected 750"
        )


class TestScriptPermissions:
    """Verify plugin scripts are executable."""

    SCRIPTS = [
        "/usr/local/opnsense/scripts/OPNsense/Reticulum/setup.sh",
        "/usr/local/opnsense/scripts/OPNsense/Reticulum/status.py",
        "/usr/local/opnsense/scripts/OPNsense/Reticulum/diagnostics.py",
        "/usr/local/opnsense/scripts/OPNsense/Reticulum/utilities.py",
    ]

    @pytest.mark.parametrize("path", SCRIPTS)
    def test_script_executable(self, ssh, path):
        """Script file is executable."""
        _, _, rc = ssh(f"test -x {path}")
        assert rc == 0, f"{path} is not executable"

    @pytest.mark.parametrize("path", SCRIPTS)
    def test_script_exists(self, ssh, path):
        """Script file exists."""
        _, _, rc = ssh(f"test -f {path}")
        assert rc == 0, f"{path} does not exist"


class TestGroupMembership:
    """Verify _reticulum user group memberships."""

    def test_reticulum_in_dialer_group(self, ssh):
        """_reticulum user is member of dialer group for serial access."""
        stdout, _, rc = ssh("id -Gn _reticulum")
        assert rc == 0
        groups = stdout.split()
        assert "dialer" in groups, f"_reticulum not in dialer group. Groups: {groups}"

    def test_reticulum_primary_group(self, ssh):
        """_reticulum primary group is _reticulum."""
        stdout, _, rc = ssh("id -gn _reticulum")
        assert rc == 0
        assert stdout.strip() == "_reticulum"
