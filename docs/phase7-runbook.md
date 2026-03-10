# Phase 7 — Test Execution Runbook

**Date:** 2026-03-10
**Status:** final
**Source:** Phase 7 testing plan (`docs/phase7-testing.md`) + plugin source review
**Plugin version:** 1.0.0
**Target OS:** OPNsense 24.x (FreeBSD 14.x base)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Test Execution Order](#2-test-execution-order)
3. [VM Setup](#3-vm-setup)
4. [Plugin Build and Install](#4-plugin-build-and-install)
5. [Template Testing Without a VM](#5-template-testing-without-a-vm)
6. [Running Template Tests (T-101–T-112)](#6-running-template-tests-t-101t-112)
7. [Running Model Validation Tests (M-201–M-209)](#7-running-model-validation-tests-m-201m-209)
8. [Running API Tests (A-301–A-309)](#8-running-api-tests-a-301a-309)
9. [Running Service Lifecycle Tests (S-401–S-407)](#9-running-service-lifecycle-tests-s-401s-407)
10. [Running GUI Tests (G-501–G-525)](#10-running-gui-tests-g-501g-525)
11. [Running Widget Tests (W-601–W-606)](#11-running-widget-tests-w-601w-606)
12. [Running Security Tests (X-701–X-710)](#12-running-security-tests-x-701x-710)
13. [Running Edge Case Tests (E-901–E-910)](#13-running-edge-case-tests-e-901e-910)
14. [Smoke Test Script](#14-smoke-test-script)
15. [Failure Investigation Guide](#15-failure-investigation-guide)
16. [Time Estimates](#16-time-estimates)

---

## 1. Prerequisites

### Tester environment (Mac/Linux workstation)

- `make` available (for plugin build)
- `scp` / `ssh` access to the VM
- A browser for GUI testing
- Optional: Python 3 with `jinja2` installed (`pip3 install jinja2`) for local template tests

### OPNsense VM

| Requirement | Value |
|---|---|
| Base OS | FreeBSD 14.x (matching OPNsense 24.x) |
| RAM | 2 GB minimum |
| Disk | 20 GB minimum |
| Network | At least one NIC reachable from workstation |
| SSH | Root or admin access |
| Internet | Required for `pkg` during installation |

The VM must be a clean OPNsense installation before running S-401 (package install). Do not run any reticulum tests on a production firewall.

### API credentials

All `curl` examples assume you are running them **on the VM** as root via SSH, targeting `https://localhost`. If testing from the workstation, replace `localhost` with the VM's LAN IP and ensure the firewall permits HTTPS from your workstation.

To authenticate `curl` from the workstation, use an OPNsense API key:

```sh
# Replace KEY and SECRET with values from System > Access > Users > API Keys
curl -k -u 'KEY:SECRET' https://<VM-IP>/api/reticulum/rnsd/get
```

For brevity, all examples below omit authentication and assume root shell on the VM.

---

## 2. Test Execution Order

Run categories in this order. Later categories depend on earlier ones passing.

```
S-401  (install)
  └── T-101..T-112  (template output — needs plugin installed)
        └── M-201..M-209  (model validation — needs API up)
              └── A-301..A-309  (API endpoints)
                    └── S-402..S-407  (service lifecycle — needs API passing)
                          └── G-501..G-525  (GUI — needs services working)
                                └── W-601..W-606  (widget — needs GUI working)
                                      └── X-701..X-710  (security)
                                            └── E-901..E-910  (edge cases, P2)
```

**Blocked-test rule:** If S-401 fails, mark all subsequent tests as Blocked. If A-301 fails, mark all A, S, G, W, X, and E tests as Blocked. Record the blocking test ID in the Notes column of `phase7-status.md`.

---

## 3. VM Setup

### 3.1 Install OPNsense

Install OPNsense on the VM using the standard installer image. After first boot:

1. Complete the console setup wizard (assign interfaces, set root password).
2. Enable SSH: **System > Settings > Administration > Secure Shell**.
3. Confirm the web GUI is reachable from your workstation.

### 3.2 Verify baseline

```sh
# SSH to VM
ssh root@<VM-IP>

# Confirm FreeBSD version
uname -r
# Expected: 14.x-RELEASE-pX-HBSD or similar

# Confirm pkg works
pkg update
```

---

## 4. Plugin Build and Install

### 4.1 Build the package (on workstation)

```sh
cd /Users/drew/Documents/Development/Opnsense_Reticulum/os-reticulum
make package
# Output: os-reticulum-1.0.0.pkg (or similar) in current directory
```

If `make package` is unavailable, consult the OPNsense plugin build toolchain docs. The build requires the OPNsense `tools` repository.

### 4.2 Copy to VM

```sh
scp os-reticulum-*.pkg root@<VM-IP>:/tmp/
```

### 4.3 Install on VM

```sh
ssh root@<VM-IP>
pkg install /tmp/os-reticulum-*.pkg
```

Expected output includes lines confirming:
- Package files extracted
- Post-install scripts run (user creation, directory setup, virtualenv install)

### 4.4 Confirm plugin is visible in GUI

Navigate to **Services > Reticulum** in the OPNsense web GUI. You should see menu items for General, Interfaces, LXMF, and Logs.

---

## 5. Template Testing Without a VM

Use this approach to validate Jinja2 template output locally on your workstation before a VM is available. It requires Python 3 and the `jinja2` package.

### 5.1 Install dependencies

```sh
pip3 install jinja2 lxml
```

### 5.2 Create a minimal test harness

Save the following as `/tmp/render_template.py`:

```python
#!/usr/bin/env python3
"""
Minimal OPNsense Jinja2 template renderer for local testing.
Usage: python3 render_template.py <template.j2> <config_snippet.xml>
"""
import sys
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader

def xml_to_dict(element):
    """Recursively convert XML element to nested dict."""
    result = {}
    for child in element:
        if len(child):
            result[child.tag] = xml_to_dict(child)
        else:
            result[child.tag] = child.text or ''
    return result

if len(sys.argv) < 3:
    print("Usage: render_template.py <template.j2> <config.xml>")
    sys.exit(1)

template_path = sys.argv[1]
config_path   = sys.argv[2]

import os
template_dir  = os.path.dirname(os.path.abspath(template_path))
template_name = os.path.basename(template_path)

tree = ET.parse(config_path)
root = tree.getroot()
# Build context: find OPNsense/Reticulum node
reticulum = root.find('.//Reticulum')
context = {'OPNsense': {'Reticulum': xml_to_dict(reticulum)}} if reticulum else {}

env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template_name)
print(template.render(**context))
```

### 5.3 Create reference XML snippets

For each template test, create a minimal `config.xml` fragment. Example for T-101:

```xml
<!-- /tmp/t101_config.xml -->
<opnsense>
  <OPNsense>
    <Reticulum>
      <general>
        <enabled>0</enabled>
        <enable_transport>0</enable_transport>
        <share_instance>1</share_instance>
        <shared_instance_port>37428</shared_instance_port>
        <instance_control_port>37429</instance_control_port>
        <panic_on_interface_error>0</panic_on_interface_error>
        <loglevel>4</loglevel>
        <logfile>/var/log/reticulum/rnsd.log</logfile>
      </general>
      <interfaces/>
    </Reticulum>
  </OPNsense>
</opnsense>
```

### 5.4 Render and diff

```sh
TEMPLATE_DIR=/Users/drew/Documents/Development/Opnsense_Reticulum/os-reticulum/src/opnsense/service/templates/OPNsense/Reticulum

python3 /tmp/render_template.py \
  "${TEMPLATE_DIR}/reticulum_config.j2" \
  /tmp/t101_config.xml \
  > /tmp/t101_rendered.config

# Compare against your hand-crafted reference
diff /tmp/t101_reference.config /tmp/t101_rendered.config
```

A clean diff (no output) means PASS. Any unexpected diff line is a FAIL.

**Note:** The OPNsense template engine uses a slightly different variable-scoping approach than raw Jinja2. The local harness above is an approximation. Always confirm passing local tests against the VM as well.

---

## 6. Running Template Tests (T-101–T-112)

**Precondition:** Plugin installed on VM (S-401 complete).

### 6.1 How to trigger template rendering on the VM

```sh
# Set config values via API, then trigger template reload
configctl template reload OPNsense/Reticulum

# Inspect generated files
cat /usr/local/etc/reticulum/config
cat /usr/local/etc/lxmf/config
cat /usr/local/etc/lxmf/allowed
cat /usr/local/etc/lxmf/ignored
cat /etc/rc.conf.d/rnsd
cat /etc/rc.conf.d/lxmd
```

### 6.2 T-101: Minimal rnsd config

```sh
# Reset to defaults (delete all interfaces, disable service)
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"enabled":"0","enable_transport":"0","share_instance":"1",
       "shared_instance_port":"37428","instance_control_port":"37429",
       "panic_on_interface_error":"0","loglevel":"4"}}'
configctl template reload OPNsense/Reticulum
cat /usr/local/etc/reticulum/config
```

**Expected output:**

```ini
[reticulum]
  enable_transport = False
  share_instance = True
  shared_instance_port = 37428
  instance_control_port = 37429
  panic_on_interface_error = False

[logging]
  loglevel = 4
```

**PASS criterion:** Output matches exactly (whitespace and key order may vary; key-value pairs must match).

### 6.3 T-102: Single TCPServerInterface

```sh
# Add interface
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"Test TCP","type":"TCPServerInterface",
       "listen_ip":"0.0.0.0","listen_port":"4242","enabled":"1"}}'
configctl template reload OPNsense/Reticulum
cat /usr/local/etc/reticulum/config
```

**PASS criterion:** Config contains a `[[Test TCP]]` section with `type = TCPServerInterface`, `listen_ip = 0.0.0.0`, `listen_port = 4242`.

### 6.4 T-103: One of each interface type

Create one interface of each type via the API (or GUI), trigger reload, and verify each `[[Name]]` section contains the correct `type =` value with no fields from other interface types bleeding in.

Interface types to cover: `AutoInterface`, `TCPServerInterface`, `TCPClientInterface`, `UDPInterface`, `I2PInterface`, `RNodeInterface`, `RNodeMultiInterface`, `SerialInterface`, `KISSInterface`, `AX25KISSInterface`, `PipeInterface`, `BackboneInterface`.

**PASS criterion:** Each section contains only type-appropriate keys. No cross-contamination (e.g., `listen_port` does not appear in an `RNodeInterface` section).

### 6.5 T-104: RNodeInterface with all fields

```sh
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"RNode Test","type":"RNodeInterface",
       "port":"/dev/cuaU0","frequency":"915000000","bandwidth":"125000",
       "txpower":"14","spreadingfactor":"7","codingrate":"5",
       "airtime_limit_long":"30","airtime_limit_short":"70",
       "id_callsign":"N0CALL","id_interval":"600","enabled":"1"}}'
configctl template reload OPNsense/Reticulum
grep -A 20 '\[\[RNode Test\]\]' /usr/local/etc/reticulum/config
```

**PASS criterion:** All supplied fields appear with correct key names. No empty or zero-value optional fields are emitted if they were not set.

### 6.6 T-105: RNodeMultiInterface raw block

```sh
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"RNodeMulti Test","type":"RNodeMultiInterface",
       "port":"/dev/cuaU0",
       "sub_interfaces_raw":"[[[Sub A]]]\n  frequency = 915000000\n  bandwidth = 125000\n",
       "enabled":"1"}}'
configctl template reload OPNsense/Reticulum
grep -A 10 '\[\[\[Sub A\]\]\]' /usr/local/etc/reticulum/config
```

**PASS criterion:** The raw block appears verbatim inside the `[[RNodeMulti Test]]` section, including the triple-bracket sub-interface header.

### 6.7 T-106: Boolean field mapping

Set boolean fields in both rnsd and lxmd configs and verify:

- rnsd booleans: `1` renders as `True`, `0` renders as `False`
- lxmd booleans: `1` renders as `yes`, `0` renders as `no`

```sh
# Check enable_transport in rnsd config
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"enable_transport":"1"}}'
configctl template reload OPNsense/Reticulum
grep enable_transport /usr/local/etc/reticulum/config
# Expected: enable_transport = True
```

### 6.8 T-107: Empty optional fields omitted

Add an interface with only name, type, and one required field. Reload and verify optional fields (e.g., `network_name`, `passphrase`, `ifac_size`) are absent from the output section.

**PASS criterion:** No keys with empty values appear in the rendered section.

### 6.9 T-108: CSV list rendering

```sh
# Set static_peers on lxmf
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"static_peers":"abc1234567890abcdef1234567890ab,def1234567890abcdef1234567890ab"}}'
configctl template reload OPNsense/Reticulum
grep static_peers /usr/local/etc/lxmf/config
# Expected: static_peers = abc1234567890abcdef1234567890ab,def1234567890abcdef1234567890ab
```

**PASS criterion:** Value is a single comma-separated line, not split across lines.

### 6.10 T-109: Minimal lxmd config

With `enable_node = 0`, verify the lxmf config contains a `[propagation]` section with only `enable_node = no`.

```sh
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"enabled":"0","enable_node":"0"}}'
configctl template reload OPNsense/Reticulum
cat /usr/local/etc/lxmf/config
```

### 6.11 T-110: Full lxmd config with propagation

Enable all lxmf propagation fields and verify all sections and keys appear correctly named in `/usr/local/etc/lxmf/config`. Key names to verify: `propagation_message_max_accepted_size`, `propagation_sync_max_accepted_size`, `propagation_stamp_cost_target`, `propagation_stamp_cost_flexibility`.

### 6.12 T-111: ACL file templates

```sh
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"allowed_identities":"aabbccddeeff00112233445566778899,00112233445566778899aabbccddeeff"}}'
configctl template reload OPNsense/Reticulum
cat /usr/local/etc/lxmf/allowed
```

**PASS criterion:** File contains exactly two lines, one hash per line, no commas.

### 6.13 T-112: rc.conf.d templates

```sh
# Test 1: rnsd enabled
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"enabled":"1"}}'
configctl template reload OPNsense/Reticulum
cat /etc/rc.conf.d/rnsd
# Expected: rnsd_enable="YES"

# Test 2: rnsd disabled
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"enabled":"0"}}'
configctl template reload OPNsense/Reticulum
cat /etc/rc.conf.d/rnsd
# Expected: rnsd_enable="NO"

# Test 3: lxmd enabled but rnsd disabled
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"enabled":"1"}}'
configctl template reload OPNsense/Reticulum
cat /etc/rc.conf.d/lxmd
# Expected: lxmd_enable="NO" (blocked because rnsd is disabled)
```

---

## 7. Running Model Validation Tests (M-201–M-209)

**Precondition:** Plugin installed, API reachable.

**How to interpret responses:**

- A validation error returns HTTP 200 with body `{"result":"failed","validations":{"field.name":"error message"}}`
- A successful save returns `{"result":"saved"}`
- Unexpected HTTP 4xx/5xx = infrastructure problem, not a model validation result

### M-201: Port range validation

```sh
# Should fail: port 0 is out of range
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"shared_instance_port":"0"}}'
# Expected: validations error on shared_instance_port

# Should fail: port 70000 is out of range
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"shared_instance_port":"70000"}}'
# Expected: validations error

# Should succeed
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"shared_instance_port":"37428"}}'
# Expected: {"result":"saved"}
```

### M-202: Integer range validation

```sh
# loglevel -1 — should fail
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"loglevel":"-1"}}'

# loglevel 8 — should fail (max is 7)
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"loglevel":"8"}}'

# spreadingfactor 6 — should fail (min is 7, defined in Reticulum.xml)
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"SF Test","type":"RNodeInterface","spreadingfactor":"6"}}'

# spreadingfactor 13 — should fail (max is 12)
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"SF Test","type":"RNodeInterface","spreadingfactor":"13"}}'

# stamp_cost_target 12 — should fail (min is 13)
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"stamp_cost_target":"12"}}'
```

### M-203: Required fields

```sh
# Interface with empty name — should fail
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"","type":"TCPServerInterface"}}'

# Interface with no type — should fail
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"NoType","type":""}}'
```

### M-204: Hex hash format

```sh
# 32 valid hex chars — should succeed
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"static_peers":"aabbccddeeff00112233445566778899"}}'

# Too short — should fail
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"static_peers":"TOOSHORT"}}'

# Invalid characters — should fail
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"static_peers":"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"}}'

# Multiple valid hashes — should succeed
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"static_peers":"aabbccddeeff00112233445566778899,00112233445566778899aabbccddeeff"}}'
```

### M-205: Cross-field — ports must differ

```sh
# Same port on both fields — should fail
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"shared_instance_port":"37428","instance_control_port":"37428"}}'

# Different ports — should succeed
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"shared_instance_port":"37428","instance_control_port":"37429"}}'
```

### M-206: Cross-field — stamp cost floor (target − flexibility ≥ 13)

Run each case; verify PASS/FAIL as indicated:

| target | flexibility | floor | Expected |
|--------|-------------|-------|----------|
| 15 | 3 | 12 | FAIL |
| 16 | 3 | 13 | PASS |
| 13 | 0 | 13 | PASS |
| 13 | 1 | 12 | FAIL |
| 64 | 16 | 48 | PASS |
| 20 | 8 | 12 | FAIL |
| 21 | 8 | 13 | PASS |

```sh
# Example — should fail (floor = 12)
curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"stamp_cost_target":"15","stamp_cost_flexibility":"3"}}'
```

### M-207: AX25 callsign format

```sh
# Valid formats — should succeed
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"AX25 Test","type":"AX25KISSInterface","callsign":"W1ABC"}}'

curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"AX25 Test2","type":"AX25KISSInterface","callsign":"W1ABC-12"}}'

# Too long — should fail (mask: [A-Z0-9]{0,7}(-[0-9]{1,2})?)
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"AX25 Test3","type":"AX25KISSInterface","callsign":"TOOLONGCALLSIGN"}}'

# Lowercase — should fail
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"AX25 Test4","type":"AX25KISSInterface","callsign":"w1abc"}}'
```

### M-208: UpdateOnlyTextField masking

```sh
# Step 1: Add interface with passphrase
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"SecureIface","type":"TCPServerInterface",
       "passphrase":"secret123","listen_port":"5001"}}'
# Save the returned UUID

UUID=<uuid-from-above>

# Step 2: GET the interface — passphrase must NOT be in the response
curl -k https://localhost/api/reticulum/rnsd/getInterface/$UUID
# Expected: no "passphrase" key or key is empty/masked

# Step 3: Update a different field without sending passphrase
curl -k -X POST https://localhost/api/reticulum/rnsd/setInterface/$UUID \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"listen_port":"5002"}}'
# Expected: {"result":"saved"} and original passphrase is preserved internally
```

**PASS criterion for step 3:** After the update, verify by checking the generated config file after a template reload — the `passphrase` or `network_key` line should still be present.

### M-209: Interface name mask

```sh
# Valid name — should succeed
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"My TCP Server","type":"TCPServerInterface"}}'

# Brackets in name — should fail (mask: [a-zA-Z0-9 _-]{1,64})
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"Interface [1]","type":"TCPServerInterface"}}'

# Empty name — should fail (Required)
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"","type":"TCPServerInterface"}}'
```

---

## 8. Running API Tests (A-301–A-309)

**Precondition:** M-201..M-209 all passing.

### A-301: General settings get/set round-trip

```sh
# 1. Get defaults
curl -k https://localhost/api/reticulum/rnsd/get
# Verify: JSON contains general{} node with all fields at defaults

# 2. Set specific values
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"enabled":"1","enable_transport":"1","loglevel":"5"}}'
# Expected: {"result":"saved"}

# 3. Get again and confirm
curl -k https://localhost/api/reticulum/rnsd/get
# Expected: enabled=1, enable_transport=1, loglevel=5
```

### A-302: Interface CRUD cycle

```sh
# Add
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"CRUD Test","type":"TCPServerInterface","listen_port":"4242","enabled":"1"}}'
# Save UUID from response

UUID=<uuid-from-above>

# Search
curl -k https://localhost/api/reticulum/rnsd/searchInterfaces
# Verify: "CRUD Test" appears in rows

# Get
curl -k https://localhost/api/reticulum/rnsd/getInterface/$UUID
# Verify: full record returned

# Update
curl -k -X POST https://localhost/api/reticulum/rnsd/setInterface/$UUID \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"listen_port":"5555"}}'
# Expected: {"result":"saved"}

# Confirm update
curl -k https://localhost/api/reticulum/rnsd/getInterface/$UUID
# Verify: listen_port = 5555

# Toggle (disable)
curl -k -X POST https://localhost/api/reticulum/rnsd/toggleInterface/$UUID
# Verify: enabled changes to 0

# Delete
curl -k -X POST https://localhost/api/reticulum/rnsd/delInterface/$UUID
# Expected: {"result":"deleted"} or similar

# Confirm deleted
curl -k https://localhost/api/reticulum/rnsd/getInterface/$UUID
# Expected: 404 or empty record
```

### A-303: LXMF get/set

```sh
curl -k https://localhost/api/reticulum/lxmd/get
# Verify: lxmf{} node with all fields at defaults

curl -k -X POST https://localhost/api/reticulum/lxmd/set \
  -H 'Content-Type: application/json' \
  -d '{"lxmf":{"enabled":"1","enable_node":"1","announce_interval":"120"}}'
# Expected: {"result":"saved"}

curl -k https://localhost/api/reticulum/lxmd/get
# Verify: enabled=1, enable_node=1, announce_interval=120
```

### A-304: Invalid data rejection

```sh
# loglevel out of range
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"loglevel":"99"}}'
# Expected: validations error, NOT {"result":"saved"}

# addInterface with no name
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"type":"TCPServerInterface"}}'
# Expected: validations error
```

### A-305: rnsd start/stop/restart

```sh
# Start
curl -k -X POST https://localhost/api/reticulum/service/rnsdStart
# Expected: {"result":"ok"} or similar

# Wait ~2 seconds, then check status
curl -k https://localhost/api/reticulum/service/rnsdStatus
# Expected: {"status":"running"}

# Confirm process
ssh root@<VM-IP> 'ps aux | grep rnsd | grep -v grep'

# Stop
curl -k -X POST https://localhost/api/reticulum/service/rnsdStop

# Confirm stopped
curl -k https://localhost/api/reticulum/service/rnsdStatus
# Expected: {"status":"stopped"}

# Restart
curl -k -X POST https://localhost/api/reticulum/service/rnsdStart
curl -k -X POST https://localhost/api/reticulum/service/rnsdRestart
curl -k https://localhost/api/reticulum/service/rnsdStatus
# Expected: {"status":"running"}
```

### A-306: lxmd start blocked without rnsd

```sh
# Ensure rnsd is stopped
curl -k -X POST https://localhost/api/reticulum/service/rnsdStop

# Attempt lxmd start
curl -k -X POST https://localhost/api/reticulum/service/lxmdStart
# Expected: {"result":"error","message":"Cannot start lxmd: rnsd is not running..."}
# (exact message may vary; key check is that result is NOT "ok" and lxmd is NOT running)

ssh root@<VM-IP> 'service lxmd status'
# Expected: not running
```

### A-307: Reconfigure

```sh
# Ensure rnsd is enabled and has an interface configured
curl -k -X POST https://localhost/api/reticulum/service/reconfigure
# Expected: {"result":"ok"} or similar

# Verify config files regenerated
ssh root@<VM-IP> 'ls -lt /usr/local/etc/reticulum/config'
# Timestamp should be recent
```

### A-308: rnstatus

```sh
# With rnsd running
curl -k https://localhost/api/reticulum/service/rnstatus
# Expected: JSON with interfaces array

# With rnsd stopped
curl -k -X POST https://localhost/api/reticulum/service/rnsdStop
curl -k https://localhost/api/reticulum/service/rnstatus
# Expected: error message or empty interfaces (not a PHP exception)
```

### A-309: Read-only user restrictions

1. In the OPNsense GUI, go to **System > Access > Users**, create a user `rotest` with privilege `page-services-reticulum-readonly` only.
2. Create an API key for `rotest`.
3. Run the following (replace `KEY:SECRET` with `rotest`'s API key):

```sh
# GET — should succeed (200)
curl -k -u 'KEY:SECRET' https://localhost/api/reticulum/rnsd/get

# POST set — should be rejected (403)
curl -k -u 'KEY:SECRET' -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"loglevel":"5"}}'

# POST addInterface — should be rejected (403)
curl -k -u 'KEY:SECRET' -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"Hack","type":"TCPServerInterface"}}'

# POST delInterface — should be rejected (403)
curl -k -u 'KEY:SECRET' -X POST https://localhost/api/reticulum/rnsd/delInterface/any-uuid
```

**PASS criterion:** All GET requests succeed; all POST mutation requests return HTTP 403.

---

## 9. Running Service Lifecycle Tests (S-401–S-407)

### S-401: Package installation

Run the [smoke test script](#14-smoke-test-script) immediately after `pkg install`.

Manual checks:

```sh
# User exists
pw usershow reticulum

# Dialer group membership
id reticulum | grep dialer

# Virtualenv
ls -la /usr/local/reticulum-venv/bin/rnsd
ls -la /usr/local/reticulum-venv/bin/lxmd

# Directory ownership and permissions
ls -ld /usr/local/etc/reticulum
ls -ld /usr/local/etc/lxmf
ls -ld /var/db/reticulum
ls -ld /var/db/lxmf
ls -ld /var/log/reticulum

# Services NOT running before configuration
service rnsd status
service lxmd status

# Menu visible in GUI
# Navigate to Services > Reticulum in browser
```

**PASS criterion:** All items above pass; menu visible in GUI; services are stopped.

### S-402: Configure and start rnsd

1. In the GUI: **Services > Reticulum > General**
2. Check "Enable rnsd"
3. Go to **Interfaces**, add a TCPServerInterface with port 4242
4. Click Save, then Apply Changes

```sh
# Verify config file
cat /usr/local/etc/reticulum/config
# Must contain [reticulum] and [[<interface-name>]] sections

# Verify service running
service rnsd status
# Expected: rnsd is running

# Verify process owner
ps aux | grep rnsd | grep -v grep
# Expected: process owned by 'reticulum', not root
```

### S-403: Configure and start lxmd

1. In GUI: **Services > Reticulum > LXMF**
2. Enable lxmd, enable propagation node
3. Save and Apply

```sh
service lxmd status
# Expected: lxmd is running

cat /usr/local/etc/lxmf/config
# Must contain [propagation] section with enable_node = yes

ps aux | grep lxmd | grep -v grep
# Expected: process owned by 'reticulum'
```

### S-404: Boot ordering

```sh
# Reboot the VM
shutdown -r now

# After boot, SSH back in
ssh root@<VM-IP>

# Check service states
service rnsd status
service lxmd status
# Both should be running if both were enabled before reboot

# Verify config files exist (syshook ran)
ls -la /usr/local/etc/reticulum/config
ls -la /usr/local/etc/lxmf/config
```

**PASS criterion:** Both services running after reboot with no manual intervention; config files present.

### S-405: Stop rnsd with lxmd running

```sh
# Confirm both running
service rnsd status
service lxmd status

# Stop rnsd
service rnsd stop
# OR via API:
curl -k -X POST https://localhost/api/reticulum/service/rnsdStop

# Observe lxmd behavior
sleep 5
service lxmd status
```

**Expected outcome:** Document the actual behavior. lxmd may continue running in a degraded state, or it may exit. Either outcome is acceptable for v1 — the key point is it does not crash the OS or produce a PHP error. Record the actual behavior in the Notes column of the status tracker.

### S-406: Settings change and reconfigure

```sh
# Add a new interface via GUI or API
# Then apply changes
curl -k -X POST https://localhost/api/reticulum/service/reconfigure

# Verify config updated
ls -lt /usr/local/etc/reticulum/config
grep '<new-interface-name>' /usr/local/etc/reticulum/config

# Verify rnsd restarted (check log timestamp)
tail -5 /var/log/reticulum/rnsd.log
```

### S-407: Clean uninstall

```sh
pkg delete os-reticulum

# Both services stopped
service rnsd status   # expected: not running
service lxmd status   # expected: not running

# Menu removed from GUI
# Refresh browser — Services > Reticulum should 404

# Plugin files removed (spot check)
ls /usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/ 2>&1
# Expected: No such file or directory

# User data PRESERVED
ls -la /usr/local/etc/reticulum/
ls -la /var/db/reticulum/
# Expected: directories and contents still present
```

---

## 10. Running GUI Tests (G-501–G-525)

**Precondition:** Plugin installed. rnsd enabled and configured (S-402 complete). Use a modern browser (Firefox or Chrome). Open the browser console (F12) before navigating to each page to catch JavaScript errors.

### General settings page (G-501 – G-507)

| Test | Action | Expected |
|---|---|---|
| G-501 | Navigate to Services > Reticulum > General | Page loads; browser console shows 0 errors |
| G-502 | First visit with no prior config | All form fields populated with default values |
| G-503 | Fill valid values, click Save | Green success notification appears |
| G-504 | Set shared_instance_port to `99999`, click Save | Red validation error on port field |
| G-505 | Uncheck "Share instance" | `shared_instance_port` and `instance_control_port` fields hide |
| G-506 | Leave page open for 15 seconds | Service status bar updates (check network tab in browser) |
| G-507 | Click Stop, then Start on service bar | rnsd stops then starts; status indicator updates |

### Interfaces page (G-508 – G-516)

| Test | Action | Expected |
|---|---|---|
| G-508 | Navigate to Interfaces page | Grid loads with any pre-configured interfaces |
| G-509 | Click "+" (Add) button | Modal opens with Type selector |
| G-510 | Change Type dropdown from TCPServerInterface to RNodeInterface | TCP fields hide; RNode fields appear |
| G-511 | Add TCPServerInterface with all fields populated | Saves; new row appears in grid |
| G-512 | Add RNodeInterface with port, frequency, bandwidth, txpower, spreadingfactor, codingrate | Saves without error |
| G-513 | Add AutoInterface | Saves |
| G-514 | Click edit (pencil) on existing interface | Modal opens with all fields pre-filled |
| G-515 | Click delete on an interface | Confirmation dialog appears; after confirm, row removed |
| G-516 | Click the enable/disable toggle in the grid row | Row enabled state flips immediately |

### LXMF page (G-517 – G-520)

| Test | Action | Expected |
|---|---|---|
| G-517 | Stop rnsd, then navigate to LXMF page | Warning banner "rnsd is not running" visible |
| G-518 | Uncheck "Enable propagation node" | Propagation-specific fields (announce_interval, message_storage_limit, etc.) hide |
| G-519 | Enter `TOOSHORT` in a hash tag field | Validation error: must be 32 hex characters |
| G-520 | Set from_static_only=yes with empty static_peers | Warning message appears |

### Log viewer (G-521 – G-525)

| Test | Action | Expected |
|---|---|---|
| G-521 | Navigate to Logs > rnsd tab | Log content displayed (or "no log content" if log empty) |
| G-522 | Click lxmd tab | lxmd log content shown |
| G-523 | Select "Error" from severity filter | Only lines containing error-level entries shown |
| G-524 | Type a keyword in the search box | Log lines filtered to matching content only |
| G-525 | Toggle auto-refresh on and off | Log updates automatically when on; stops updating when off |

---

## 11. Running Widget Tests (W-601–W-606)

**Precondition:** rnsd running with at least one interface.

1. Navigate to **Lobby > Dashboard** in the OPNsense GUI.
2. Click **Add Widget**, find and add the **Reticulum** widget.

| Test | Action | Expected |
|---|---|---|
| W-601 | Open Add Widget dialog | Reticulum widget appears in the list |
| W-602 | Widget displayed on dashboard with rnsd + lxmd running | Both show "running" status |
| W-603 | rnsd running with interfaces | Interface table populated with name, type, TX/RX |
| W-604 | Stop rnsd; observe widget | Widget shows degraded state without JS errors |
| W-605 | Leave dashboard open for 20 seconds | Widget data refreshes (verify via network tab — calls at ~15s interval) |
| W-606 | Resize the dashboard column to narrow width (≤300px equivalent) | TX/RX rate columns hide; Type and Status columns remain |

For W-606, simulate narrow widths via browser developer tools: open the responsive design mode and set the viewport width progressively smaller. The widget's `onWidgetResize` breakpoints are at 400px, 300px, and 200px.

---

## 12. Running Security Tests (X-701–X-710)

### X-701 and X-702: Service process owner

```sh
# With both services running
ps aux | grep -E 'rnsd|lxmd' | grep -v grep
```

**PASS:** Both processes show `reticulum` in the USER column, not `root`.

### X-703: Config file permissions

```sh
ls -ld /usr/local/etc/reticulum
ls -ld /usr/local/etc/lxmf
```

**PASS:** Both directories owned by `reticulum` and mode `700` (drwx------).

### X-704: Identity files not world-readable

```sh
ls -la /var/db/reticulum/
ls -la /var/db/lxmf/
```

**PASS:** No file has world-read permission (no `r` in the last group of the mode string).

### X-705: rpc_key not returned in GET

```sh
# First set a value
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"rpc_key":"aabbccddeeff00112233445566778899"}}'

# Then GET
curl -k https://localhost/api/reticulum/rnsd/get
```

**PASS:** The `rpc_key` field is absent from the response, or its value is empty. Any non-empty value in the response is a FAIL.

### X-706: passphrase not returned in GET

```sh
UUID=$(curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"PhraseTest","type":"TCPServerInterface",
       "passphrase":"mysecretphrase","listen_port":"5099"}}' | python3 -c "import sys,json;print(json.load(sys.stdin)['uuid'])")

curl -k https://localhost/api/reticulum/rnsd/getInterface/$UUID
```

**PASS:** `passphrase` is absent from the response or empty.

### X-707: PipeInterface command field — no config injection

```sh
# Attempt to inject INI structure through the command field
# The model mask /^[^\n\r\[\]]{0,512}$/ should reject brackets
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"PipeTest","type":"PipeInterface",
       "command":"/usr/local/bin/myprogram [reticulum] enable_transport = True"}}'
# Expected: validation error (brackets rejected by mask)

# A valid command without brackets should succeed
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d '{"interface":{"name":"PipeTest2","type":"PipeInterface",
       "command":"/usr/local/bin/myprogram --flag value"}}'
# Expected: {"result":"saved"} or uuid returned
```

### X-708: POST endpoints reject GET requests

```sh
# These must reject GET
curl -k https://localhost/api/reticulum/service/rnsdStart
curl -k https://localhost/api/reticulum/service/rnsdStop
curl -k https://localhost/api/reticulum/service/rnsdRestart
curl -k https://localhost/api/reticulum/service/reconfigure
```

**PASS:** Each returns `{"result":"error","message":"POST required"}` or an HTTP 4xx, not a successful action result.

### X-709: CSRF token required on POST endpoints

In the browser (not curl), submit a POST form to a mutation endpoint without a valid CSRF token. The OPNsense framework enforces this automatically for browser sessions; verify by:

1. Log in to the GUI.
2. Open browser developer tools > Network tab.
3. Perform a save on the General settings page.
4. Confirm the request includes an `X-CSRFToken` header (or equivalent OPNsense token mechanism).

**PASS:** The `X-CSRFToken` header is present on all form POST requests.

### X-710: sub_interfaces_raw config injection

```sh
# Add interface with injected content in sub_interfaces_raw
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -H 'Content-Type: application/json' \
  -d "{\"interface\":{\"name\":\"Legit\",\"type\":\"RNodeMultiInterface\",
       \"port\":\"/dev/cuaU0\",
       \"sub_interfaces_raw\":\"[[[A]]]\nfrequency = 915000000\n[reticulum]\n  enable_transport = True\",
       \"enabled\":\"1\"}}"

configctl template reload OPNsense/Reticulum
grep -c '^\[reticulum\]' /usr/local/etc/reticulum/config
```

**PASS criteria:**
1. The count of `[reticulum]` section headers is 1 (the legitimate header at the top).
2. rnsd starts and operates normally (the injected second `[reticulum]` section is overridden by the first occurrence in INI parsing).
3. The GUI displays a warning on the `sub_interfaces_raw` textarea when an RNodeMultiInterface is selected.

Note: The raw block is emitted verbatim by design (see model comment in `Reticulum.xml` line 414–418). The security property here is that INI parsers use the first occurrence of a section, so the injected section cannot override `[reticulum]` settings. Verify this behaviorally by confirming rnsd does not activate transport based on the injected section.

---

## 13. Running Edge Case Tests (E-901–E-910)

**Priority P2 — run after all P0 and P1 tests pass.**

| Test | Steps | Expected |
|---|---|---|
| E-901 | Delete all interfaces, start rnsd | rnsd starts; log may show a warning but service does not crash |
| E-902 | Disable all interfaces (enabled=0), start rnsd | Same behavior as E-901 |
| E-903 | Add interface with name exactly 64 characters (alphanumeric) | Save succeeds; config renders correctly |
| E-904 | Add two interfaces with identical names | Second add returns a validation error |
| E-905 | Set port to `/dev/cuaU99` (non-existent device), start rnsd | rnsd starts; log shows interface error but service stays up |
| E-906 | Manually edit `/usr/local/etc/reticulum/config`, then trigger reconfigure | File is overwritten with model-derived content |
| E-907 | Submit two simultaneous save requests via curl (background jobs) | Both return a result; config is not corrupted |
| E-908 | Remove rnsd binary from venv, call lxmdInfo API | Returns graceful error JSON, no PHP exception |
| E-909 | Disable share_instance in rnsd config, call rnstatus | Returns error JSON explaining shared instance is disabled |
| E-910 | Add 25 interfaces, navigate to Interfaces page | Grid displays with pagination; no JS errors |

For E-907:

```sh
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"loglevel":"5"}}' &

curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -H 'Content-Type: application/json' \
  -d '{"general":{"loglevel":"6"}}' &

wait
# Then verify config is valid
curl -k https://localhost/api/reticulum/rnsd/get | python3 -m json.tool
```

---

## 14. Smoke Test Script

Run this script immediately after installing the plugin on a fresh VM. It performs rapid checks of the installation structure without starting services.

```sh
#!/bin/sh
# os-reticulum smoke test
# Run as root on the OPNsense VM after: pkg install os-reticulum
# A FAIL line means a required component is missing. INFO lines are non-blocking.

echo "=== [1] Checking service user ==="
pw usershow reticulum || echo "FAIL: reticulum user missing"
id reticulum | grep -q dialer && echo "PASS: dialer group OK" || echo "FAIL: reticulum not in dialer group"

echo ""
echo "=== [2] Checking virtualenv ==="
ls /usr/local/reticulum-venv/bin/rnsd  || echo "FAIL: rnsd binary missing from venv"
ls /usr/local/reticulum-venv/bin/lxmd  || echo "FAIL: lxmd binary missing from venv"

echo ""
echo "=== [3] Checking runtime directories ==="
for d in /usr/local/etc/reticulum /usr/local/etc/lxmf /var/db/reticulum /var/db/lxmf /var/log/reticulum; do
    if ls -ld "$d" > /dev/null 2>&1; then
        echo "PASS: $d exists"
    else
        echo "FAIL: $d missing"
    fi
done

echo ""
echo "=== [4] Checking configd actions ==="
configctl reticulum status.rnsd > /dev/null 2>&1 && echo "PASS: configd action status.rnsd OK" || echo "FAIL: configd action status.rnsd failed"

echo ""
echo "=== [5] Generating config templates ==="
configctl template reload OPNsense/Reticulum && echo "PASS: template reload OK" || echo "FAIL: template reload failed"

echo ""
echo "=== [6] Checking generated files ==="
ls -l /usr/local/etc/reticulum/config 2>/dev/null && echo "PASS: rnsd config exists" || echo "INFO: no rnsd config yet (expected if rnsd not enabled)"
ls -l /usr/local/etc/lxmf/config 2>/dev/null && echo "PASS: lxmf config exists"  || echo "INFO: no lxmd config yet (expected if lxmd not enabled)"
ls -l /etc/rc.conf.d/rnsd 2>/dev/null && echo "PASS: rc.conf.d/rnsd exists" || echo "FAIL: rc.conf.d/rnsd missing"
ls -l /etc/rc.conf.d/lxmd 2>/dev/null && echo "PASS: rc.conf.d/lxmd exists" || echo "FAIL: rc.conf.d/lxmd missing"

echo ""
echo "=== Done ==="
```

**Interpreting results:**

- Any `FAIL:` line requires investigation before proceeding.
- `INFO:` lines are expected for a fresh install where the service has never been enabled.
- All `PASS:` lines with no `FAIL:` lines = S-401 passes.

---

## 15. Failure Investigation Guide

### Template test fails

1. Check that `configctl template reload OPNsense/Reticulum` completed without error.
2. Check the configd log: `tail -50 /var/log/configd.log`
3. Inspect the raw Jinja2 template: `/usr/local/opnsense/service/templates/OPNsense/Reticulum/reticulum_config.j2`
4. Inspect the model XML for the field in question: `src/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.xml`
5. Check that the config.xml actually contains the value you set: `grep -i '<fieldname>' /conf/config.xml`

### API returns HTTP 500

1. Check the OPNsense PHP error log: `tail -50 /var/log/php-fpm.log`
2. Check if the model file parses: `php -l /usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.php`
3. Check the controller: `php -l /usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/Api/RnsdController.php`

### Service fails to start

```sh
# Check service rc script
cat /usr/local/etc/rc.d/rnsd
cat /usr/local/etc/rc.d/lxmd

# Check rc.conf.d
cat /etc/rc.conf.d/rnsd

# Try starting manually
/usr/local/reticulum-venv/bin/rnsd --config /usr/local/etc/reticulum/config --verbose
```

### GUI page loads but form is empty

1. Open browser console (F12) and look for XHR errors on the `api/reticulum/rnsd/get` call.
2. Confirm the API returns valid JSON: `curl -k https://localhost/api/reticulum/rnsd/get | python3 -m json.tool`
3. Check that the volt template field names match the model field names.

### configd action not found

```sh
# Restart configd to pick up new actions
service configd restart

# Then retry
configctl reticulum status.rnsd
```

### Widget shows no data / errors

1. Open browser console on the Dashboard page.
2. Look for failed XHR calls to `api/reticulum/service/*`.
3. Check the four endpoints declared in `src/opnsense/www/js/widgets/Metadata/Reticulum.xml` are all responding.

---

## 16. Time Estimates

| Category | Tests | Estimated time |
|---|---|---|
| S-401 (install + smoke test) | 1 | 20 min |
| T-101..T-112 (templates) | 12 | 45 min |
| M-201..M-209 (model validation) | 9 | 30 min |
| A-301..A-309 (API) | 9 | 30 min |
| S-402..S-407 (service lifecycle) | 6 | 45 min (includes reboot) |
| G-501..G-525 (GUI) | 25 | 60 min |
| W-601..W-606 (widget) | 6 | 20 min |
| X-701..X-710 (security) | 10 | 30 min |
| E-901..E-910 (edge cases, P2) | 10 | 45 min |
| **Total** | **88** | **~5.5 hours** |

P0 + P1 tests only (excluding E-901..E-910): approximately 4.5 hours on a prepared VM.

Template-only testing without a VM (T-101..T-112 using local Python harness): approximately 30 minutes.
