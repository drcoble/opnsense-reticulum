"""Test 01: Plugin installation verification.

Verifies that +POST_INSTALL created the expected user, group, directories,
permissions, and that configd recognizes the plugin actions.
"""

import pytest

pytestmark = pytest.mark.integration


class TestPluginInstall:
    """Verify plugin post-install artifacts."""

    def test_service_user_exists(self, ssh):
        """_reticulum user exists with UID 920."""
        stdout, _, rc = ssh("id -u _reticulum")
        assert rc == 0, "User _reticulum does not exist"
        assert stdout.strip() == "920", f"Expected UID 920, got {stdout}"

    def test_service_group_exists(self, ssh):
        """_reticulum group exists with GID 920."""
        stdout, _, rc = ssh("pw groupshow _reticulum -o 2>/dev/null | cut -d: -f3")
        assert rc == 0
        assert stdout.strip() == "920", f"Expected GID 920, got {stdout}"

    def test_dialer_group_membership(self, ssh):
        """_reticulum is a member of the dialer group."""
        stdout, _, rc = ssh("id -Gn _reticulum")
        assert rc == 0
        assert "dialer" in stdout, f"_reticulum not in dialer group: {stdout}"

    def test_config_dir_exists(self, ssh):
        """/usr/local/etc/reticulum directory exists with correct ownership."""
        stdout, _, rc = ssh("stat -f '%Su:%Sg %Lp' /usr/local/etc/reticulum")
        assert rc == 0
        assert "_reticulum:_reticulum" in stdout
        assert "750" in stdout

    def test_lxmd_config_dir_exists(self, ssh):
        """/usr/local/etc/lxmd directory exists with correct ownership."""
        stdout, _, rc = ssh("stat -f '%Su:%Sg %Lp' /usr/local/etc/lxmd")
        assert rc == 0
        assert "_reticulum:_reticulum" in stdout
        assert "750" in stdout

    def test_messagestore_dir_exists(self, ssh):
        """/var/db/lxmd/messagestore directory exists."""
        stdout, _, rc = ssh("stat -f '%Su:%Sg %Lp' /var/db/lxmd/messagestore")
        assert rc == 0
        assert "_reticulum:_reticulum" in stdout
        assert "750" in stdout

    def test_log_dir_exists(self, ssh):
        """/var/log/reticulum directory exists."""
        stdout, _, rc = ssh("stat -f '%Su:%Sg %Lp' /var/log/reticulum")
        assert rc == 0
        assert "_reticulum:_reticulum" in stdout
        assert "750" in stdout

    def test_setup_sh_executable(self, ssh):
        """setup.sh is executable."""
        _, _, rc = ssh("test -x /usr/local/opnsense/scripts/OPNsense/Reticulum/setup.sh")
        assert rc == 0, "setup.sh is not executable"

    def test_status_py_executable(self, ssh):
        """status.py is executable."""
        _, _, rc = ssh("test -x /usr/local/opnsense/scripts/OPNsense/Reticulum/status.py")
        assert rc == 0, "status.py is not executable"

    def test_diagnostics_py_executable(self, ssh):
        """diagnostics.py is executable."""
        _, _, rc = ssh("test -x /usr/local/opnsense/scripts/OPNsense/Reticulum/diagnostics.py")
        assert rc == 0, "diagnostics.py is not executable"

    def test_configd_actions_registered(self, ssh):
        """configd action definitions are in place."""
        _, _, rc = ssh("test -f /usr/local/opnsense/service/conf/actions.d/actions_reticulum.conf")
        assert rc == 0, "actions_reticulum.conf not found"

    def test_rns_installed(self, ssh):
        """Reticulum (RNS) Python package is installed."""
        stdout, _, rc = ssh("/usr/local/bin/python3.11 -c 'import RNS; print(RNS.__version__)'")
        assert rc == 0, f"RNS not installed: {stdout}"

    def test_lxmf_installed(self, ssh):
        """LXMF Python package is installed."""
        stdout, _, rc = ssh("/usr/local/bin/python3.11 -c 'import LXMF; print(LXMF.__version__)'")
        assert rc == 0, f"LXMF not installed: {stdout}"
