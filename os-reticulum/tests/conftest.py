"""
Shared pytest fixtures for os-reticulum test suite.
"""
import os
import pytest
from jinja2 import Environment, BaseLoader


TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "src", "opnsense", "service", "templates", "OPNsense", "Reticulum"
)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")


def load_template(name: str) -> str:
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path) as f:
        return f.read()


def render(template_name: str, context: dict) -> str:
    """Render a Jinja2 template with the given OPNsense-style context dict."""
    src = load_template(template_name)
    env = Environment(loader=BaseLoader(), keep_trailing_newline=True)
    tmpl = env.from_string(src)
    return tmpl.render(**context)


def make_ctx(general=None, interfaces=None, lxmf=None) -> dict:
    """Build the OPNsense template context dict."""
    base_general = {
        "enabled": "0",
        "enable_transport": "0",
        "share_instance": "1",
        "shared_instance_port": "37428",
        "instance_control_port": "37429",
        "panic_on_interface_error": "0",
        "respond_to_probes": "0",
        "enable_remote_management": "0",
        "remote_management_allowed": "",
        "rpc_key": "",
        "loglevel": "4",
        "logfile": "",
    }
    base_lxmf = {
        "enabled": "0",
        "display_name": "Anonymous Peer",
        "lxmf_announce_at_start": "0",
        "lxmf_announce_interval": "",
        "delivery_transfer_max_size": "1000",
        "on_inbound": "",
        "enable_node": "0",
        "node_name": "",
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
        "static_peers": "",
        "auth_required": "0",
        "control_allowed": "",
        "prioritise_destinations": "",
        "allowed_identities": "",
        "ignored_destinations": "",
        "loglevel": "4",
        "logfile": "",
    }

    if general:
        base_general.update(general)
    if lxmf:
        base_lxmf.update(lxmf)

    ctx = {"OPNsense": {"Reticulum": {"general": base_general, "lxmf": base_lxmf}}}

    if interfaces is not None:
        ctx["OPNsense"]["Reticulum"]["interfaces"] = {"interface": interfaces}

    return ctx


@pytest.fixture
def render_rnsd():
    def _render(general=None, interfaces=None):
        ctx = make_ctx(general=general, interfaces=interfaces)
        return render("reticulum_config.j2", ctx)
    return _render


@pytest.fixture
def render_lxmf():
    def _render(lxmf=None, general=None):
        ctx = make_ctx(general=general, lxmf=lxmf)
        return render("lxmf_config.j2", ctx)
    return _render


@pytest.fixture
def render_rc_rnsd():
    def _render(general=None):
        ctx = make_ctx(general=general)
        return render("rc.conf.d_rnsd.j2", ctx)
    return _render


@pytest.fixture
def render_rc_lxmd():
    def _render(general=None, lxmf=None):
        ctx = make_ctx(general=general, lxmf=lxmf)
        return render("rc.conf.d_lxmd.j2", ctx)
    return _render


@pytest.fixture
def render_allowed():
    def _render(lxmf=None):
        ctx = make_ctx(lxmf=lxmf)
        return render("lxmf_allowed.j2", ctx)
    return _render
