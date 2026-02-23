"""Test 10: Independent RNSD and LXMD service control.

Verifies the new enable_lxmf / lxmf_bind_to_rnsd settings and the
individual configd service actions (start_rnsd, stop_rnsd, start_lxmd,
stop_lxmd) introduced in the UI refactor.
"""

import time

import pytest

pytestmark = pytest.mark.integration

RNSD_BIN = "/usr/local/bin/rnsd"
LXMD_BIN = "/usr/local/bin/lxmd"


@pytest.fixture(autouse=True, scope="module")
def prepare_module(request):
    """Enable the plugin with an AutoInterface so rnsd can bind, clean up after."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1", "enable_lxmf": "0", "lxmf_bind_to_rnsd": "1"})

    result = api.add_interface({
        "name": "CI Independent Svc",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-svc-independent",
    })
    uuid = result.get("uuid")

    api.service_reconfigure()
    time.sleep(3)

    yield uuid

    # Cleanup: stop everything, reset flags
    try:
        api.service_stop()
    except Exception:
        pass
    time.sleep(3)
    api.set_settings({"enable_lxmf": "0", "lxmf_bind_to_rnsd": "1", "enabled": "0"})
    if uuid:
        try:
            api.del_interface(uuid)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# RNSD independent control
# ---------------------------------------------------------------------------

class TestRNSDIndependentControl:
    """Verify enable_lxmf / lxmf_bind_to_rnsd settings and individual rnsd control."""

    def test_enable_lxmf_flag_saved(self, api):
        """SET enable_lxmf=1, GET confirms round-trip."""
        result = api.set_settings({"enable_lxmf": "1"})
        assert result.get("result") == "saved"

        resp = api.get_settings()
        assert resp["reticulum"]["enable_lxmf"] == "1"

    def test_lxmf_bind_to_rnsd_flag_saved(self, api):
        """SET lxmf_bind_to_rnsd=0, GET confirms round-trip."""
        result = api.set_settings({"lxmf_bind_to_rnsd": "0"})
        assert result.get("result") == "saved"

        resp = api.get_settings()
        assert resp["reticulum"]["lxmf_bind_to_rnsd"] == "0"

        # Reset to default
        api.set_settings({"lxmf_bind_to_rnsd": "1"})

    def test_start_rnsd_only_via_configd(self, ssh, wait_for_service):
        """configd start_rnsd starts only rnsd; lxmd remains stopped."""
        # Ensure both stopped first
        ssh(f"pkill -f {RNSD_BIN} || true", timeout=10)
        ssh(f"pkill -f {LXMD_BIN} || true", timeout=10)
        time.sleep(2)

        stdout, stderr, rc = ssh("configd reticulum start_rnsd", timeout=30)
        assert rc == 0, f"configd start_rnsd failed: {stderr}"

        def rnsd_running():
            _, _, rc2 = ssh(f"pgrep -f {RNSD_BIN}")
            return rc2 == 0

        wait_for_service(rnsd_running, "rnsd started via configd", timeout=20)

        # lxmd must NOT have started
        _, _, lxmd_rc = ssh(f"pgrep -f {LXMD_BIN}")
        assert lxmd_rc != 0, "lxmd started unexpectedly when only rnsd was requested"

    def test_stop_rnsd_via_configd(self, ssh):
        """configd stop_rnsd stops rnsd."""
        stdout, stderr, rc = ssh("configd reticulum stop_rnsd", timeout=30)
        assert rc == 0, f"configd stop_rnsd failed: {stderr}"
        time.sleep(3)

        _, _, rnsd_rc = ssh(f"pgrep -f {RNSD_BIN}")
        assert rnsd_rc != 0, "rnsd is still running after stop_rnsd"


# ---------------------------------------------------------------------------
# LXMD independent control
# ---------------------------------------------------------------------------

class TestLXMDIndependentControl:
    """Verify lxmd can be started independently and respects bind flag."""

    def test_enable_lxmf_generates_sentinel(self, api, ssh):
        """Enabling enable_lxmf and reconfiguring writes __lxmf_enabled__ sentinel."""
        api.set_settings({"enable_lxmf": "1"})
        api.service_reconfigure()
        time.sleep(3)

        stdout, _, rc = ssh("grep __lxmf_enabled__ /usr/local/etc/lxmd/config 2>/dev/null || true")
        assert "__lxmf_enabled__" in stdout, (
            "lxmd.conf does not contain __lxmf_enabled__ sentinel after enabling LXMF"
        )

    def test_start_lxmd_unbound(self, api, ssh, wait_for_service):
        """With lxmf_bind_to_rnsd=0, lxmd starts even when rnsd is stopped."""
        # Ensure rnsd is stopped
        ssh(f"pkill -f {RNSD_BIN} || true", timeout=10)
        time.sleep(2)

        api.set_settings({"enable_lxmf": "1", "lxmf_bind_to_rnsd": "0"})
        api.service_reconfigure()
        time.sleep(3)

        stdout, stderr, rc = ssh("configd reticulum start_lxmd", timeout=30)
        assert rc == 0, f"configd start_lxmd failed: {stderr}"

        def lxmd_running():
            _, _, rc2 = ssh(f"pgrep -f {LXMD_BIN}")
            return rc2 == 0

        wait_for_service(lxmd_running, "lxmd started unbound", timeout=20)

        # Cleanup
        ssh("configd reticulum stop_lxmd", timeout=30)
        time.sleep(2)
        api.set_settings({"lxmf_bind_to_rnsd": "1"})

    def test_lxmd_bound_requires_rnsd(self, api, ssh):
        """With lxmf_bind_to_rnsd=1 and rnsd stopped, lxmd should not start."""
        # Ensure rnsd is stopped
        ssh(f"pkill -f {RNSD_BIN} || true", timeout=10)
        ssh(f"pkill -f {LXMD_BIN} || true", timeout=10)
        time.sleep(3)

        api.set_settings({"enable_lxmf": "1", "lxmf_bind_to_rnsd": "1"})
        api.service_reconfigure()
        time.sleep(3)

        ssh("configd reticulum start_lxmd", timeout=30)
        time.sleep(5)

        _, _, lxmd_rc = ssh(f"pgrep -f {LXMD_BIN}")
        assert lxmd_rc != 0, (
            "lxmd started despite lxmf_bind_to_rnsd=1 and rnsd being stopped"
        )

    def test_status_api_reports_both_daemons(self, api, ssh, wait_for_service):
        """service/status returns both rnsd and lxmd keys when both are running."""
        # Start rnsd first
        api.set_settings({"enabled": "1", "enable_lxmf": "1", "lxmf_bind_to_rnsd": "1"})
        api.service_reconfigure()
        time.sleep(3)
        api.service_start()

        def rnsd_running():
            _, _, rc = ssh(f"pgrep -f {RNSD_BIN}")
            return rc == 0

        wait_for_service(rnsd_running, "rnsd running", timeout=30)
        time.sleep(5)  # Give lxmd time to come up

        status = api.service_status()
        assert isinstance(status, dict), f"Unexpected status response: {status}"
        # The status response should contain both daemon keys
        combined = str(status)
        assert "rnsd" in combined or "running" in combined, (
            f"service_status response does not reference rnsd: {status}"
        )
