"""Tests that configuration files are generated correctly on reconfigure."""

import time

import pytest

pytestmark = pytest.mark.integration


def test_autointerface_config_generation(api):
    """Adding an AutoInterface and reconfiguring leaves service running."""
    data = api.add_interface({
        "enabled": "1",
        "name": "CI-AutoIface",
        "interfaceType": "AutoInterface",
        "outgoing": "1",
    })
    uuid = data.get("uuid")
    assert uuid, f"Expected uuid in response: {data}"

    try:
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(10)

        status = api.service_status()
        assert status["status"] == "running", f"Service not running: {status}"
    finally:
        api.del_interface(uuid)


def test_udp_interface_config_generation(api):
    """Adding a UDPInterface and reconfiguring leaves service running."""
    data = api.add_interface({
        "enabled": "1",
        "name": "CI-UDPIface",
        "interfaceType": "UDPInterface",
        "outgoing": "1",
        "udp_listen_port": "14300",
    })
    uuid = data.get("uuid")
    assert uuid, f"Expected uuid in response: {data}"

    try:
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(10)

        status = api.service_status()
        assert status["status"] == "running", f"Service not running: {status}"
    finally:
        api.del_interface(uuid)
        api.service_reconfigure()
        time.sleep(5)
