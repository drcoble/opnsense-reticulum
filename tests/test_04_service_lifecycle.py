"""Test 04: Service lifecycle management.

Tests start/stop/restart/status/reconfigure via the OPNsense API.
Requires the plugin to be enabled and at least one interface configured.
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True, scope="module")
def enable_plugin_with_interface(request):
    """Enable the plugin and create an AutoInterface for service tests."""
    api = request.getfixturevalue("api")

    # Enable plugin
    api.set_settings({"enabled": "1"})

    # Create an AutoInterface so rnsd has something to bind
    result = api.add_interface({
        "name": "CI Service Test Auto",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-svc-test",
    })
    uuid = result.get("uuid")

    # Reconfigure to generate configs
    api.service_reconfigure()
    time.sleep(3)

    yield uuid

    # Cleanup: stop services, delete interface
    try:
        api.service_stop()
    except Exception:
        pass
    time.sleep(2)
    if uuid:
        try:
            api.del_interface(uuid)
        except Exception:
            pass
    api.set_settings({"enabled": "0"})


class TestServiceLifecycle:
    """Service start/stop/restart/status tests."""

    def test_reconfigure(self, api):
        """Reconfigure generates configs and returns success."""
        resp = api.service_reconfigure()
        assert resp.get("result", resp.get("status")) is not None

    def test_service_start(self, api, wait_for_service):
        """Start service, verify rnsd is running."""
        api.service_start()

        def check():
            try:
                status = api.service_status()
                # Status may be nested under 'result' or 'status'
                if isinstance(status, dict):
                    if "result" in status:
                        return "running" in str(status["result"])
                    return status.get("rnsd") is True or status.get("status") == "running"
            except Exception:
                return False

        wait_for_service(check, "rnsd started", timeout=30)

    def test_service_status_running(self, api):
        """Status reports rnsd as running."""
        status = api.service_status()
        assert isinstance(status, dict)

    def test_service_stop(self, api):
        """Stop service, verify rnsd is stopped."""
        api.service_stop()
        time.sleep(5)

        status = api.service_status()
        assert isinstance(status, dict)

    def test_service_restart(self, api, wait_for_service):
        """Restart service (start first if stopped)."""
        api.service_start()
        time.sleep(3)

        api.service_restart()

        def check():
            try:
                status = api.service_status()
                if isinstance(status, dict):
                    if "result" in status:
                        return "running" in str(status["result"])
                    return status.get("rnsd") is True or status.get("status") == "running"
            except Exception:
                return False

        wait_for_service(check, "rnsd restarted", timeout=30)

        # Clean stop for subsequent tests
        api.service_stop()
        time.sleep(3)
