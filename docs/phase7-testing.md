# Phase 7 — Testing & Validation Plan

## Overview
Comprehensive testing strategy covering template validation, model constraints, API endpoints, service lifecycle, GUI functionality, and security. Tests are categorized by priority: P0 (must pass), P1 (should pass), P2 (nice to have).

---

## 1. Template Output Validation (P0)

### 1.1 Reference Config Files
Create hand-crafted reference configs for comparison.

**Test T-101: Minimal rnsd config (no interfaces)**
- Input: Only `[reticulum]` defaults, no interfaces
- Expected output:
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

**Test T-102: Single TCPServerInterface**
- Input: General defaults + one TCPServerInterface (listen_ip=0.0.0.0, listen_port=4242)
- Verify: `[[Interface Name]]` section with type, listen_ip, listen_port

**Test T-103: One of each interface type**
- Create config.xml with one interface of each of the 12 types
- Verify: Each generates correct type-specific fields, no cross-contamination

**Test T-104: RNodeInterface with all fields**
- Input: RNode with port, frequency, bandwidth, txpower, spreadingfactor, codingrate, airtime limits, id_callsign, id_interval
- Verify: All fields present in output

**Test T-105: RNodeMultiInterface with raw block**
- Input: RNodeMulti with sub_interfaces_raw containing triple-bracket INI
- Verify: Raw block emitted verbatim

**Test T-106: Boolean field mapping**
- Test all boolean fields map correctly: `1` → `True` (rnsd), `1` → `yes` (lxmd)

**Test T-107: Empty optional fields omitted**
- Input: Interface with only required fields
- Verify: Optional fields not in output

**Test T-108: CSV list rendering**
- Input: static_peers = "abc123,def456,789abc"
- Verify: Renders as `static_peers = abc123,def456,789abc`

**Test T-109: Minimal lxmd config**
- Input: lxmf defaults, propagation disabled
- Expected: `[propagation]` section with `enable_node = no` only

**Test T-110: Full lxmd config with propagation**
- Input: All lxmf fields populated, enable_node=1
- Verify: All sections rendered with correct key names

**Test T-111: ACL file templates**
- Input: allowed_identities = "hash1,hash2,hash3"
- Verify: `/usr/local/etc/lxmf/allowed` has one hash per line

**Test T-112: rc.conf.d templates**
- Test: rnsd enabled → `rnsd_enable="YES"`
- Test: rnsd disabled → `rnsd_enable="NO"`
- Test: lxmd enabled but rnsd disabled → `lxmd_enable="NO"`

### How to Test Templates
```sh
# On OPNsense VM after installing plugin:
# 1. Set config values via API
curl -k -X POST https://localhost/api/reticulum/rnsd/set -d '...'

# 2. Render templates
configctl template reload OPNsense/Reticulum

# 3. Diff against reference
diff /usr/local/etc/reticulum/config reference/test-case-N.config
```

---

## 2. Model Validation Testing (P0)

### 2.1 Field Constraint Tests

**Test M-201: Port range validation**
- Set shared_instance_port = 0 → expect error
- Set shared_instance_port = 70000 → expect error
- Set shared_instance_port = 37428 → expect success

**Test M-202: Integer range validation**
- loglevel = -1 → error
- loglevel = 8 → error
- spreadingfactor = 6 → error
- spreadingfactor = 13 → error
- stamp_cost_target = 12 → error (min 13)

**Test M-203: Required fields**
- Interface with empty name → error
- Interface with empty type → error
- general.enabled not set → uses default (0)

**Test M-204: Hex hash format (CSVListField)**
- static_peers = "validhex32chars0123456789abcdef" → success (32 chars)
- static_peers = "TOOSHORT" → error
- static_peers = "has_invalid_chars_in_this_hash!!" → error
- static_peers = "abc123,def456" → success (multiple valid)

**Test M-205: Cross-field: ports must differ**
- shared_instance_port = 37428, instance_control_port = 37428 → error
- shared_instance_port = 37428, instance_control_port = 37429 → success

**Test M-206: Cross-field: stamp cost floor (target − flexibility ≥ 13)**
- stamp_cost_target = 15, stamp_cost_flexibility = 3 → error (floor = 12 < 13)
- stamp_cost_target = 16, stamp_cost_flexibility = 3 → success (floor = 13 ✓)
- stamp_cost_target = 13, stamp_cost_flexibility = 0 → success (floor = 13 ✓)
- stamp_cost_target = 13, stamp_cost_flexibility = 1 → error (floor = 12 < 13)
- stamp_cost_target = 64, stamp_cost_flexibility = 16 → success (floor = 48 ✓)
- stamp_cost_target = 20, stamp_cost_flexibility = 8 → success (floor = 12... wait: 20−8=12 < 13 → error)
- stamp_cost_target = 21, stamp_cost_flexibility = 8 → success (floor = 13 ✓)

**Test M-207: AX25 callsign format**
- callsign = "W1ABC" → success
- callsign = "W1ABC-12" → success
- callsign = "toolongcallsign" → error
- callsign = "w1abc" → error (lowercase)

**Test M-208: UpdateOnlyTextField masking**
- Set passphrase = "secret123"
- GET interface → passphrase not in response (or masked)
- Set interface with no passphrase field → existing value preserved

**Test M-209: Interface name mask**
- name = "My TCP Server" → success
- name = "Interface [1]" → error (brackets in mask)
- name = "" → error (required)

---

## 3. API Endpoint Testing (P0)

### 3.1 CRUD Cycle

**Test A-301: General settings get/set**
```sh
# Get defaults
curl -k https://localhost/api/reticulum/rnsd/get
# Expect: JSON with all general fields at default values

# Set values
curl -k -X POST https://localhost/api/reticulum/rnsd/set \
  -d '{"general":{"enabled":"1","enable_transport":"1","loglevel":"5"}}'
# Expect: {"result":"saved"}

# Verify
curl -k https://localhost/api/reticulum/rnsd/get
# Expect: enabled=1, enable_transport=1, loglevel=5
```

**Test A-302: Interface CRUD cycle**
```sh
# Add
curl -k -X POST https://localhost/api/reticulum/rnsd/addInterface \
  -d '{"interface":{"name":"Test TCP","type":"TCPServerInterface","listen_port":"4242"}}'
# Expect: {"uuid":"<new-uuid>"}

# Search
curl -k https://localhost/api/reticulum/rnsd/searchInterfaces
# Expect: rows containing "Test TCP"

# Get
curl -k https://localhost/api/reticulum/rnsd/getInterface/<uuid>
# Expect: full interface record

# Update
curl -k -X POST https://localhost/api/reticulum/rnsd/setInterface/<uuid> \
  -d '{"interface":{"listen_port":"5555"}}'

# Toggle disable
curl -k -X POST https://localhost/api/reticulum/rnsd/toggleInterface/<uuid>

# Delete
curl -k -X POST https://localhost/api/reticulum/rnsd/delInterface/<uuid>
```

**Test A-303: LXMF get/set**
- Similar to A-301 but for lxmf model node

**Test A-304: Invalid data rejection**
- POST set with loglevel=99 → validation error
- POST addInterface with no name → validation error

### 3.2 Service Actions

**Test A-305: rnsd start/stop/restart**
```sh
curl -k -X POST https://localhost/api/reticulum/service/rnsdStart
# Expect: {"result":"ok"} and rnsd process running

curl -k https://localhost/api/reticulum/service/rnsdStatus
# Expect: {"status":"running"}

curl -k -X POST https://localhost/api/reticulum/service/rnsdStop
curl -k https://localhost/api/reticulum/service/rnsdStatus
# Expect: {"status":"stopped"}
```

**Test A-306: lxmd start blocked without rnsd**
```sh
# Ensure rnsd is stopped
curl -k -X POST https://localhost/api/reticulum/service/rnsdStop

# Try to start lxmd
curl -k -X POST https://localhost/api/reticulum/service/lxmdStart
# Expect: {"result":"error","message":"Cannot start lxmd: rnsd is not running..."}
```

**Test A-307: Reconfigure**
```sh
curl -k -X POST https://localhost/api/reticulum/service/reconfigure
# Verify config files regenerated
```

**Test A-308: rnstatus**
```sh
curl -k https://localhost/api/reticulum/service/rnstatus
# Expect: JSON with interfaces array (when running)
# Expect: error message (when stopped)
```

### 3.3 ACL Testing (P1)

**Test A-309: Read-only user restrictions**
- Create user with `page-services-reticulum-readonly` privilege
- GET endpoints → success
- POST set/add/delete → 403 forbidden

---

## 4. Service Lifecycle Testing (P0)

### 4.1 Fresh Install

**Test S-401: Package installation**
```sh
pkg install os-reticulum
```
Verify:
- [ ] `reticulum` user exists: `pw usershow reticulum`
- [ ] User in dialer group: `id reticulum`
- [ ] Virtualenv exists: `ls /usr/local/reticulum-venv/bin/rnsd`
- [ ] Directories created with correct ownership
- [ ] Services NOT running (not yet configured)
- [ ] Menu visible in OPNsense GUI

### 4.2 Configuration & Start

**Test S-402: Configure and start rnsd**
1. Enable rnsd via GUI
2. Add a TCPServerInterface (port 4242)
3. Save → verify `/usr/local/etc/reticulum/config` exists and is valid
4. Apply Changes → verify rnsd starts
5. `service rnsd status` → running
6. Process running as reticulum user: `ps aux | grep rnsd`

**Test S-403: Configure and start lxmd**
1. Enable lxmd, enable propagation node via GUI
2. Save → verify `/usr/local/etc/lxmf/config` exists
3. Start lxmd → verify it starts (rnsd is running)
4. `service lxmd status` → running

### 4.3 Reboot

**Test S-404: Boot ordering**
1. Reboot OPNsense VM
2. Verify rnsd starts before lxmd
3. Both services running after boot
4. Config files regenerated (syshook ran)

### 4.4 Dependency Enforcement

**Test S-405: Stop rnsd with lxmd running**
1. Both services running
2. Stop rnsd → what happens to lxmd?
3. (lxmd may crash or continue with degraded function — document behavior)

### 4.5 Reconfigure

**Test S-406: Settings change via GUI**
1. Change a setting (e.g., add interface)
2. Save + Apply
3. Verify config file updated
4. Verify rnsd restarted

### 4.6 Uninstall

**Test S-407: Clean uninstall**
```sh
pkg delete os-reticulum
```
Verify:
- [ ] Both services stopped
- [ ] Menu removed from OPNsense
- [ ] Plugin files removed
- [ ] User data preserved: `/usr/local/etc/reticulum/`, `/var/db/reticulum/`
- [ ] No orphaned files (check pkg-plist completeness)

---

## 5. GUI Testing (P1)

### 5.1 General Settings Page

**Test G-501:** Page loads without JS errors
**Test G-502:** Form populated with defaults on first visit
**Test G-503:** Save with valid data → success message
**Test G-504:** Save with invalid port → validation error
**Test G-505:** Conditional visibility: share_instance toggles port fields
**Test G-506:** Service status bar updates every 10s
**Test G-507:** Start/Stop/Restart buttons work

### 5.2 Interfaces Page

**Test G-508:** Grid loads with configured interfaces
**Test G-509:** Add interface → modal opens with type selector
**Test G-510:** Change type → correct fields shown/hidden
**Test G-511:** Add TCPServerInterface with all fields → saves correctly
**Test G-512:** Add RNodeInterface with required radio fields → saves
**Test G-513:** Add AutoInterface → saves
**Test G-514:** Edit existing interface → fields populated correctly
**Test G-515:** Delete interface → confirm dialog → removed from grid
**Test G-516:** Toggle enabled → immediate state change in grid

### 5.3 LXMF Page

**Test G-517:** Page shows rnsd dependency warning when rnsd stopped
**Test G-518:** Propagation fields hidden when enable_node unchecked
**Test G-519:** Hash tag inputs validate 32-char hex format
**Test G-520:** Warning when from_static_only=yes + empty static_peers

### 5.4 Log Viewer

**Test G-521:** rnsd log tab displays log content
**Test G-522:** lxmd log tab displays log content
**Test G-523:** Level filter works
**Test G-524:** Keyword search works
**Test G-525:** Auto-refresh toggles on/off

---

## 6. Dashboard Widget Testing (P1)

**Test W-601:** Widget appears in dashboard widget selection
**Test W-602:** Shows rnsd/lxmd status (running/stopped)
**Test W-603:** Shows interface list when rnsd running
**Test W-604:** Handles rnsd stopped gracefully (no errors)
**Test W-605:** Auto-refreshes every 15 seconds
**Test W-606:** Responsive: TX/RX rate columns hide on narrow width (≤768px viewport); Type and Status columns remain visible

---

## 7. Security Testing (P1)

**Test X-701:** rnsd runs as `reticulum` user, not root
**Test X-702:** lxmd runs as `reticulum` user, not root
**Test X-703:** Config files at `/usr/local/etc/reticulum/` owned by reticulum, mode 700
**Test X-704:** Identity files not world-readable
**Test X-705:** GET api/reticulum/rnsd/get does NOT return rpc_key value
**Test X-706:** GET interface does NOT return passphrase value
**Test X-707:** PipeInterface command field: ensure no command injection through config.xml
**Test X-708:** All POST endpoints reject GET requests
**Test X-709:** CSRF token required on all POST endpoints

**Test X-710: sub_interfaces_raw config injection**
- Set interface name = `Legit`, type = `RNodeMultiInterface`, sub_interfaces_raw = `[[[A]]]\nfrequency = 915000000\n[reticulum]\n  enable_transport = True`
- Trigger reconfigure → verify generated config does NOT contain a second `[reticulum]` section
- Verify rnsd rejects or ignores the injected section (raw block is still emitted verbatim — confirm the malicious `[reticulum]` section is present but overridden by the first occurrence)
- Verify GUI displays security warning on the sub_interfaces_raw textarea

---

## 8. Upgrade Testing (P1)

**Test U-801: v1.0.0 → v1.0.1 upgrade**
1. Install v1.0.0, configure with interfaces and lxmd
2. Build v1.0.1 package
3. `pkg upgrade os-reticulum`
4. Verify all settings preserved in config.xml
5. Verify services restart cleanly
6. Verify virtualenv updated if pip versions changed

---

## 9. Edge Case Testing (P2)

**Test E-901:** No interfaces configured → rnsd starts with warning
**Test E-902:** All interfaces disabled → same as no interfaces
**Test E-903:** Interface name at max length (64 chars)
**Test E-904:** Duplicate interface names → validation error
**Test E-905:** Serial port doesn't exist → non-blocking warning
**Test E-906:** Config file manually edited → next reconfigure overwrites
**Test E-907:** Concurrent saves → last write wins
**Test E-908:** lxmd --version when binary missing → graceful error
**Test E-909:** rnstatus when shared instance disabled → error message
**Test E-910:** Very large number of interfaces (20+) → grid pagination works

---

## 10. Test Environment Setup

### Requirements
- OPNsense VM (FreeBSD 14.x based, matching target OPNsense release)
- At least 2GB RAM, 20GB disk
- Network connectivity for package installation
- SSH access for verification commands

### Setup Steps
1. Install OPNsense on VM
2. Build plugin: `cd os-reticulum && make package`
3. Copy package to VM: `scp os-reticulum-*.pkg root@opnsense:/tmp/`
4. Install: `pkg install /tmp/os-reticulum-*.pkg`
5. Navigate to Services > Reticulum in GUI

### Template Testing Without VM
For template-only testing, the Jinja2 templates can be rendered locally:
```sh
# Create test config.xml snippet
# Use Python + jinja2 to render template
# Diff against reference configs
python3 -c "
from jinja2 import Environment, FileSystemLoader
import xml.etree.ElementTree as ET
# ... render and compare
"
```

### Quick Smoke Test Script
```sh
#!/bin/sh
# Run after installing plugin on OPNsense VM
echo "=== Checking user ==="
pw usershow reticulum || echo "FAIL: user missing"

echo "=== Checking virtualenv ==="
ls /usr/local/reticulum-venv/bin/rnsd || echo "FAIL: venv missing"

echo "=== Checking directories ==="
for d in /usr/local/etc/reticulum /usr/local/etc/lxmf /var/db/reticulum /var/log/reticulum; do
    ls -ld $d || echo "FAIL: $d missing"
done

echo "=== Checking configd actions ==="
configctl reticulum status.rnsd || echo "FAIL: configd action failed"

echo "=== Generating configs ==="
configctl template reload OPNsense/Reticulum || echo "FAIL: template reload failed"

echo "=== Checking generated files ==="
ls -l /usr/local/etc/reticulum/config 2>/dev/null || echo "INFO: no rnsd config yet"
ls -l /usr/local/etc/lxmf/config 2>/dev/null || echo "INFO: no lxmd config yet"

echo "=== Done ==="
```

---

## 11. Priority Summary

| Priority | Count | Category |
|----------|-------|----------|
| P0 | 25 | Template output, model validation, API CRUD, service lifecycle |
| P1 | 25 | GUI pages, widgets, security, ACL, upgrade |
| P2 | 10 | Edge cases, stress testing |
