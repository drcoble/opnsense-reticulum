"""
Template Output Validation Tests — T-101 through T-112

Tests render Jinja2 templates with fixture data and compare against expected output.
Run with: pytest tests/template/
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import REFERENCE_DIR

pytestmark = pytest.mark.unit


def load_reference(name: str) -> str:
    path = os.path.join(REFERENCE_DIR, name)
    with open(path) as f:
        return f.read()


def norm(s: str) -> str:
    """Normalize whitespace for comparison."""
    return "\n".join(line.rstrip() for line in s.strip().splitlines())


# ---------------------------------------------------------------------------
# T-101: Minimal rnsd config (no interfaces, all defaults)
# ---------------------------------------------------------------------------

def test_T101_minimal_rnsd_config(render_rnsd):
    """T-101: Minimal rnsd config with defaults produces correct [reticulum] and [logging] sections."""
    output = render_rnsd()
    assert "[reticulum]" in output
    assert "enable_transport = False" in output
    assert "share_instance = True" in output
    assert "shared_instance_port = 37428" in output
    assert "instance_control_port = 37429" in output
    assert "panic_on_interface_error = False" in output
    assert "[logging]" in output
    assert "loglevel = 4" in output
    # No interface sections
    assert "[[" not in output


# ---------------------------------------------------------------------------
# T-102: Single TCPServerInterface
# ---------------------------------------------------------------------------

def test_T102_tcp_server_interface(render_rnsd):
    """T-102: Single TCPServerInterface generates correct section with listen_ip and listen_port."""
    iface = {
        "enabled": "1",
        "name": "My TCP Server",
        "type": "TCPServerInterface",
        "listen_ip": "0.0.0.0",
        "listen_port": "4242",
    }
    output = render_rnsd(interfaces=[iface])
    assert "[[My TCP Server]]" in output
    assert "type = TCPServerInterface" in output
    assert "listen_ip = 0.0.0.0" in output
    assert "listen_port = 4242" in output


# ---------------------------------------------------------------------------
# T-103: One of each interface type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("iface_type,extra_fields,expected_key", [
    ("TCPServerInterface", {"listen_port": "4242"}, "listen_port = 4242"),
    ("TCPClientInterface", {"target_host": "example.com", "target_port": "4242"}, "target_host = example.com"),
    ("UDPInterface", {"listen_port": "4242", "forward_ip": "192.168.1.1", "forward_port": "4242"}, "forward_ip = 192.168.1.1"),
    ("AutoInterface", {}, "type = AutoInterface"),
    ("RNodeInterface", {"port": "/dev/cuaU0", "frequency": "915000000", "bandwidth": "125000", "txpower": "14", "spreadingfactor": "8", "codingrate": "5"}, "frequency = 915000000"),
    ("RNodeMultiInterface", {"port": "/dev/cuaU0", "sub_interfaces_raw": "[[[SubA]]]\n  frequency = 915000000"}, "port = /dev/cuaU0"),
    ("SerialInterface", {"port": "/dev/cuaU0", "speed": "9600"}, "speed = 9600"),
    ("KISSInterface", {"port": "/dev/cuaU0", "speed": "9600"}, "type = KISSInterface"),
    ("AX25KISSInterface", {"port": "/dev/cuaU0", "speed": "9600", "callsign": "N0CALL", "ssid": "0"}, "callsign = N0CALL"),
    ("PipeInterface", {"command": "/usr/local/bin/mybridge"}, "command = /usr/local/bin/mybridge"),
    ("I2PInterface", {}, "type = I2PInterface"),
    ("BackboneInterface", {"listen_port": "4242"}, "type = BackboneInterface"),
])
def test_T103_interface_types(render_rnsd, iface_type, extra_fields, expected_key):
    """T-103: Each interface type generates the correct type field and type-specific fields."""
    iface = {"enabled": "1", "name": f"Test {iface_type}", "type": iface_type}
    iface.update(extra_fields)
    output = render_rnsd(interfaces=[iface])
    assert f"[[Test {iface_type}]]" in output
    assert f"type = {iface_type}" in output
    assert expected_key in output


def test_T103_no_cross_contamination(render_rnsd):
    """T-103: Multiple interface types in one config don't mix type-specific fields."""
    ifaces = [
        {"enabled": "1", "name": "TCP", "type": "TCPServerInterface", "listen_port": "4242"},
        {"enabled": "1", "name": "RNode", "type": "RNodeInterface", "port": "/dev/cuaU0",
         "frequency": "915000000", "bandwidth": "125000", "txpower": "14",
         "spreadingfactor": "8", "codingrate": "5"},
    ]
    output = render_rnsd(interfaces=ifaces)
    # Find each section
    tcp_section = output[output.index("[[TCP]]"):output.index("[[RNode]]")]
    rnode_section = output[output.index("[[RNode]]"):]
    # TCP section should not have frequency
    assert "frequency" not in tcp_section
    # RNode section should not have listen_port
    assert "listen_port" not in rnode_section


# ---------------------------------------------------------------------------
# T-104: RNodeInterface with all fields
# ---------------------------------------------------------------------------

def test_T104_rnode_all_fields(render_rnsd):
    """T-104: RNodeInterface renders all optional fields when set."""
    iface = {
        "enabled": "1",
        "name": "LoRa Node",
        "type": "RNodeInterface",
        "port": "/dev/cuaU0",
        "frequency": "915000000",
        "bandwidth": "125000",
        "txpower": "14",
        "spreadingfactor": "8",
        "codingrate": "5",
        "airtime_limit_long": "70",
        "airtime_limit_short": "15",
        "id_callsign": "N0CALL",
        "id_interval": "600",
        "flow_control": "0",
    }
    output = render_rnsd(interfaces=[iface])
    assert "port = /dev/cuaU0" in output
    assert "frequency = 915000000" in output
    assert "bandwidth = 125000" in output
    assert "txpower = 14" in output
    assert "spreadingfactor = 8" in output
    assert "codingrate = 5" in output
    assert "airtime_limit_long = 70" in output
    assert "airtime_limit_short = 15" in output
    assert "id_callsign = N0CALL" in output
    assert "id_interval = 600" in output


# ---------------------------------------------------------------------------
# T-105: RNodeMultiInterface raw block emitted verbatim
# ---------------------------------------------------------------------------

def test_T105_rnodemulti_raw_block(render_rnsd):
    """T-105: sub_interfaces_raw is emitted verbatim into the config."""
    raw = "[[[SubA]]]\n  frequency = 915000000\n  bandwidth = 125000"
    iface = {
        "enabled": "1",
        "name": "MultiNode",
        "type": "RNodeMultiInterface",
        "port": "/dev/cuaU0",
        "sub_interfaces_raw": raw,
    }
    output = render_rnsd(interfaces=[iface])
    assert "[[[SubA]]]" in output
    assert "frequency = 915000000" in output
    assert "bandwidth = 125000" in output


# ---------------------------------------------------------------------------
# T-106: Boolean field mapping
# ---------------------------------------------------------------------------

def test_T106_bool_true_rnsd(render_rnsd):
    """T-106: rnsd boolean: '1' maps to True."""
    output = render_rnsd(general={"enable_transport": "1"})
    assert "enable_transport = True" in output


def test_T106_bool_false_rnsd(render_rnsd):
    """T-106: rnsd boolean: '0' maps to False."""
    output = render_rnsd(general={"enable_transport": "0"})
    assert "enable_transport = False" in output


def test_T106_bool_true_lxmf(render_lxmf):
    """T-106: lxmd boolean: '1' maps to yes."""
    output = render_lxmf(lxmf={"lxmf_announce_at_start": "1"})
    assert "announce_at_start = yes" in output


def test_T106_bool_false_lxmf(render_lxmf):
    """T-106: lxmd boolean: '0' maps to no."""
    output = render_lxmf(lxmf={"lxmf_announce_at_start": "0"})
    assert "announce_at_start = no" in output


# ---------------------------------------------------------------------------
# T-107: Empty optional fields are omitted
# ---------------------------------------------------------------------------

def test_T107_empty_optional_fields_omitted(render_rnsd):
    """T-107: Optional fields not set are absent from output."""
    iface = {
        "enabled": "1",
        "name": "Basic TCP",
        "type": "TCPServerInterface",
        "listen_port": "4242",
    }
    output = render_rnsd(interfaces=[iface])
    # These are optional and not set — should not appear
    assert "network_name" not in output
    assert "passphrase" not in output
    assert "ifac_size" not in output
    assert "announce_cap" not in output
    assert "prefer_ipv6" not in output
    assert "discoverable" not in output
    assert "id_callsign" not in output


# ---------------------------------------------------------------------------
# T-108: CSV list rendering (static_peers)
# ---------------------------------------------------------------------------

def test_T108_csv_list_static_peers(render_lxmf):
    """T-108: static_peers CSV value rendered as-is (comma-separated on one line)."""
    peers = "abc123def456789012345678901234ab,fedcba0987654321fedcba0987654321"
    output = render_lxmf(lxmf={"enable_node": "1", "static_peers": peers})
    assert f"static_peers = {peers}" in output


# ---------------------------------------------------------------------------
# T-109: Minimal lxmd config (propagation disabled)
# ---------------------------------------------------------------------------

def test_T109_minimal_lxmd_config(render_lxmf):
    """T-109: Minimal lxmd config with propagation disabled."""
    output = render_lxmf()
    assert "[lxmf]" in output
    assert "[propagation]" in output
    assert "enable_node = no" in output
    # Propagation-only fields should not appear
    assert "announce_interval" not in output.split("[propagation]")[1].split("[logging]")[0]
    assert "message_storage_limit" not in output


# ---------------------------------------------------------------------------
# T-110: Full lxmd config with propagation enabled
# ---------------------------------------------------------------------------

def test_T110_full_lxmd_propagation(render_lxmf):
    """T-110: Full lxmd config with all propagation fields rendered."""
    output = render_lxmf(lxmf={
        "enable_node": "1",
        "node_name": "My Prop Node",
        "announce_interval": "360",
        "announce_at_start": "1",
        "message_storage_limit": "500",
        "propagation_message_max_size": "256",
        "propagation_sync_max_size": "10240",
        "stamp_cost_target": "16",
        "stamp_cost_flexibility": "3",
        "peering_cost": "18",
        "remote_peering_cost_max": "26",
        "max_peers": "20",
        "autopeer": "1",
        "autopeer_maxdepth": "6",
        "from_static_only": "0",
        "auth_required": "0",
    })
    assert "enable_node = yes" in output
    assert "node_name = My Prop Node" in output
    assert "announce_interval = 360" in output
    assert "message_storage_limit = 500" in output
    assert "propagation_message_max_accepted_size = 256" in output
    assert "propagation_sync_max_accepted_size = 10240" in output
    assert "propagation_stamp_cost_target = 16" in output
    assert "propagation_stamp_cost_flexibility = 3" in output
    assert "max_peers = 20" in output
    assert "autopeer = yes" in output
    assert "autopeer_maxdepth = 6" in output


# ---------------------------------------------------------------------------
# T-111: ACL file (lxmf_allowed) — one hash per line
# ---------------------------------------------------------------------------

def test_T111_acl_file_one_hash_per_line(render_allowed):
    """T-111: allowed_identities CSV renders to one hash per line in the ACL file."""
    hashes = "aaaabbbbccccdddd1111222233334444,bbbbccccddddeeee5555666677778888"
    output = render_allowed(lxmf={"allowed_identities": hashes})
    lines = [ln.strip() for ln in output.strip().splitlines() if ln.strip()]
    assert lines == [
        "aaaabbbbccccdddd1111222233334444",
        "bbbbccccddddeeee5555666677778888",
    ]


def test_T111_acl_empty(render_allowed):
    """T-111: Empty allowed_identities produces empty file."""
    output = render_allowed()
    assert output.strip() == ""


# ---------------------------------------------------------------------------
# T-112: rc.conf.d templates
# ---------------------------------------------------------------------------

def test_T112_rnsd_enabled(render_rc_rnsd):
    """T-112: rnsd enabled → rnsd_enable=YES."""
    output = render_rc_rnsd(general={"enabled": "1"})
    assert 'rnsd_enable="YES"' in output


def test_T112_rnsd_disabled(render_rc_rnsd):
    """T-112: rnsd disabled → rnsd_enable=NO."""
    output = render_rc_rnsd(general={"enabled": "0"})
    assert 'rnsd_enable="NO"' in output


def test_T112_lxmd_enabled_with_rnsd(render_rc_lxmd):
    """T-112: lxmd enabled + rnsd enabled → lxmd_enable=YES."""
    output = render_rc_lxmd(
        general={"enabled": "1"},
        lxmf={"enabled": "1"}
    )
    assert 'lxmd_enable="YES"' in output


def test_T112_lxmd_blocked_without_rnsd(render_rc_lxmd):
    """T-112: lxmd enabled but rnsd disabled → lxmd_enable=NO (template gate)."""
    output = render_rc_lxmd(
        general={"enabled": "0"},
        lxmf={"enabled": "1"}
    )
    assert 'lxmd_enable="NO"' in output


def test_T112_lxmd_propagation_flag(render_rc_lxmd):
    """T-112: lxmd_propagation=YES when enable_node=1."""
    output = render_rc_lxmd(
        general={"enabled": "1"},
        lxmf={"enabled": "1", "enable_node": "1"}
    )
    assert 'lxmd_propagation="YES"' in output


def test_T112_lxmd_propagation_no(render_rc_lxmd):
    """T-112: lxmd_propagation=NO when enable_node=0."""
    output = render_rc_lxmd(
        general={"enabled": "1"},
        lxmf={"enabled": "1", "enable_node": "0"}
    )
    assert 'lxmd_propagation="NO"' in output


# ---------------------------------------------------------------------------
# Additional: disabled interface excluded from output
# ---------------------------------------------------------------------------

def test_disabled_interface_excluded(render_rnsd):
    """Disabled interface (enabled=0) must not appear in rendered config."""
    ifaces = [
        {"enabled": "0", "name": "Hidden", "type": "TCPServerInterface", "listen_port": "4242"},
        {"enabled": "1", "name": "Visible", "type": "TCPServerInterface", "listen_port": "5555"},
    ]
    output = render_rnsd(interfaces=ifaces)
    assert "[[Hidden]]" not in output
    assert "[[Visible]]" in output
