# GUI & Widget Manual Test Checklist

Phase 7 — Tests G-501 to G-525, W-601 to W-606

**Instructions:** Work through each test in order. Check the box when passing. Note failures in the Notes column.

---

## G-501 to G-507: General Settings Page

| ID | Test | Steps | Expected | Pass | Notes |
|----|------|-------|----------|------|-------|
| G-501 | Page loads without JS errors | Navigate to Services > Reticulum > General. Open browser console (F12). | No red JS errors in console | ☐ | |
| G-502 | Form populated with defaults on first visit | On a fresh install, load the General page | enable_transport=off, share_instance=on, shared_instance_port=37428, instance_control_port=37429, loglevel=4 | ☐ | |
| G-503 | Save with valid data | Fill in valid values, click Save | Green success banner appears | ☐ | |
| G-504 | Save with invalid port | Set shared_instance_port=0 or 99999, click Save | Red validation error appears, data not saved | ☐ | |
| G-505 | Conditional visibility: share_instance toggles ports | Uncheck "Share Instance" | shared_instance_port and instance_control_port fields hide | ☐ | |
| G-506 | Service status bar updates every 10s | Watch the status bar for 20 seconds | Status refreshes automatically | ☐ | |
| G-507 | Start/Stop/Restart buttons work | Click Start, verify status → running. Click Stop, verify stopped. Click Restart, verify running. | Status bar reflects correct state | ☐ | |

---

## G-508 to G-516: Interfaces Page

| ID | Test | Steps | Expected | Pass | Notes |
|----|------|-------|----------|------|-------|
| G-508 | Grid loads with configured interfaces | Navigate to Services > Reticulum > Interfaces with existing interfaces | Grid shows interface rows with name, type, status | ☐ | |
| G-509 | Add interface modal opens | Click "+" button | Modal opens with Name, Type selector, and a tab panel | ☐ | |
| G-510 | Change type shows correct fields | In the modal, select each type from the dropdown | Only relevant fields for that type are visible (others hidden) | ☐ | |
| G-511 | Add TCPServerInterface | Type=TCPServerInterface, Name="Test TCP", listen_port=4242. Save. | Interface appears in grid | ☐ | |
| G-512 | Add RNodeInterface | Fill required radio fields (port, frequency, bandwidth, txpower, spreadingfactor, codingrate). Save. | Interface appears in grid | ☐ | |
| G-513 | Add AutoInterface | Type=AutoInterface, Name="Auto". Save (no required fields beyond name/type). | Interface appears in grid | ☐ | |
| G-514 | Edit existing interface | Click pencil icon on existing interface | Modal opens with all fields pre-populated correctly | ☐ | |
| G-515 | Delete interface | Click trash icon, confirm in dialog | Interface removed from grid | ☐ | |
| G-516 | Toggle enabled | Click the enable toggle in the grid row | Icon/state changes immediately without page reload | ☐ | |

---

## G-517 to G-520: LXMF Page

| ID | Test | Steps | Expected | Pass | Notes |
|----|------|-------|----------|------|-------|
| G-517 | rnsd dependency warning | Navigate to Services > Reticulum > LXMF with rnsd stopped | Yellow/red banner: "rnsd must be running..." | ☐ | |
| G-518 | Propagation fields hidden | Uncheck "Enable Propagation Node" | Propagation-specific fields (announce_interval, stamp_cost, etc.) hide | ☐ | |
| G-519 | Hash tag inputs validate format | In static_peers or similar field, enter "INVALIDHASH" | Validation error: must be 32-char lowercase hex | ☐ | |
| G-520 | Static-only warning | Set from_static_only=yes, leave static_peers empty | Warning appears: "No static peers configured" | ☐ | |

---

## G-521 to G-525: Log Viewer

| ID | Test | Steps | Expected | Pass | Notes |
|----|------|-------|----------|------|-------|
| G-521 | rnsd log tab | Navigate to Services > Reticulum > Logs, click rnsd tab | rnsd log lines appear | ☐ | |
| G-522 | lxmd log tab | Click lxmd tab | lxmd log lines appear (or "no log file" message) | ☐ | |
| G-523 | Level filter | Set severity filter to "Warning" | Only warning/error lines shown | ☐ | |
| G-524 | Keyword search | Type "interface" in search box | Only lines containing "interface" shown | ☐ | |
| G-525 | Auto-refresh toggle | Click auto-refresh toggle | Button state changes; log auto-updates every ~5s when on | ☐ | |

---

## W-601 to W-606: Dashboard Widget

| ID | Test | Steps | Expected | Pass | Notes |
|----|------|-------|----------|------|-------|
| W-601 | Widget in selection | Go to Dashboard, click "Add Widget" | "Reticulum" appears in the widget list | ☐ | |
| W-602 | Shows service status | Add widget, ensure rnsd is running | rnsd: Running, lxmd: Running/Stopped shown | ☐ | |
| W-603 | Shows interface list | With rnsd running and interfaces configured | Interface table shows name, type, TX/RX rates | ☐ | |
| W-604 | Handles rnsd stopped | Stop rnsd | Widget shows graceful degraded state, no JS errors | ☐ | |
| W-605 | Auto-refresh | Watch widget for 30 seconds | Data updates every 15 seconds | ☐ | |
| W-606 | Responsive width | Resize browser window to < 768px | TX/RX rate columns hide; Type and Status remain visible | ☐ | |

---

## Summary

Total tests: 31
Passed: ___
Failed: ___
Blocked: ___

Tester: _________________
Date: ___________________
OPNsense version: ________
Plugin version: __________
