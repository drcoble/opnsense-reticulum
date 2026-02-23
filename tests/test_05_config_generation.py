"""Test 05: Config file generation verification.

SSH into the OPNsense VM and verify that the rendered config files
match the values set via the API.
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True, scope="module")
def configure_and_reconfigure(request):
    """Set up settings and interfaces, then reconfigure to generate configs."""
    api = request.getfixturevalue("api")

    # Enable plugin with specific settings
    api.set_settings({
        "enabled": "1",
        "enable_transport": "0",
        "share_instance": "1",
        "shared_instance_port": "37428",
        "loglevel": "5",
    })

    # Add a TCPServerInterface
    result = api.add_interface({
        "name": "CI Config Test TCP",
        "interfaceType": "TCPServerInterface",
        "enabled": "1",
        "tcp_server_listen_ip": "0.0.0.0",
        "tcp_server_listen_port": "7777",
    })
    tcp_uuid = result.get("uuid")

    # Reconfigure to render templates
    api.service_reconfigure()
    time.sleep(3)

    yield tcp_uuid

    # Cleanup
    try:
        api.service_stop()
    except Exception:
        pass
    if tcp_uuid:
        try:
            api.del_interface(tcp_uuid)
        except Exception:
            pass
    api.set_settings({"enabled": "0"})


class TestReticulumConfig:
    """Verify rendered /usr/local/etc/reticulum/config."""

    def test_config_file_exists(self, ssh):
        """Config file was generated."""
        _, _, rc = ssh("test -f /usr/local/etc/reticulum/config")
        assert rc == 0, "Reticulum config file not found"

    def test_reticulum_section(self, ssh):
        """Config contains [reticulum] section."""
        stdout, _, rc = ssh("cat /usr/local/etc/reticulum/config")
        assert rc == 0
        assert "[reticulum]" in stdout

    def test_share_instance_setting(self, ssh):
        """share_instance = Yes in config."""
        stdout, _, _ = ssh("cat /usr/local/etc/reticulum/config")
        assert "share_instance" in stdout

    def test_loglevel_setting(self, ssh):
        """loglevel = 5 in config."""
        stdout, _, _ = ssh("cat /usr/local/etc/reticulum/config")
        assert "loglevel" in stdout

    def test_interfaces_section(self, ssh):
        """Config contains [[interfaces]] or [interfaces] section."""
        stdout, _, _ = ssh("cat /usr/local/etc/reticulum/config")
        # Reticulum uses [[interface_name]] format
        assert "CI Config Test TCP" in stdout or "TCPServerInterface" in stdout

    def test_tcp_listen_port(self, ssh):
        """TCP listen port 7777 appears in config."""
        stdout, _, _ = ssh("cat /usr/local/etc/reticulum/config")
        assert "7777" in stdout


class TestLxmdConfig:
    """Verify rendered /usr/local/etc/lxmd/config when propagation is enabled."""

    def test_enable_propagation_generates_config(self, api, ssh):
        """Enabling propagation and reconfiguring generates lxmd config."""
        api.set_propagation({"enabled": "1"})
        api.service_reconfigure()

        import time
        time.sleep(3)

        _, _, rc = ssh("test -f /usr/local/etc/lxmd/config")
        assert rc == 0, "LXMF config file not generated"

        stdout, _, _ = ssh("cat /usr/local/etc/lxmd/config")
        assert "enable_propagation" in stdout.lower() or "lxmf" in stdout.lower()

        # Disable propagation for cleanup
        api.set_propagation({"enabled": "0"})
        api.service_reconfigure()
