# Phase 7 — Test Status Tracker

**Plugin version tested:** 1.0.0
**OPNsense version:** ___________
**Tester:** ___________
**Date started:** ___________
**Date completed:** ___________
**Runbook reference:** `docs/phase7-runbook.md`

---

## How to Use This Document

1. Fill in the header fields above before starting.
2. Update the **Status** column as you run each test:
   - `Not Run` — default
   - `Pass` — test produced expected result
   - `Fail` — test produced unexpected result (record detail in Notes)
   - `Blocked` — cannot run because a prerequisite test failed (record blocking test ID in Notes)
3. Record any relevant detail in **Notes** (error messages, workarounds, environment quirks).
4. Update the [Summary](#summary) section when testing is complete.

---

## Category T — Template Output Validation (P0)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| T-101 | Minimal rnsd config with no interfaces matches expected `[reticulum]` + `[logging]` output | P0 | Not Run | |
| T-102 | Single TCPServerInterface generates correct `[[Name]]` section with type, listen_ip, listen_port | P0 | Not Run | |
| T-103 | One of each of the 12 interface types generates correct type-specific fields with no cross-contamination | P0 | Not Run | |
| T-104 | RNodeInterface with all fields (port, frequency, bandwidth, txpower, spreadingfactor, codingrate, airtime limits, id_callsign, id_interval) renders all keys | P0 | Not Run | |
| T-105 | RNodeMultiInterface sub_interfaces_raw block emitted verbatim including triple-bracket headers | P0 | Not Run | |
| T-106 | Boolean fields map correctly: `1`→`True` in rnsd, `1`→`yes` in lxmd | P0 | Not Run | |
| T-107 | Optional fields with no value set are omitted from rendered output | P0 | Not Run | |
| T-108 | CSV list (static_peers) renders as single comma-separated line | P0 | Not Run | |
| T-109 | Minimal lxmd config with propagation disabled: `[propagation]` section contains only `enable_node = no` | P0 | Not Run | |
| T-110 | Full lxmd config with propagation enabled: all sections and keys render with correct INI key names | P0 | Not Run | |
| T-111 | allowed_identities CSVList renders to `/usr/local/etc/lxmf/allowed` as one hash per line | P0 | Not Run | |
| T-112 | rc.conf.d templates: rnsd enabled→YES, rnsd disabled→NO, lxmd enabled but rnsd disabled→NO | P0 | Not Run | |

---

## Category M — Model Validation (P0)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| M-201 | Port range: shared_instance_port rejects 0 and 70000; accepts 37428 | P0 | Not Run | |
| M-202 | Integer ranges: loglevel rejects -1 and 8; spreadingfactor rejects 6 and 13; stamp_cost_target rejects 12 | P0 | Not Run | |
| M-203 | Required fields: interface with empty name fails; interface with empty type fails | P0 | Not Run | |
| M-204 | Hex hash format: 32-char lowercase hex succeeds; too short fails; invalid chars fail; multiple valid items succeed | P0 | Not Run | |
| M-205 | Cross-field: shared_instance_port = instance_control_port fails; different values succeed | P0 | Not Run | |
| M-206 | Cross-field stamp cost floor: target − flexibility ≥ 13 enforced across all 7 test cases | P0 | Not Run | |
| M-207 | AX25 callsign: W1ABC and W1ABC-12 succeed; TOOLONGCALLSIGN and w1abc fail | P0 | Not Run | |
| M-208 | UpdateOnlyTextField: passphrase not returned in GET; existing value preserved when field absent in update | P0 | Not Run | |
| M-209 | Interface name mask: spaces/alphanumeric/dash/underscore succeed; brackets fail; empty fails | P0 | Not Run | |

---

## Category A — API Endpoints (P0/P1)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| A-301 | General settings get/set round-trip: GET returns defaults, POST saves, GET confirms new values | P0 | Not Run | |
| A-302 | Interface CRUD cycle: add, search, get, update, toggle, delete — all return expected results | P0 | Not Run | |
| A-303 | LXMF get/set round-trip | P0 | Not Run | |
| A-304 | Invalid data rejected: loglevel=99 fails; addInterface with no name fails | P0 | Not Run | |
| A-305 | rnsd start/stop/restart via API: status reflects actual process state | P0 | Not Run | |
| A-306 | lxmd start blocked when rnsd stopped: returns error, lxmd does not start | P0 | Not Run | |
| A-307 | Reconfigure: config files regenerated after POST to service/reconfigure | P0 | Not Run | |
| A-308 | rnstatus: returns interface JSON when running; graceful error when stopped | P0 | Not Run | |
| A-309 | Read-only user: GET endpoints succeed; POST mutation endpoints return 403 | P1 | Not Run | |

---

## Category S — Service Lifecycle (P0)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| S-401 | Package install: reticulum user created, dialer group, virtualenv, directories, services stopped, GUI menu visible | P0 | Not Run | |
| S-402 | Configure and start rnsd: config file generated, service running as reticulum user | P0 | Not Run | |
| S-403 | Configure and start lxmd: config file generated, service running as reticulum user | P0 | Not Run | |
| S-404 | Boot ordering: after reboot both services start automatically, config files present | P0 | Not Run | |
| S-405 | Stop rnsd with lxmd running: document lxmd behavior (crash/degrade/continue); no OS-level failure | P0 | Not Run | |
| S-406 | Settings change and reconfigure: config file updated, rnsd restarts cleanly | P0 | Not Run | |
| S-407 | Clean uninstall: services stopped, menu removed, plugin files removed, user data preserved | P0 | Not Run | |

---

## Category G — GUI Functionality (P1)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| G-501 | General settings page loads without JS errors | P1 | Not Run | |
| G-502 | Form populated with defaults on first visit | P1 | Not Run | |
| G-503 | Save with valid data shows success message | P1 | Not Run | |
| G-504 | Save with invalid port shows validation error on field | P1 | Not Run | |
| G-505 | Unchecking share_instance hides shared_instance_port and instance_control_port fields | P1 | Not Run | |
| G-506 | Service status bar updates on a polling interval (no manual refresh needed) | P1 | Not Run | |
| G-507 | Start/Stop/Restart buttons on service bar change service state | P1 | Not Run | |
| G-508 | Interfaces grid loads and displays configured interfaces | P1 | Not Run | |
| G-509 | Add button opens modal with type selector | P1 | Not Run | |
| G-510 | Changing type in modal shows/hides correct type-specific fields | P1 | Not Run | |
| G-511 | Add TCPServerInterface with all fields saves correctly | P1 | Not Run | |
| G-512 | Add RNodeInterface with required radio fields saves correctly | P1 | Not Run | |
| G-513 | Add AutoInterface saves correctly | P1 | Not Run | |
| G-514 | Edit existing interface: modal opens with all fields pre-populated | P1 | Not Run | |
| G-515 | Delete interface: confirmation dialog shown; row removed after confirm | P1 | Not Run | |
| G-516 | Toggle enabled in grid row: state flips immediately | P1 | Not Run | |
| G-517 | LXMF page: rnsd dependency warning banner visible when rnsd stopped | P1 | Not Run | |
| G-518 | LXMF page: propagation fields hide when enable_node unchecked | P1 | Not Run | |
| G-519 | LXMF page: hash tag input validates 32-char lowercase hex format | P1 | Not Run | |
| G-520 | LXMF page: warning shown when from_static_only=yes and static_peers is empty | P1 | Not Run | |
| G-521 | Logs page: rnsd tab displays log content | P1 | Not Run | |
| G-522 | Logs page: lxmd tab displays log content | P1 | Not Run | |
| G-523 | Logs page: severity filter shows only matching lines | P1 | Not Run | |
| G-524 | Logs page: keyword search filters to matching lines | P1 | Not Run | |
| G-525 | Logs page: auto-refresh toggle starts/stops polling | P1 | Not Run | |

---

## Category W — Dashboard Widget (P1)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| W-601 | Widget appears in the Add Widget dialog on the Dashboard | P1 | Not Run | |
| W-602 | Widget displays correct running/stopped status for both rnsd and lxmd | P1 | Not Run | |
| W-603 | Widget shows interface list (name, type, TX/RX) when rnsd running with interfaces | P1 | Not Run | |
| W-604 | Widget handles rnsd stopped state gracefully — no JS errors, shows degraded state | P1 | Not Run | |
| W-605 | Widget auto-refreshes at ~15-second interval without manual action | P1 | Not Run | |
| W-606 | At narrow viewport widths (≤300px): TX/RX columns hide; Type and Status columns remain | P1 | Not Run | |

---

## Category X — Security (P1)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| X-701 | rnsd process runs as `reticulum` user, not root | P1 | Not Run | |
| X-702 | lxmd process runs as `reticulum` user, not root | P1 | Not Run | |
| X-703 | Config directories `/usr/local/etc/reticulum/` and `/usr/local/etc/lxmf/` owned by reticulum, mode 700 | P1 | Not Run | |
| X-704 | Identity files in `/var/db/reticulum/` and `/var/db/lxmf/` not world-readable | P1 | Not Run | |
| X-705 | GET `api/reticulum/rnsd/get` does not return rpc_key value | P1 | Not Run | |
| X-706 | GET `api/reticulum/rnsd/getInterface/<uuid>` does not return passphrase value | P1 | Not Run | |
| X-707 | PipeInterface command field: brackets and newlines rejected by model mask | P1 | Not Run | |
| X-708 | All POST-only service endpoints reject GET requests | P1 | Not Run | |
| X-709 | CSRF token present on all POST requests from the GUI | P1 | Not Run | |
| X-710 | sub_interfaces_raw config injection: injected `[reticulum]` section does not override primary; GUI displays warning | P1 | Not Run | |

---

## Category E — Edge Cases (P2)

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| E-901 | No interfaces configured: rnsd starts with warning but does not crash | P2 | Not Run | |
| E-902 | All interfaces disabled (enabled=0): same behavior as no interfaces | P2 | Not Run | |
| E-903 | Interface name at maximum length (64 chars): save succeeds, config renders | P2 | Not Run | |
| E-904 | Duplicate interface names: second add returns validation error | P2 | Not Run | |
| E-905 | Serial port device does not exist: rnsd starts with non-blocking interface error | P2 | Not Run | |
| E-906 | Manually edited config file overwritten by next reconfigure | P2 | Not Run | |
| E-907 | Two concurrent save requests: both return a result, config is not corrupted | P2 | Not Run | |
| E-908 | rnsd binary missing from virtualenv: lxmdInfo API returns graceful error, no PHP exception | P2 | Not Run | |
| E-909 | share_instance disabled: rnstatus returns descriptive error, not PHP exception | P2 | Not Run | |
| E-910 | 25+ interfaces in grid: pagination works, no JS errors | P2 | Not Run | |

---

## Summary

Update this table at the end of each test session.

### By Priority

| Priority | Total | Pass | Fail | Blocked | Not Run |
|----------|-------|------|------|---------|---------|
| P0 | 43 | | | | 43 |
| P1 | 35 | | | | 35 |
| P2 | 10 | | | | 10 |
| **Total** | **88** | | | | **88** |

### By Category

| Category | Total | Pass | Fail | Blocked | Not Run |
|----------|-------|------|------|---------|---------|
| T — Templates | 12 | | | | 12 |
| M — Model Validation | 9 | | | | 9 |
| A — API | 9 | | | | 9 |
| S — Service Lifecycle | 7 | | | | 7 |
| G — GUI | 25 | | | | 25 |
| W — Widget | 6 | | | | 6 |
| X — Security | 10 | | | | 10 |
| E — Edge Cases | 10 | | | | 10 |
| **Total** | **88** | | | | **88** |

### Known Gaps / Outstanding Issues

Record any gaps discovered during testing that are not covered by an existing test case.

| Date | Description | Severity | Status |
|------|-------------|----------|--------|
| | | | |

### Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | | | |
| Reviewer | | | |
