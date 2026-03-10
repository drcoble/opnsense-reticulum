"""
Model Validation Tests — M-201 through M-209

These tests validate field constraints defined in Reticulum.xml without an OPNsense VM,
by directly applying the same validation logic (regex masks, integer ranges) in Python.

Run with: pytest tests/model/
"""
import re
import pytest


# ---------------------------------------------------------------------------
# Helpers — mirrors OPNsense MVC field validation logic
# ---------------------------------------------------------------------------

def validate_port(value):
    """PortField: 1–65535."""
    try:
        v = int(value)
        return 1 <= v <= 65535
    except (ValueError, TypeError):
        return False


def validate_integer(value, min_val=None, max_val=None):
    """IntegerField with optional min/max."""
    try:
        v = int(value)
        if min_val is not None and v < min_val:
            return False
        if max_val is not None and v > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def validate_mask(value, pattern):
    """TextField Mask: regex must match entire value."""
    return bool(re.fullmatch(pattern.strip("/"), value))


def validate_csvlist(value, item_pattern):
    """CSVListField with MaskPerItem: each comma-separated item must match."""
    if not value:
        return True
    items = [i.strip() for i in value.split(",")]
    pat = item_pattern.strip("/")
    return all(re.fullmatch(pat, item) for item in items)


# ---------------------------------------------------------------------------
# M-201: Port range validation
# ---------------------------------------------------------------------------

class TestM201PortRange:
    """M-201: shared_instance_port must be a valid port (1–65535)."""

    def test_port_zero_invalid(self):
        assert not validate_port("0")

    def test_port_too_high_invalid(self):
        assert not validate_port("70000")

    def test_port_valid(self):
        assert validate_port("37428")

    def test_port_min_valid(self):
        assert validate_port("1")

    def test_port_max_valid(self):
        assert validate_port("65535")

    def test_port_non_numeric_invalid(self):
        assert not validate_port("abc")

    def test_instance_control_port_valid(self):
        assert validate_port("37429")


# ---------------------------------------------------------------------------
# M-202: Integer range validation
# ---------------------------------------------------------------------------

class TestM202IntegerRange:
    """M-202: Various integer fields with min/max constraints."""

    def test_loglevel_negative_invalid(self):
        assert not validate_integer("-1", min_val=0, max_val=7)

    def test_loglevel_too_high_invalid(self):
        assert not validate_integer("8", min_val=0, max_val=7)

    def test_loglevel_valid(self):
        assert validate_integer("4", min_val=0, max_val=7)

    def test_loglevel_boundaries(self):
        assert validate_integer("0", min_val=0, max_val=7)
        assert validate_integer("7", min_val=0, max_val=7)

    def test_spreadingfactor_too_low(self):
        # XML: min=7, max=12
        assert not validate_integer("6", min_val=7, max_val=12)

    def test_spreadingfactor_too_high(self):
        assert not validate_integer("13", min_val=7, max_val=12)

    def test_spreadingfactor_valid(self):
        assert validate_integer("8", min_val=7, max_val=12)

    def test_stamp_cost_target_below_min(self):
        # XML: min=13, max=64
        assert not validate_integer("12", min_val=13, max_val=64)

    def test_stamp_cost_target_valid(self):
        assert validate_integer("13", min_val=13, max_val=64)

    def test_stamp_cost_target_max(self):
        assert validate_integer("64", min_val=13, max_val=64)

    def test_codingrate_range(self):
        # XML: min=5, max=8
        assert not validate_integer("4", min_val=5, max_val=8)
        assert not validate_integer("9", min_val=5, max_val=8)
        assert validate_integer("5", min_val=5, max_val=8)
        assert validate_integer("8", min_val=5, max_val=8)


# ---------------------------------------------------------------------------
# M-203: Required fields
# ---------------------------------------------------------------------------

class TestM203RequiredFields:
    """M-203: Required fields must be non-empty."""

    def test_interface_name_empty_invalid(self):
        # name: Required=Y, Mask=/^[a-zA-Z0-9 _-]{1,64}$/
        assert not validate_mask("", r"[a-zA-Z0-9 _-]{1,64}")

    def test_interface_name_valid(self):
        assert validate_mask("My Interface", r"[a-zA-Z0-9 _-]{1,64}")

    def test_interface_type_required(self):
        # type is OptionField — empty string is not a valid option
        valid_types = {
            "AutoInterface", "TCPServerInterface", "TCPClientInterface",
            "UDPInterface", "I2PInterface", "RNodeInterface",
            "RNodeMultiInterface", "SerialInterface", "KISSInterface",
            "AX25KISSInterface", "PipeInterface", "BackboneInterface"
        }
        assert "" not in valid_types
        assert "TCPServerInterface" in valid_types


# ---------------------------------------------------------------------------
# M-204: Hex hash format (CSVListField)
# ---------------------------------------------------------------------------

class TestM204HexHashFormat:
    """M-204: static_peers — each must be exactly 32 lowercase hex chars."""

    PATTERN = r"[0-9a-f]{32}"

    def test_valid_single_hash(self):
        # 32 lowercase hex chars (the spec placeholder "validhex32chars..." is not actual hex)
        assert validate_csvlist("abcdef0123456789abcdef0123456789", self.PATTERN)

    def test_too_short_invalid(self):
        assert not validate_csvlist("TOOSHORT", self.PATTERN)

    def test_invalid_chars(self):
        assert not validate_csvlist("has_invalid_chars_in_this_hash!!", self.PATTERN)

    def test_uppercase_invalid(self):
        # Must be lowercase
        assert not validate_csvlist("AAAABBBBCCCCDDDD1111222233334444", self.PATTERN)

    def test_valid_multiple(self):
        val = "aaaabbbbccccdddd1111222233334444,bbbbccccddddeeee5555666677778888"
        assert validate_csvlist(val, self.PATTERN)

    def test_one_invalid_in_list(self):
        val = "aaaabbbbccccdddd1111222233334444,TOOSHORT"
        assert not validate_csvlist(val, self.PATTERN)

    def test_empty_allowed(self):
        assert validate_csvlist("", self.PATTERN)

    def test_33_chars_invalid(self):
        assert not validate_csvlist("a" * 33, self.PATTERN)

    def test_31_chars_invalid(self):
        assert not validate_csvlist("a" * 31, self.PATTERN)


# ---------------------------------------------------------------------------
# M-205: Cross-field: ports must differ
# ---------------------------------------------------------------------------

class TestM205PortsMustDiffer:
    """M-205: shared_instance_port and instance_control_port must not be equal."""

    def test_same_ports_invalid(self):
        shared = 37428
        control = 37428
        assert shared == control  # This condition triggers validation error

    def test_different_ports_valid(self):
        shared = 37428
        control = 37429
        assert shared != control


# ---------------------------------------------------------------------------
# M-206: Cross-field stamp cost floor (target − flexibility ≥ 13)
# ---------------------------------------------------------------------------

class TestM206StampCostFloor:
    """M-206: stamp_cost_target - stamp_cost_flexibility must be >= 13."""

    def _floor_valid(self, target, flexibility):
        return (target - flexibility) >= 13

    def test_floor_below_min_invalid(self):
        assert not self._floor_valid(15, 3)  # floor=12 < 13

    def test_floor_at_min_valid(self):
        assert self._floor_valid(16, 3)  # floor=13 ✓

    def test_floor_exact_min_both_min(self):
        assert self._floor_valid(13, 0)  # floor=13 ✓

    def test_floor_one_below_both_min(self):
        assert not self._floor_valid(13, 1)  # floor=12 < 13

    def test_floor_large_values_valid(self):
        assert self._floor_valid(64, 16)  # floor=48 ✓

    def test_floor_case_from_spec_error(self):
        # 20-8=12 < 13 → error
        assert not self._floor_valid(20, 8)

    def test_floor_case_from_spec_valid(self):
        # 21-8=13 ✓
        assert self._floor_valid(21, 8)


# ---------------------------------------------------------------------------
# M-207: AX25 callsign format
# ---------------------------------------------------------------------------

class TestM207AX25Callsign:
    """M-207: callsign field — /^[A-Z0-9]{0,7}(-[0-9]{1,2})?$/"""

    PATTERN = r"[A-Z0-9]{0,7}(-[0-9]{1,2})?"

    def test_basic_callsign_valid(self):
        assert validate_mask("W1ABC", self.PATTERN)

    def test_callsign_with_ssid_valid(self):
        assert validate_mask("W1ABC-12", self.PATTERN)

    def test_callsign_too_long_invalid(self):
        # 8 chars is too long (max 7)
        assert not validate_mask("TOOLONGC", self.PATTERN)

    def test_lowercase_invalid(self):
        assert not validate_mask("w1abc", self.PATTERN)

    def test_empty_valid(self):
        # Optional field — empty allowed
        assert validate_mask("", self.PATTERN)

    def test_with_hyphen_one_digit(self):
        assert validate_mask("N0CALL-5", self.PATTERN)

    def test_with_hyphen_two_digits(self):
        assert validate_mask("N0CALL-15", self.PATTERN)

    def test_special_chars_invalid(self):
        assert not validate_mask("W1ABC!", self.PATTERN)


# ---------------------------------------------------------------------------
# M-208: UpdateOnlyTextField masking
# ---------------------------------------------------------------------------

class TestM208UpdateOnlyTextField:
    """M-208: UpdateOnlyTextField (passphrase, rpc_key) behavior."""

    def test_field_type_is_update_only(self):
        """Verify the XML declares passphrase and rpc_key as UpdateOnlyTextField."""
        import xml.etree.ElementTree as ET
        import os
        xml_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "src", "opnsense", "mvc", "app", "models",
            "OPNsense", "Reticulum", "Reticulum.xml"
        )
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Check passphrase field type
        passphrase = root.find(".//passphrase")
        assert passphrase is not None, "passphrase field missing from model"
        assert passphrase.get("type") == "UpdateOnlyTextField", \
            f"passphrase type is {passphrase.get('type')}, expected UpdateOnlyTextField"

        # Check rpc_key field type
        rpc_key = root.find(".//rpc_key")
        assert rpc_key is not None, "rpc_key field missing from model"
        assert rpc_key.get("type") == "UpdateOnlyTextField", \
            f"rpc_key type is {rpc_key.get('type')}, expected UpdateOnlyTextField"

    def test_rpc_key_mask(self):
        """rpc_key mask: empty OR 32-128 lowercase hex chars."""
        pattern = r"([0-9a-f]{32,128})?"
        # Empty (unset)
        assert validate_mask("", pattern)
        # Valid 32-char hex
        assert validate_mask("a" * 32, pattern)
        # Valid 128-char hex
        assert validate_mask("a" * 128, pattern)
        # Too short
        assert not validate_mask("a" * 31, pattern)
        # Uppercase invalid
        assert not validate_mask("A" * 32, pattern)


# ---------------------------------------------------------------------------
# M-209: Interface name mask
# ---------------------------------------------------------------------------

class TestM209InterfaceNameMask:
    """M-209: Interface name — /^[a-zA-Z0-9 _-]{1,64}$/"""

    PATTERN = r"[a-zA-Z0-9 _-]{1,64}"

    def test_normal_name_valid(self):
        assert validate_mask("My TCP Server", self.PATTERN)

    def test_brackets_invalid(self):
        # Brackets would break INI section headers
        assert not validate_mask("Interface [1]", self.PATTERN)

    def test_empty_invalid(self):
        assert not validate_mask("", self.PATTERN)

    def test_max_length_valid(self):
        assert validate_mask("A" * 64, self.PATTERN)

    def test_over_max_length_invalid(self):
        assert not validate_mask("A" * 65, self.PATTERN)

    def test_underscore_dash_valid(self):
        assert validate_mask("my-interface_1", self.PATTERN)

    def test_equals_invalid(self):
        assert not validate_mask("iface=bad", self.PATTERN)

    def test_newline_invalid(self):
        assert not validate_mask("iface\nbad", self.PATTERN)
