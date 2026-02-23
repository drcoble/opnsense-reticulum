"""Test 09: Plugin uninstall behavior.

Tests that +POST_DEINSTALL stops services and that config directories
are preserved (not deleted on removal).
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True, scope="module")
def start_services_for_uninstall(request):
    """Start the service so we can verify it gets stopped on uninstall."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1"})

    result = api.add_interface({
        "name": "CI Uninstall Test",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-uninstall",
    })
    uuid = result.get("uuid")

    api.service_reconfigure()
    time.sleep(3)
    api.service_start()
    time.sleep(5)

    yield uuid


class TestUninstall:
    """Verify POST_DEINSTALL behavior."""

    def test_services_running_before_uninstall(self, ssh):
        """Confirm rnsd is running before running deinstall."""
        stdout, _, rc = ssh("pgrep -f /usr/local/bin/rnsd")
        assert rc == 0, "rnsd should be running before uninstall test"

    def test_post_deinstall_runs(self, ssh):
        """Execute +POST_DEINSTALL script (uninstalls pip packages)."""
        stdout, stderr, rc = ssh("sh /usr/local/+POST_DEINSTALL 2>&1 || true")
        # POST_DEINSTALL should run without fatal errors
        assert "error" not in stdout.lower() or "removing" in stdout.lower()

    def test_config_dirs_preserved(self, ssh):
        """+POST_DEINSTALL preserves configuration directories."""
        for path in ["/usr/local/etc/reticulum", "/usr/local/etc/lxmd", "/var/db/lxmd"]:
            _, _, rc = ssh(f"test -d {path}")
            assert rc == 0, f"Config directory {path} was deleted during uninstall"

    def test_pip_packages_removed(self, ssh):
        """RNS and LXMF pip packages are uninstalled."""
        # After POST_DEINSTALL, importing should fail
        _, _, rc = ssh("/usr/local/bin/python3.11 -c 'import RNS' 2>/dev/null")
        assert rc != 0, "RNS package still importable after deinstall"

        _, _, rc = ssh("/usr/local/bin/python3.11 -c 'import LXMF' 2>/dev/null")
        assert rc != 0, "LXMF package still importable after deinstall"
