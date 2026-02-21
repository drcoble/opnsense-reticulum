"""Tests that configuration files are generated correctly on reconfigure."""

import time


def test_autointerface_config_generation(api):
    """Adding an AutoInterface and reconfiguring leaves service running."""
    resp = api.post(
        "/api/reticulum/settings/addInterface",
        json={
            "interface": {
                "enabled": "1",
                "name": "CI-AutoIface",
                "interfaceType": "AutoInterface",
                "outgoing": "1",
            }
        },
    )
    assert resp.status_code == 200
    uuid = resp.json().get("uuid")
    assert uuid

    try:
        resp = api.post("/api/reticulum/service/reconfigure")
        assert resp.status_code == 200
        time.sleep(10)

        status = api.get("/api/reticulum/service/status").json()
        assert status["status"] == "running", f"Service not running: {status}"
    finally:
        api.post(f"/api/reticulum/settings/delInterface/{uuid}")


def test_udp_interface_config_generation(api):
    """Adding a UDPInterface and reconfiguring leaves service running."""
    resp = api.post(
        "/api/reticulum/settings/addInterface",
        json={
            "interface": {
                "enabled": "1",
                "name": "CI-UDPIface",
                "interfaceType": "UDPInterface",
                "outgoing": "1",
                "udp_listen_port": "14300",
            }
        },
    )
    assert resp.status_code == 200
    uuid = resp.json().get("uuid")

    try:
        resp = api.post("/api/reticulum/service/reconfigure")
        assert resp.status_code == 200
        time.sleep(10)

        status = api.get("/api/reticulum/service/status").json()
        assert status["status"] == "running", f"Service not running: {status}"
    finally:
        api.post(f"/api/reticulum/settings/delInterface/{uuid}")
        api.post("/api/reticulum/service/reconfigure")
        time.sleep(5)


def test_propagation_disabled_no_lxmd(api):
    """With propagation disabled, lxmd should not be running."""
    # saveContainerSettings('propagation', 'propagation') expects fields under 'propagation'
    api.post(
        "/api/reticulum/settings/setPropagation",
        json={"propagation": {"enabled": "0", "enable_node": "0"}},
    )
    api.post("/api/reticulum/service/reconfigure")
    time.sleep(8)

    status = api.get("/api/reticulum/service/status").json()
    assert status["status"] == "running"
    assert status.get("lxmd") is False, f"lxmd should not run when propagation disabled: {status}"
