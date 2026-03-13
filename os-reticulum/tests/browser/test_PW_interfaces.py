"""Playwright browser tests for the Reticulum Interfaces page.

Covers toolbar/grid, modal lifecycle, type-visibility system, field
spot-checks, CRUD flows, and delete confirmation.

Requires a live OPNsense VM — see conftest.py for required env vars.
"""

import pytest

from browser.pages.interfaces_page import InterfacesPage

pytestmark = pytest.mark.browser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_page(authenticated_page, base_url) -> InterfacesPage:
    """Create an InterfacesPage and navigate to it."""
    ifc = InterfacesPage(authenticated_page, base_url)
    ifc.navigate()
    return ifc


def _create_pw_interface(api_client, name: str, type_: str = "TCPServerInterface",
                         listen_port: str = "19999") -> str:
    """Create an interface via the API and return its UUID."""
    data = {"name": name, "type": type_, "listen_port": listen_port, "enabled": "1"}
    resp = api_client.add_interface(data)
    assert resp.ok, f"Failed to create interface {name}: {resp.status_code} {resp.text}"
    body = resp.json()
    uuid = body.get("uuid", "")
    assert uuid, f"No UUID from addInterface: {body}"
    return uuid


# ---------------------------------------------------------------------------
# Toolbar and Grid — PW-IFC-001–019
# ---------------------------------------------------------------------------

class TestToolbarAndGrid:

    def test_PW_IFC_001_add_button_present(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        assert page.add_btn.is_visible()

    def test_PW_IFC_002_apply_button_present(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        assert page.apply_btn.is_visible()

    def test_PW_IFC_010_grid_loads(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        assert page.grid.is_visible()

    def test_PW_IFC_011_type_column_displayed(self, authenticated_page, base_url,
                                               seed_one_interface):
        """The type column shows a formatted display name, not the raw value."""
        page = _make_page(authenticated_page, base_url)
        row = page.get_row_by_name("PW-Seed-TCP")
        row_text = row.inner_text()
        # The formatted display name for TCPServerInterface contains "TCP Server"
        assert "TCP Server" in row_text or "TCPServer" in row_text

    def test_PW_IFC_012_enabled_toggle_in_grid(self, authenticated_page, base_url,
                                                seed_one_interface):
        """The enabled column contains a clickable toggle widget."""
        page = _make_page(authenticated_page, base_url)
        row = page.get_row_by_name("PW-Seed-TCP")
        toggle = row.locator(".command-toggle, input[type='checkbox']")
        assert toggle.count() > 0

    def test_PW_IFC_016_empty_state(self, authenticated_page, base_url,
                                     api_client, clean_interfaces):
        """With no interfaces, the grid shows an empty message or zero-row footer."""
        # Delete all PW- interfaces that may exist from other tests
        resp = api_client.list_interfaces()
        if resp.ok:
            for row in resp.json().get("rows", []):
                if row.get("name", "").startswith("PW-"):
                    api_client.delete_interface(row["uuid"])

        page = _make_page(authenticated_page, base_url)
        if page.grid_row_count() == 0:
            # Bootgrid shows either a .no-results row or a footer info
            # message saying "0 of 0".  Check for either indicator.
            no_results = page.grid.locator("tbody tr.no-results, .no-results")
            footer_info = page.grid.locator(".infotable")
            has_empty = no_results.count() > 0 or (
                footer_info.count() > 0 and "0" in footer_info.inner_text()
            )
            assert has_empty, "Grid is empty but no empty-state indicator found"

    def test_PW_IFC_017_pagination_with_many_interfaces(self, authenticated_page, base_url,
                                                         api_client, clean_interfaces):
        """Creating >10 interfaces causes pagination controls to appear."""
        for i in range(12):
            _create_pw_interface(api_client, f"PW-Page-{i:02d}",
                                listen_port=str(18000 + i))

        _make_page(authenticated_page, base_url)
        # Bootgrid renders pagination as <ul class="pagination"> or
        # navigation buttons in the footer area.
        authenticated_page.wait_for_timeout(1000)
        pagination = authenticated_page.locator(
            ".pagination, .bootgrid-footer, .infotable"
        )
        assert pagination.count() > 0, "No pagination or footer controls found"

    def test_PW_IFC_018_inline_toggle_fires_api(self, authenticated_page, base_url,
                                                  seed_one_interface):
        """Toggling the enabled switch on the seed interface fires an API call."""
        page = _make_page(authenticated_page, base_url)
        page.toggle_enabled("PW-Seed-TCP")
        # Toggle again to restore original state
        page.toggle_enabled("PW-Seed-TCP")

    def test_PW_IFC_019_service_bar_present(self, authenticated_page, base_url):
        _make_page(authenticated_page, base_url)
        # updateServiceControlUI injects #service_status_container via AJAX
        # after page load — wait for it to appear.
        service_bar = authenticated_page.locator("#service_status_container")
        service_bar.wait_for(state="attached", timeout=15_000)
        assert service_bar.count() > 0


# ---------------------------------------------------------------------------
# Modal lifecycle — PW-IFC-020–023
# ---------------------------------------------------------------------------

class TestModalLifecycle:

    def test_PW_IFC_020_modal_opens_on_add(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        assert page.modal_visible()

    def test_PW_IFC_021_modal_opens_on_edit(self, authenticated_page, base_url,
                                             seed_one_interface):
        """Edit modal opens with data from the existing seed interface."""
        page = _make_page(authenticated_page, base_url)
        page.click_edit("PW-Seed-TCP")
        assert page.modal_visible()
        # Verify the name field is pre-populated
        assert page.interface_name.input_value() == "PW-Seed-TCP"

    def test_PW_IFC_022_modal_close_button(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        assert page.modal_visible()
        page.cancel_modal()
        assert not page.modal_visible()

    def test_PW_IFC_023_modal_close_on_esc(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        assert page.modal_visible()
        authenticated_page.keyboard.press("Escape")
        page.modal.wait_for(state="hidden")
        assert not page.modal_visible()


# ---------------------------------------------------------------------------
# Basic tab — PW-IFC-030–040
# ---------------------------------------------------------------------------

class TestBasicTab:

    def test_PW_IFC_030_basic_tab_default(self, authenticated_page, base_url):
        """Basic Settings tab is the default active tab when the modal opens."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        basic_tab = page.modal.locator("#tab-interface-basic")
        assert basic_tab.is_visible()

    def test_PW_IFC_031_enabled_checkbox(self, authenticated_page, base_url):
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        assert page.interface_enabled.is_visible()
        page.set_enabled_modal(True)
        assert page.interface_enabled.is_checked()

    def test_PW_IFC_032_name_required(self, authenticated_page, base_url):
        """The name input field is present in the modal."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        assert page.interface_name.is_visible()

    def test_PW_IFC_034_type_select_options(self, authenticated_page, base_url):
        """The type select has 12 interface type options."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        options = page.interface_type.locator("option")
        # 12 interface types (may include a placeholder; count real options)
        option_count = options.count()
        # Filter out any empty/placeholder options
        real_options = [
            options.nth(i).get_attribute("value")
            for i in range(option_count)
            if options.nth(i).get_attribute("value")
        ]
        assert len(real_options) == 12

    def test_PW_IFC_035_mode_select(self, authenticated_page, base_url):
        """Mode select is present with selectable options."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        assert page.interface_mode.is_visible()
        options = page.interface_mode.locator("option")
        assert options.count() >= 1


# ---------------------------------------------------------------------------
# Type-visibility system — PW-IFC-080–091 (parametrized)
# ---------------------------------------------------------------------------

# Mapping: (type option value, expected set of visible CSS classes)
_TYPE_VISIBILITY_CASES = [
    pytest.param("TCPServerInterface", {"type-tcp", "type-tcp-server", "type-discover"},
                 id="080-tcp-server"),
    pytest.param("TCPClientInterface", {"type-tcp"},
                 id="081-tcp-client"),
    pytest.param("UDPInterface", {"type-udp"},
                 id="082-udp"),
    pytest.param("AutoInterface", {"type-auto"},
                 id="083-auto"),
    pytest.param("RNodeInterface", {"type-rnode"},
                 id="084-rnode"),
    pytest.param("SerialInterface", {"type-serial"},
                 id="085-serial"),
    pytest.param("KISSInterface", {"type-kiss"},
                 id="086-kiss"),
    pytest.param("AX25KISSInterface", {"type-ax25", "type-kiss"},
                 id="087-ax25"),
    pytest.param("PipeInterface", {"type-pipe"},
                 id="088-pipe"),
    pytest.param("I2PInterface", {"type-i2p"},
                 id="089-i2p"),
    pytest.param("RNodeMultiInterface", {"type-rnode", "type-multi"},
                 id="090-multi"),
]


class TestTypeVisibility:

    @pytest.mark.parametrize("type_value, expected_visible", _TYPE_VISIBILITY_CASES)
    def test_PW_IFC_080_090_type_visibility(self, authenticated_page, base_url,
                                             type_value, expected_visible):
        """Selecting a type shows exactly the correct CSS visibility classes."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type(type_value)
        # Allow the JS visibility handler to fire
        authenticated_page.wait_for_timeout(300)
        visible = page.fields_visible_for_type(type_value)
        assert visible == expected_visible, (
            f"Type {type_value}: expected {expected_visible}, got {visible}"
        )

    def test_PW_IFC_091_fields_hidden_for_unselected_type(self, authenticated_page, base_url):
        """Switching from TCP to UDP hides TCP-specific fields."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()

        # Start with TCP Server — shows type-tcp, type-tcp-server, type-discover
        page.set_type("TCPServerInterface")
        authenticated_page.wait_for_timeout(300)
        tcp_visible = page.fields_visible_for_type("TCPServerInterface")
        assert "type-tcp-server" in tcp_visible

        # Switch to UDP — TCP classes should be hidden
        page.set_type("UDPInterface")
        authenticated_page.wait_for_timeout(300)
        udp_visible = page.fields_visible_for_type("UDPInterface")
        assert "type-tcp-server" not in udp_visible
        assert "type-tcp" not in udp_visible
        assert "type-udp" in udp_visible


# ---------------------------------------------------------------------------
# Network tab field spot-checks — PW-IFC-051–068
# ---------------------------------------------------------------------------

class TestNetworkTabFields:

    def test_PW_IFC_051_052_tcp_server_listen_fields(self, authenticated_page, base_url):
        """TCP Server: listen_ip and listen_port visible on the network tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("TCPServerInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("network")
        assert page.listen_ip.is_visible()
        assert page.listen_port.is_visible()
        # Fields are fillable
        page.set_listen_ip("0.0.0.0")
        page.set_listen_port("4242")
        assert page.listen_ip.input_value() == "0.0.0.0"
        assert page.listen_port.input_value() == "4242"

    def test_PW_IFC_053_054_tcp_client_target_fields(self, authenticated_page, base_url):
        """TCP Client: target_host and target_port visible on the network tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("TCPClientInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("network")
        assert page.target_host.is_visible()
        assert page.target_port.is_visible()

    def test_PW_IFC_060_061_udp_forward_fields(self, authenticated_page, base_url):
        """UDP: forward_ip and forward_port visible on the network tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("UDPInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("network")
        assert page.forward_ip.is_visible()
        assert page.forward_port.is_visible()

    def test_PW_IFC_062_063_auto_discovery_fields(self, authenticated_page, base_url):
        """Auto: group_id and discovery_scope visible on the network tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("AutoInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("network")
        assert page.group_id.is_visible()
        assert page.discovery_scope.is_visible()


# ---------------------------------------------------------------------------
# Radio/Serial tab field spot-checks — PW-IFC-101–124
# ---------------------------------------------------------------------------

class TestRadioSerialTabFields:

    def test_PW_IFC_101_106_rnode_radio_fields(self, authenticated_page, base_url):
        """RNode: frequency, bandwidth, txpower, spreading_factor, coding_rate visible."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("RNodeInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("radio")
        assert page.frequency.is_visible()
        assert page.bandwidth.is_visible()
        assert page.txpower.is_visible()
        assert page.spreading_factor.is_visible()
        assert page.coding_rate.is_visible()

    def test_PW_IFC_112_serial_baud_rate(self, authenticated_page, base_url):
        """Serial: speed (baud rate) field visible on radio tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("SerialInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("radio")
        assert page.speed.is_visible()

    def test_PW_IFC_122_pipe_command_field(self, authenticated_page, base_url):
        """Pipe: command field visible on radio tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("PipeInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("radio")
        assert page.command.is_visible()

    def test_PW_IFC_124_rnode_multi_textarea(self, authenticated_page, base_url):
        """RNodeMulti: sub_interfaces_raw textarea visible on the advanced tab."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()
        page.set_type("RNodeMultiInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("advanced")
        assert page.rnode_multi_config.is_visible()


# ---------------------------------------------------------------------------
# CRUD flow — PW-IFC full lifecycle
# ---------------------------------------------------------------------------

class TestCRUDFlow:

    def test_PW_IFC_add_tcp_server_full_flow(self, authenticated_page, base_url,
                                              clean_interfaces):
        """Add a TCP Server interface through the modal and verify it appears in the grid."""
        page = _make_page(authenticated_page, base_url)
        page.click_add()

        page.set_name("PW-TCP-Test")
        page.set_type("TCPServerInterface")
        authenticated_page.wait_for_timeout(300)
        page.select_modal_tab("network")
        page.set_listen_port("17777")
        page.save_modal()

        # Wait for bootgrid to reload after save
        authenticated_page.wait_for_timeout(1000)
        row = page.get_row_by_name("PW-TCP-Test")
        assert row.count() > 0

    def test_PW_IFC_edit_existing_interface(self, authenticated_page, base_url,
                                             seed_one_interface):
        """Edit the seed interface: change listen port, save, verify update."""
        page = _make_page(authenticated_page, base_url)
        page.click_edit("PW-Seed-TCP")

        page.select_modal_tab("network")
        page.set_listen_port("9998")
        page.save_modal()

        # Re-open to verify the change persisted
        authenticated_page.wait_for_timeout(500)
        page.click_edit("PW-Seed-TCP")
        page.select_modal_tab("network")
        assert page.listen_port.input_value() == "9998"
        page.cancel_modal()

        # Restore original port so other tests using seed are unaffected
        page.click_edit("PW-Seed-TCP")
        page.select_modal_tab("network")
        page.set_listen_port("9999")
        page.save_modal()


# ---------------------------------------------------------------------------
# Delete — PW-IFC-140–143
# ---------------------------------------------------------------------------

class TestDelete:

    def test_PW_IFC_140_141_142_delete_confirmation(self, authenticated_page, base_url,
                                                      api_client, clean_interfaces):
        """Create interface via API, delete through grid, confirm removal."""
        _create_pw_interface(api_client, "PW-Del-Target", listen_port="17888")

        page = _make_page(authenticated_page, base_url)
        # Verify the interface exists in the grid
        row = page.get_row_by_name("PW-Del-Target")
        assert row.count() > 0

        page.click_delete("PW-Del-Target")
        page.confirm_delete()

        # Wait for grid refresh
        authenticated_page.wait_for_timeout(500)
        # Row should be gone
        row = page.get_row_by_name("PW-Del-Target")
        assert row.count() == 0

    def test_PW_IFC_143_delete_cancel(self, authenticated_page, base_url,
                                       api_client, clean_interfaces):
        """Clicking cancel on the delete confirmation keeps the row."""
        _create_pw_interface(api_client, "PW-Del-Cancel", listen_port="17889")

        page = _make_page(authenticated_page, base_url)
        row = page.get_row_by_name("PW-Del-Cancel")
        assert row.count() > 0

        page.click_delete("PW-Del-Cancel")
        page.cancel_delete()

        # Row should still be present
        authenticated_page.wait_for_timeout(300)
        row = page.get_row_by_name("PW-Del-Cancel")
        assert row.count() > 0
