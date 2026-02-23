"""Test 08: LXMF propagation node lifecycle.

Tests enabling/disabling propagation, lxmd service start/stop,
and config generation for the propagation node.
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True, scope="module")
def prepare_for_propagation(request):
    """Enable plugin with an interface so rnsd can start."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1"})

    result = api.add_interface({
        "name": "CI Prop Test Auto",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-prop-test",
    })
    uuid = result.get("uuid")

    yield uuid

    # Cleanup
    try:
        api.service_stop()
    except Exception:
        pass
    time.sleep(3)
    api.set_propagation({"enabled": "0"})
    if uuid:
        try:
            api.del_interface(uuid)
        except Exception:
            pass
    api.set_settings({"enabled": "0"})


class TestPropagationLifecycle:
    """Enable propagation -> start -> verify lxmd -> stop -> verify stopped."""

    def test_enable_propagation(self, api):
        """Enable propagation node via API."""
        result = api.set_propagation({"enabled": "1"})
        assert result.get("result") == "saved"

    def test_reconfigure_generates_lxmd_config(self, api, ssh):
        """Reconfigure generates lxmd config file."""
        api.set_propagation({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(3)

        _, _, rc = ssh("test -f /usr/local/etc/lxmd/config")
        assert rc == 0, "lxmd config file not generated after enabling propagation"

    def test_lxmd_starts_with_propagation(self, api, ssh, wait_for_service):
        """Start service with propagation enabled -> lxmd should be running."""
        api.set_propagation({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(3)

        api.service_start()
        time.sleep(5)

        def check_lxmd():
            stdout, _, rc = ssh("pgrep -f /usr/local/bin/lxmd")
            return rc == 0

        wait_for_service(check_lxmd, "lxmd started", timeout=30)

    def test_propagation_diagnostics(self, api):
        """Propagation diagnostics returns running=true when lxmd is active."""
        resp = api.diag_propagation()
        assert resp.get("status") == "ok"
        data = resp.get("data", {})
        assert data.get("running") is True

    def test_disable_propagation_stops_lxmd(self, api, ssh):
        """Disable propagation and reconfigure -> lxmd should stop."""
        api.set_propagation({"enabled": "0"})
        api.service_reconfigure()
        time.sleep(5)

        # After disabling, lxmd should not be running
        stdout, _, rc = ssh("pgrep -f /usr/local/bin/lxmd")
        # rc != 0 means lxmd not found (expected)
        assert rc != 0, "lxmd is still running after disabling propagation"

    def test_rnsd_still_running_after_lxmd_stop(self, api, ssh):
        """rnsd should continue running even after lxmd is stopped."""
        stdout, _, rc = ssh("pgrep -f /usr/local/bin/rnsd")
        assert rc == 0, "rnsd stopped unexpectedly when propagation was disabled"

        # Final cleanup: stop services
        api.service_stop()
        time.sleep(3)
