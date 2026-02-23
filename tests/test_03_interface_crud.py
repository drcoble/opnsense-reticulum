"""Test 03: Interface CRUD operations.

Tests add/get/set/search/toggle/delete for all major interface types.
"""

import pytest

pytestmark = pytest.mark.integration


class TestTCPServerInterface:
    """CRUD operations on TCPServerInterface."""

    @pytest.fixture(autouse=True)
    def setup_interface(self, api):
        """Create a TCPServerInterface for testing, clean up after."""
        self.api = api
        result = api.add_interface({
            "name": "CI TCP Server",
            "interfaceType": "TCPServerInterface",
            "enabled": "1",
            "tcp_server_listen_ip": "0.0.0.0",
            "tcp_server_listen_port": "4242",
        })
        assert result.get("result") == "saved", f"Failed to add interface: {result}"
        self.uuid = result.get("uuid")
        assert self.uuid, f"No UUID returned: {result}"
        yield
        # Cleanup
        try:
            api.del_interface(self.uuid)
        except Exception:
            pass

    def test_get_interface(self):
        """Retrieve the created interface by UUID."""
        resp = self.api.get_interface(self.uuid)
        assert "interface" in resp
        iface = resp["interface"]
        assert iface["name"] == "CI TCP Server"
        assert iface["interfaceType"] == "TCPServerInterface"

    def test_search_interface(self):
        """Interface appears in search results."""
        resp = self.api.search_interfaces()
        assert "rows" in resp
        names = [row.get("name") for row in resp["rows"]]
        assert "CI TCP Server" in names

    def test_update_interface(self):
        """Update the interface port."""
        result = self.api.set_interface(self.uuid, {
            "name": "CI TCP Server",
            "interfaceType": "TCPServerInterface",
            "enabled": "1",
            "tcp_server_listen_port": "5555",
        })
        assert result.get("result") == "saved"

        resp = self.api.get_interface(self.uuid)
        assert resp["interface"]["tcp_server_listen_port"] == "5555"

    def test_toggle_interface(self):
        """Toggle interface disabled then enabled."""
        result = self.api.toggle_interface(self.uuid, enabled=False)
        assert result.get("result") in ("saved", "Toggled")

        resp = self.api.get_interface(self.uuid)
        assert resp["interface"]["enabled"] == "0"

        result = self.api.toggle_interface(self.uuid, enabled=True)
        resp = self.api.get_interface(self.uuid)
        assert resp["interface"]["enabled"] == "1"

    def test_delete_interface(self):
        """Delete the interface."""
        result = self.api.del_interface(self.uuid)
        assert result.get("result") == "deleted"

        # Verify gone from search
        resp = self.api.search_interfaces()
        uuids = [row.get("uuid") for row in resp.get("rows", [])]
        assert self.uuid not in uuids
        # Prevent double-delete in cleanup
        self.uuid = None


class TestAutoInterface:
    """CRUD operations on AutoInterface."""

    @pytest.fixture(autouse=True)
    def setup_interface(self, api):
        self.api = api
        result = api.add_interface({
            "name": "CI Auto Discovery",
            "interfaceType": "AutoInterface",
            "enabled": "1",
            "auto_group_id": "ci-test",
            "auto_discovery_scope": "link",
            "auto_discovery_port": "29716",
            "auto_data_port": "42671",
        })
        assert result.get("result") == "saved", f"Failed to add interface: {result}"
        self.uuid = result.get("uuid")
        assert self.uuid
        yield
        try:
            if self.uuid:
                api.del_interface(self.uuid)
        except Exception:
            pass

    def test_get_auto_interface(self):
        """Retrieve AutoInterface with correct fields."""
        resp = self.api.get_interface(self.uuid)
        iface = resp["interface"]
        assert iface["interfaceType"] == "AutoInterface"
        assert iface["auto_group_id"] == "ci-test"

    def test_update_group_id(self):
        """Update auto_group_id."""
        result = self.api.set_interface(self.uuid, {
            "name": "CI Auto Discovery",
            "interfaceType": "AutoInterface",
            "enabled": "1",
            "auto_group_id": "ci-updated",
        })
        assert result.get("result") == "saved"

        resp = self.api.get_interface(self.uuid)
        assert resp["interface"]["auto_group_id"] == "ci-updated"


class TestUDPInterface:
    """CRUD operations on UDPInterface."""

    @pytest.fixture(autouse=True)
    def setup_interface(self, api):
        self.api = api
        result = api.add_interface({
            "name": "CI UDP Link",
            "interfaceType": "UDPInterface",
            "enabled": "1",
            "udp_listen_ip": "0.0.0.0",
            "udp_listen_port": "4243",
            "udp_forward_ip": "192.168.1.100",
            "udp_forward_port": "4243",
        })
        assert result.get("result") == "saved", f"Failed to add interface: {result}"
        self.uuid = result.get("uuid")
        assert self.uuid
        yield
        try:
            if self.uuid:
                api.del_interface(self.uuid)
        except Exception:
            pass

    def test_get_udp_interface(self):
        """Retrieve UDPInterface with correct fields."""
        resp = self.api.get_interface(self.uuid)
        iface = resp["interface"]
        assert iface["interfaceType"] == "UDPInterface"
        assert iface["udp_listen_port"] == "4243"

    def test_update_forward_port(self):
        """Update UDP forward port."""
        result = self.api.set_interface(self.uuid, {
            "name": "CI UDP Link",
            "interfaceType": "UDPInterface",
            "enabled": "1",
            "udp_forward_port": "5555",
        })
        assert result.get("result") == "saved"

        resp = self.api.get_interface(self.uuid)
        assert resp["interface"]["udp_forward_port"] == "5555"
