"""Test 13: Real Reticulum node connectivity.

Tests that the OPNsense plugin can connect to a real peer Reticulum node,
discover paths, and probe destinations. Requires RUNNER_IP and
RETICULUM_PEER_HASH environment variables to be set (done automatically
by the CI workflow which starts a peer rnsd on the runner).

Tests in this module skip automatically when RUNNER_IP is absent, making
them safe to run in local development environments.
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def peer_interface_uuid(request, api, runner_ip, reticulum_peer):
    """Create a TCPClientInterface pointing to the CI runner peer node.

    Yields the interface UUID for the peer connection and the peer hash.
    Cleans up after the module completes.
    """
    # Add a TCPClientInterface pointing at the runner peer node
    result = api.add_interface({
        "name": "CI Peer Link",
        "interfaceType": "TCPClientInterface",
        "enabled": "1",
        "tcp_client_target_host": runner_ip,
        "tcp_client_target_port": str(reticulum_peer.port),
    })
    assert result.get("result") == "saved", f"Failed to add peer interface: {result}"
    uuid = result.get("uuid")
    assert uuid, f"No UUID returned for peer interface: {result}"

    # Enable plugin and start service
    api.set_settings({"enabled": "1"})
    api.service_reconfigure()
    time.sleep(3)
    api.service_start()
    time.sleep(8)  # Allow TCP connection + route propagation

    yield uuid

    # Cleanup
    try:
        api.service_stop()
    except Exception:
        pass
    time.sleep(3)
    try:
        api.del_interface(uuid)
    except Exception:
        pass
    api.set_settings({"enabled": "0"})


class TestPeerConnectivity:
    """Live Reticulum peer connectivity tests via TCPClientInterface."""

    def test_rnstatus_shows_peer_interface(self, api, peer_interface_uuid):
        """rnstatus output references the peer TCPClientInterface."""
        resp = api.util_rnstatus(detail=0)
        assert resp.get("status") == "ok"
        output = str(resp.get("data", {}))
        assert "CI Peer Link" in output or "TCPClientInterface" in output, (
            f"Peer interface not visible in rnstatus output: {output[:400]}"
        )

    def test_interface_appears_in_interfaces_detail(self, api, peer_interface_uuid):
        """interfacesDetail lists the peer interface."""
        resp = api.diag_interfaces_detail()
        assert resp.get("status") == "ok"
        output = str(resp.get("data", {}))
        assert "CI Peer Link" in output or "TCPClientInterface" in output, (
            f"Peer interface not found in interfacesDetail: {output[:400]}"
        )

    def test_rnpath_finds_route_to_peer(self, api, reticulum_peer, peer_interface_uuid):
        """rnpath locates a route to the peer destination hash."""
        resp = api.util_rnpath(hash=reticulum_peer.hash)
        assert resp.get("status") == "ok", f"rnpath returned error: {resp}"
        output = str(resp.get("data", {}))
        # rnpath should NOT report "No path" or equivalent when peer is connected
        assert "no path" not in output.lower(), (
            f"rnpath could not find route to peer {reticulum_peer.hash}: {output}"
        )

    def test_rnprobe_peer_responds(self, api, reticulum_peer, peer_interface_uuid):
        """rnprobe successfully probes the peer."""
        resp = api.util_rnprobe(hash=reticulum_peer.hash, timeout=15)
        assert resp.get("status") == "ok", f"rnprobe returned error: {resp}"
        data = resp.get("data", {})
        # A successful probe shows a response time or reachability confirmation
        output = (data.get("output") or data.get("raw") or "").lower()
        assert data.get("success") is not False, (
            f"rnprobe reported failure for peer: {data}"
        )
        assert "unreachable" not in output and "failed" not in output, (
            f"rnprobe could not reach peer: {output}"
        )

    def test_rnid_peer_hash_lookup(self, api, reticulum_peer, peer_interface_uuid):
        """rnid lookup of the peer hash returns non-empty output."""
        resp = api.util_rnid(hash=reticulum_peer.hash)
        assert resp.get("status") == "ok", f"rnid returned error: {resp}"
        data = resp.get("data", {})
        output = data.get("output") or data.get("raw") or ""
        assert output, f"rnid lookup of peer hash returned empty output: {resp}"

    def test_announces_shows_peer_activity(self, api, peer_interface_uuid):
        """announces endpoint has at least one entry after peer connection."""
        resp = api.diag_announces()
        assert resp.get("status") == "ok"
        data = resp.get("data")
        # data may be a list, dict, or raw string — just verify it's non-empty
        assert data, f"No announce data returned: {resp}"

    def test_paths_table_contains_peer(self, api, reticulum_peer, peer_interface_uuid):
        """paths table includes the peer hash after connection."""
        resp = api.diag_paths()
        assert resp.get("status") == "ok"
        output = str(resp.get("data", {}))
        assert reticulum_peer.hash in output or reticulum_peer.hash[:16] in output, (
            f"Peer hash {reticulum_peer.hash} not found in path table: {output[:400]}"
        )
