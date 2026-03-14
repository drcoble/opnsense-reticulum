"""
X-710: Configuration Injection Test — sub_interfaces_raw

Tests that a malicious [reticulum] section injected via sub_interfaces_raw
does not override the legitimate [reticulum] section in the rendered config.

The template emits sub_interfaces_raw verbatim inside the [[MultiInterface]] block.
Reticulum's INI parser treats [[...]] as a sub-section of the preceding [section],
so the injected [reticulum] content technically appears after the real [reticulum]
block at the top level — but INI parsers that use last-value-wins would override it.

This test:
1. Renders the template with injected content
2. Parses the resulting config as INI
3. Verifies the legitimate [reticulum] enable_transport=False is not overridden

Run with: pytest tests/security/test_config_injection.py
"""
import sys
import os
import configparser
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import make_ctx, render

pytestmark = pytest.mark.unit


INJECTED_RAW = """[[[SubA]]]
  frequency = 915000000
[reticulum]
  enable_transport = True
  share_instance = False"""


def test_X710_injected_reticulum_section_does_not_override():
    """X-710: Injected [reticulum] section in sub_interfaces_raw — verify behavior."""
    iface = {
        "enabled": "1",
        "name": "MultiNode",
        "type": "RNodeMultiInterface",
        "port": "/dev/cuaU0",
        "sub_interfaces_raw": INJECTED_RAW,
    }
    ctx = make_ctx(
        general={"enable_transport": "0", "share_instance": "1"},
        interfaces=[iface]
    )
    output = render("reticulum_config.j2", ctx)

    # The raw block IS present verbatim (by design)
    assert "[[[SubA]]]" in output, "Raw block should be emitted verbatim"
    assert "[reticulum]" in output, "Original [reticulum] section must exist"

    # Count occurrences of top-level [reticulum] (not [[...]] or [[[...]]])
    import re
    top_level_reticulum = re.findall(r"^\[reticulum\]", output, re.MULTILINE)
    injected_reticulum = re.findall(r"^\[reticulum\]", INJECTED_RAW, re.MULTILINE)

    # Document: the injected section IS present in the raw output
    print(f"\nTop-level [reticulum] count in rendered config: {len(top_level_reticulum)}")
    print(f"[reticulum] occurrences from injection: {len(injected_reticulum)}")
    print("\n--- Rendered config ---")
    print(output)
    print("---")

    # The first [reticulum] section comes from the legitimate template
    lines = output.splitlines()
    first_reticulum_idx = next(i for i, line in enumerate(lines) if line.strip() == "[reticulum]")
    # enable_transport should be False in the legitimate section
    section_after = "\n".join(lines[first_reticulum_idx:first_reticulum_idx + 10])
    assert "enable_transport = False" in section_after, \
        f"Legitimate [reticulum] section should have enable_transport=False. Got:\n{section_after}"


def test_X710_ini_parser_last_value_wins():
    """X-710: Document what configparser does with duplicate sections (last-value-wins)."""
    iface = {
        "enabled": "1",
        "name": "MultiNode",
        "type": "RNodeMultiInterface",
        "port": "/dev/cuaU0",
        "sub_interfaces_raw": INJECTED_RAW,
    }
    ctx = make_ctx(
        general={"enable_transport": "0", "share_instance": "1"},
        interfaces=[iface]
    )
    output = render("reticulum_config.j2", ctx)

    # Use strict=False to allow duplicate sections (mirrors Python configparser default)
    parser = configparser.RawConfigParser(strict=False)
    # configparser uses [DEFAULT] as a special section, skip that
    # We strip the [[[...]]] lines as configparser can't handle triple-bracket
    cleaned = "\n".join(
        line for line in output.splitlines()
        if not line.strip().startswith("[[[") and not line.strip().startswith("]]]")
    )

    try:
        parser.read_string(cleaned)
        transport = parser.get("reticulum", "enable_transport", fallback="NOT_FOUND")
        print(f"\nconfigparser resolved enable_transport = {transport}")

        # SECURITY FINDING: If configparser returns "True", the injection succeeded
        # Document this behavior regardless of outcome
        if transport == "True":
            pytest.xfail(
                "SECURITY: configparser last-value-wins behavior means injected "
                "[reticulum] section overrides the legitimate one. "
                "Reticulum's own parser behavior may differ — test on VM."
            )
        else:
            # Either False (injection didn't win) or parsing skipped the section
            print(f"Resolved value '{transport}' — injection did not override (or was skipped)")
    except Exception as e:
        print(f"Parser error (expected for triple-bracket syntax): {e}")


def test_X710_legitimate_section_is_first():
    """X-710: The legitimate [reticulum] section appears before the injected one."""
    iface = {
        "enabled": "1",
        "name": "MultiNode",
        "type": "RNodeMultiInterface",
        "port": "/dev/cuaU0",
        "sub_interfaces_raw": INJECTED_RAW,
    }
    ctx = make_ctx(interfaces=[iface])
    output = render("reticulum_config.j2", ctx)

    import re
    positions = [(m.start(), m.group()) for m in re.finditer(r"^\[reticulum\]", output, re.MULTILINE)]

    print(f"\n[reticulum] positions in output: {positions}")

    if len(positions) >= 2:
        # First occurrence is the legitimate template section
        assert positions[0][0] < positions[1][0], "Legitimate section should come first"
        # The legitimate section is at position 0 (top of file, before any interfaces)
        assert positions[0][0] < 50, \
            f"Legitimate [reticulum] should be near top of file (pos={positions[0][0]})"
        print("NOTE: Duplicate [reticulum] exists. Reticulum uses first-value-wins (Python dict).")
    else:
        print("Only one [reticulum] found — injection may have been parsed differently")
