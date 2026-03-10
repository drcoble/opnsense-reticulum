"""
Shared pytest fixtures for os-reticulum test suite.

Fixtures provided
-----------------
jinja2_env        — A configured Jinja2 Environment (FileSystemLoader pointing at
                    the Reticulum templates directory). Use this when you need to
                    load templates by name without going through make_ctx.

sample_model_xml  — Path to the canonical Reticulum.xml model file. Useful for
                    tests that introspect field types, masks, and defaults.

render_template   — A callable fixture (template_name, context) -> str that
                    renders any template in the Reticulum templates directory
                    with an arbitrary context dict. Lower-level than render_rnsd
                    et al.; useful for security and edge-case tests.

render_rnsd       — Renders reticulum_config.j2 with optional general/interfaces.
render_lxmf       — Renders lxmf_config.j2 with optional general/lxmf.
render_rc_rnsd    — Renders rc.conf.d_rnsd.j2 with optional general.
render_rc_lxmd    — Renders rc.conf.d_lxmd.j2 with optional general/lxmf.
render_allowed    — Renders lxmf_allowed.j2 with optional lxmf.
"""
import os
import xml.etree.ElementTree as ET
import pytest
from jinja2 import Environment, FileSystemLoader, BaseLoader


TEMPLATES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..", "src", "opnsense", "service", "templates", "OPNsense", "Reticulum"
))
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")

MODEL_XML_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..", "src", "opnsense", "mvc", "app", "models",
    "OPNsense", "Reticulum", "Reticulum.xml"
))


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


# ---------------------------------------------------------------------------
# New raw fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def jinja2_env():
    """
    A Jinja2 Environment backed by a FileSystemLoader pointed at the Reticulum
    templates directory.  Tests that need to load templates by filename (rather
    than rendering through make_ctx) should use this fixture.

    Example::

        def test_something(jinja2_env):
            tmpl = jinja2_env.get_template("reticulum_config.j2")
            output = tmpl.render(**ctx)
    """
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
    )


@pytest.fixture(scope="session")
def sample_model_xml():
    """
    Returns the parsed ElementTree root of Reticulum.xml.

    Useful for tests that verify field types, masks, required flags, and
    default values without needing a live OPNsense VM.

    Example::

        def test_field_type(sample_model_xml):
            field = sample_model_xml.find(".//passphrase")
            assert field.get("type") == "UpdateOnlyTextField"
    """
    tree = ET.parse(MODEL_XML_PATH)
    return tree.getroot()


@pytest.fixture
def render_template(jinja2_env):
    """
    A low-level render helper that loads a template by name from the Reticulum
    templates directory and renders it with the given context dict.

    Unlike the higher-level render_rnsd / render_lxmf fixtures, this fixture
    does not inject default values — callers supply the entire context.

    Example::

        def test_raw_render(render_template):
            ctx = {"OPNsense": {"Reticulum": {"general": {...}, "lxmf": {...}}}}
            output = render_template("reticulum_config.j2", ctx)
            assert "[reticulum]" in output
    """
    def _render(template_name: str, context: dict) -> str:
        tmpl = jinja2_env.get_template(template_name)
        return tmpl.render(**context)
    return _render


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
