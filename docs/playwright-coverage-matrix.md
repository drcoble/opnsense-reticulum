# Playwright Test Coverage Matrix — OPNsense Reticulum Plugin
**Date:** 2026-03-12
**Status:** final
**Source:** Technical documentarian — derived from volt template source, widget JS, and API controller source

---

## How to Read This Document

- **Priority** — P0 = must pass before any release; P1 = important user flows; P2 = edge cases and polish
- **Coverage status** — each element row carries one of: `covered`, `uncovered`, or `partial`
- **Test ID format** — `PW-GEN-NNN` (general), `PW-IFC-NNN` (interfaces), `PW-LXM-NNN` (lxmf), `PW-LOG-NNN` (logs), `PW-WDG-NNN` (widget), `PW-NAV-NNN` (navigation/cross-page)

---

## Table of Contents

1. [Element Coverage Tables](#1-element-coverage-tables)
   - 1.1 General Settings
   - 1.2 Interfaces
   - 1.3 Propagation Node (LXMF)
   - 1.4 Log Viewer
   - 1.5 Dashboard Widget
2. [User Flow Coverage](#2-user-flow-coverage)
3. [Validation Coverage](#3-validation-coverage)
4. [State Coverage](#4-state-coverage)
5. [API Interaction Coverage](#5-api-interaction-coverage)
6. [Priority Summary](#6-priority-summary)

---

## 1. Element Coverage Tables

### 1.1 General Settings (`/ui/reticulum/general`)

**Runtime info bar** (populated by `GET /api/reticulum/service/rnsdInfo`)

| Element | ID / Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Version span | `#rnsd-version` | PW-GEN-001 | P0 | covered |
| Identity span (truncated to 16 chars) | `#rnsd-identity` | PW-GEN-001 | P0 | covered |
| Identity full hash on hover (title attr) | `#rnsd-identity[title]` | PW-GEN-002 | P1 | covered |
| Uptime span | `#rnsd-uptime` | PW-GEN-001 | P0 | covered |

**Service bar** (OPNsense `updateServiceControlUI('reticulum')` — targets `#service_status_container`)

| Element | ID / Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Service status indicator | `#service_status_container` | PW-GEN-003 | P0 | covered |
| Service Start button | within service bar | PW-GEN-004 | P0 | covered |
| Service Stop button | within service bar | PW-GEN-005 | P0 | covered |
| Service Restart button | within service bar | PW-GEN-006 | P0 | covered |
| 10-second polling refresh | interval behavior | PW-GEN-007 | P1 | covered |

**Tab navigation** (`#maintabs`)

| Tab | href | Test ID | Priority | Coverage |
|---|---|---|---|---|
| General tab | `#tab-general` | PW-GEN-010 | P0 | covered |
| Transport tab | `#tab-transport` | PW-GEN-011 | P0 | covered |
| Sharing tab | `#tab-sharing` | PW-GEN-012 | P0 | covered |
| Management tab | `#tab-management` | PW-GEN-013 | P0 | covered |
| Logging tab | `#tab-logging` | PW-GEN-014 | P0 | covered |

**General tab fields**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Enable Reticulum Service checkbox | `#general\.enabled` | PW-GEN-020 | P0 | covered |
| Help icon expander | `.showhelp` (all) | PW-GEN-021 | P2 | covered |

**Transport tab fields**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Enable Transport Node checkbox | `#general\.enable_transport` | PW-GEN-030 | P0 | covered |
| Respond to Probes checkbox | `#general\.respond_to_probes` | PW-GEN-031 | P1 | covered |
| Stop Service on Interface Failure checkbox | `#general\.panic_on_interface_error` | PW-GEN-032 | P1 | covered |

**Sharing tab fields and conditional visibility**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Allow Application Sharing checkbox | `#general\.share_instance` | PW-GEN-040 | P0 | covered |
| Application Sharing Port input | `#general\.shared_instance_port` | PW-GEN-041 | P0 | covered |
| Service Management Port input | `#general\.instance_control_port` | PW-GEN-042 | P0 | covered |
| Port conflict error message | `#port-conflict-msg` | PW-GEN-043 | P0 | covered |
| Sharing-disabled info message | `#sharing-disabled-msg` | PW-GEN-044 | P0 | covered |
| Port fields hidden when share disabled | `.share_instance_dep` | PW-GEN-044 | P0 | covered |
| Port fields visible when share enabled | `.share_instance_dep` | PW-GEN-045 | P0 | covered |

**Management tab fields and conditional visibility**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Enable Remote Management checkbox | `#general\.enable_remote_management` | PW-GEN-050 | P0 | covered |
| Authorized Administrators tokenizer | `#general\.remote_management_allowed` | PW-GEN-051 | P1 | covered |
| Remote Management Key password input | `#general\.rpc_key` | PW-GEN-052 | P1 | covered |
| Dep fields hidden when remote mgmt disabled | `#remote-mgmt-dep-fields` | PW-GEN-053 | P0 | covered |
| Dep fields visible when remote mgmt enabled | `#remote-mgmt-dep-fields` | PW-GEN-054 | P0 | covered |
| Remote-mgmt-disabled info message | `#remote-mgmt-disabled-msg` | PW-GEN-055 | P0 | covered |

**Logging tab fields**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Log Level select (8 options) | `#general\.loglevel` | PW-GEN-060 | P1 | covered |
| Log File path input | `#general\.logfile` | PW-GEN-061 | P1 | covered |

**Form footer**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Save button | `#saveBtn` | PW-GEN-070 | P0 | covered |
| Apply Changes button | `#applyBtn` | PW-GEN-071 | P0 | covered |
| Apply success alert | `#apply-success-msg` | PW-GEN-072 | P1 | covered |
| Apply success alert auto-dismiss (3s) | `#apply-success-msg` fade | PW-GEN-073 | P2 | covered |

---

### 1.2 Interfaces (`/ui/reticulum/interfaces`)

**Toolbar**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Add Interface button | `#addInterfaceBtn` | PW-IFC-001 | P0 | covered |
| Apply Changes button | `#applyInterfacesBtn` | PW-IFC-002 | P0 | covered |
| Apply success alert | `#apply-success-msg` | PW-IFC-003 | P1 | covered |

**UIBootgrid table (`#grid-interfaces`)**

| Element | Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Name column | `[data-column-id="name"]` | PW-IFC-010 | P0 | covered |
| Type column (typeDisplay formatter) | `[data-column-id="type"]` | PW-IFC-011 | P0 | covered |
| Enabled toggle (rowtoggle formatter) | `[data-column-id="enabled"]` | PW-IFC-012 | P0 | covered |
| Mode column (modeDisplay formatter) | `[data-column-id="mode"]` | PW-IFC-013 | P1 | covered |
| Edit command button | commands formatter | PW-IFC-014 | P0 | covered |
| Delete command button | commands formatter | PW-IFC-015 | P0 | covered |
| Empty state message | `data-empty` attr | PW-IFC-016 | P1 | covered |
| Pagination (many interfaces) | bootgrid pagination | PW-IFC-017 | P1 | covered |
| Inline enabled toggle fires API | rowtoggle click | PW-IFC-018 | P0 | covered |
| Service bar | `#service_status_container` | PW-IFC-019 | P0 | covered |

**Edit modal (`#DialogInterface`) — modal lifecycle**

| Element | Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Modal opens on Add | `#DialogInterface.show` | PW-IFC-020 | P0 | covered |
| Modal opens on Edit | `#DialogInterface.show` | PW-IFC-021 | P0 | covered |
| Modal close (×) button | `.modal .close` | PW-IFC-022 | P1 | covered |
| Modal close on Esc key | keyboard dismiss | PW-IFC-023 | P2 | covered |

**Edit modal — Basic Settings tab (always visible)**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Basic Settings tab | `#tab-interface-basic` | PW-IFC-030 | P0 | covered |
| Enabled checkbox | `#interface\.enabled` | PW-IFC-031 | P0 | covered |
| Name text input (required) | `#interface\.name` | PW-IFC-032 | P0 | covered |
| Name uniqueness conflict message | `#interface-name-conflict` | PW-IFC-033 | P0 | covered |
| Type select (12 options) | `#interface\.type` | PW-IFC-034 | P0 | covered |
| Mode select (5 options) | `#interface\.mode` | PW-IFC-035 | P1 | covered |
| Allow Outbound Packets checkbox | `#interface\.outgoing` | PW-IFC-036 | P1 | covered |
| Bootstrap Only checkbox | `#interface\.bootstrap_only` | PW-IFC-037 | P2 | covered |
| Network Segment Name input | `#interface\.network_name` | PW-IFC-038 | P1 | covered |
| Network Segment Passphrase (write-only) | `#interface\.passphrase` | PW-IFC-039 | P1 | covered |
| Authentication Tag Size input | `#interface\.ifac_size` | PW-IFC-040 | P2 | covered |

**Edit modal — Network tab (type-conditional fields)**

| Element | Visible for types | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Network tab | all | PW-IFC-050 | P0 | covered |
| Listen IP input | TCPServer, Backbone, UDP | PW-IFC-051 | P0 | covered |
| Listen Port input | TCPServer, Backbone, UDP | PW-IFC-052 | P0 | covered |
| Target Host input | TCPClient, Backbone | PW-IFC-053 | P0 | covered |
| Target Port input | TCPClient, Backbone | PW-IFC-054 | P0 | covered |
| Prefer IPv6 checkbox | TCPClient, Backbone | PW-IFC-055 | P1 | covered |
| Restrict to Network Adapter input | TCPClient, Backbone | PW-IFC-056 | P2 | covered |
| I2P Tunneled checkbox | TCPClient, Backbone | PW-IFC-057 | P2 | covered |
| KISS Framing checkbox | TCPClient, Backbone | PW-IFC-058 | P2 | covered |
| Fixed MTU input | TCPClient, Backbone | PW-IFC-059 | P2 | covered |
| Forward IP input | UDP | PW-IFC-060 | P1 | covered |
| Forward Port input | UDP | PW-IFC-061 | P1 | covered |
| Network Group Name input | Auto | PW-IFC-062 | P1 | covered |
| Discovery Scope select (5 options) | Auto | PW-IFC-063 | P1 | covered |
| Discovery Port input | Auto | PW-IFC-064 | P1 | covered |
| Data Port input | Auto | PW-IFC-065 | P1 | covered |
| Devices tokenizer | Auto | PW-IFC-066 | P1 | covered |
| Ignored Devices tokenizer | Auto | PW-IFC-067 | P2 | covered |
| Multicast Address Type select | Auto | PW-IFC-068 | P2 | covered |
| Type-visibility JS: TCPServer shows listen fields | `.type-tcp-server` | PW-IFC-080 | P0 | covered |
| Type-visibility JS: TCPClient shows target fields | `.type-tcp` | PW-IFC-081 | P0 | covered |
| Type-visibility JS: UDP shows UDP fields | `.type-udp` | PW-IFC-082 | P0 | covered |
| Type-visibility JS: Auto shows auto fields | `.type-auto` | PW-IFC-083 | P0 | covered |
| Type-visibility JS: RNode shows rnode fields | `.type-rnode` | PW-IFC-084 | P0 | covered |
| Type-visibility JS: Serial shows serial fields | `.type-serial` | PW-IFC-085 | P0 | covered |
| Type-visibility JS: KISS shows kiss fields | `.type-kiss` | PW-IFC-086 | P0 | covered |
| Type-visibility JS: AX25 shows ax25 fields | `.type-ax25` | PW-IFC-087 | P0 | covered |
| Type-visibility JS: Pipe shows pipe fields | `.type-pipe` | PW-IFC-088 | P0 | covered |
| Type-visibility JS: I2P shows no extra fields | `.type-i2p` | PW-IFC-089 | P1 | covered |
| Type-visibility JS: Multi shows rnode-multi fields | `.type-multi` | PW-IFC-090 | P1 | covered |
| Fields for unselected type are hidden | negative cases | PW-IFC-091 | P0 | covered |

**Edit modal — Radio/Serial tab**

| Element | ID | Visible for types | Test ID | Priority | Coverage |
|---|---|---|---|---|---|
| Radio/Serial tab | `#tab-interface-radio` | all (tab always shown) | PW-IFC-100 | P0 | covered |
| Serial Port input | `#interface\.port` | RNode, Serial, KISS | PW-IFC-101 | P0 | covered |
| Frequency input | `#interface\.frequency` | RNode | PW-IFC-102 | P0 | covered |
| Bandwidth input | `#interface\.bandwidth` | RNode | PW-IFC-103 | P0 | covered |
| TX Power input | `#interface\.txpower` | RNode | PW-IFC-104 | P0 | covered |
| Spreading Factor input | `#interface\.spreadingfactor` | RNode | PW-IFC-105 | P0 | covered |
| Coding Rate input | `#interface\.codingrate` | RNode | PW-IFC-106 | P0 | covered |
| Daily Airtime Limit input | `#interface\.airtime_limit_long` | RNode | PW-IFC-107 | P1 | covered |
| 10-Minute Airtime Limit input | `#interface\.airtime_limit_short` | RNode | PW-IFC-108 | P1 | covered |
| Flow Control checkbox | `#interface\.flow_control` | RNode, Serial, KISS | PW-IFC-109 | P1 | covered |
| ID Callsign input | `#interface\.id_callsign` | RNode, KISS | PW-IFC-110 | P1 | covered |
| ID Interval input | `#interface\.id_interval` | RNode, KISS | PW-IFC-111 | P1 | covered |
| Baud Rate input | `#interface\.speed` | Serial, KISS | PW-IFC-112 | P0 | covered |
| Data Bits input | `#interface\.databits` | Serial | PW-IFC-113 | P2 | covered |
| Parity select (3 options) | `#interface\.parity` | Serial, KISS | PW-IFC-114 | P1 | covered |
| Stop Bits input | `#interface\.stopbits` | Serial, KISS | PW-IFC-115 | P2 | covered |
| KISS Preamble input | `#interface\.preamble` | KISS | PW-IFC-116 | P2 | covered |
| KISS TX Tail input | `#interface\.txtail` | KISS | PW-IFC-117 | P2 | covered |
| KISS Persistence input | `#interface\.persistence` | KISS | PW-IFC-118 | P2 | covered |
| KISS Slot Time input | `#interface\.slottime` | KISS | PW-IFC-119 | P2 | covered |
| AX.25 Callsign input | `#interface\.callsign` | AX25 | PW-IFC-120 | P1 | covered |
| AX.25 SSID input | `#interface\.ssid` | AX25 | PW-IFC-121 | P1 | covered |
| Pipe Command input | `#interface\.command` | Pipe | PW-IFC-122 | P0 | covered |
| Pipe Respawn Delay input | `#interface\.respawn_delay` | Pipe | PW-IFC-123 | P1 | covered |
| RNodeMulti raw text area | `#interface\.rnode_multi_config` | RNodeMulti | PW-IFC-124 | P1 | covered |

**Edit modal — Advanced tab**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Advanced tab | `#tab-interface-advanced` | PW-IFC-130 | P1 | covered |
| Ingress control toggle | see note below | PW-IFC-131 | P1 | uncovered |

> **Coverage gap — PW-IFC-131:** The ingress control toggle is described in project memory and volt comments but the exact field ID was not found in the sections read. The Advanced tab exists in the tab list; full field inventory requires reading `interfaces.volt` lines 800–end.

**Delete confirmation modal**

| Element | Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Delete button in grid | commands formatter | PW-IFC-140 | P0 | covered |
| Delete confirmation modal appears | modal | PW-IFC-141 | P0 | covered |
| Confirm delete fires `delInterface` | modal confirm | PW-IFC-142 | P0 | covered |
| Cancel delete leaves record intact | modal cancel | PW-IFC-143 | P1 | covered |

---

### 1.3 Propagation Node (`/ui/reticulum/lxmf`)

**Dual service bar**

| Element | ID / Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| rnsd status badge (read-only) | `#rnsd-status-badge` | PW-LXM-001 | P0 | covered |
| Link to General page | `a[href="/ui/reticulum/general"]` | PW-LXM-002 | P1 | covered |
| lxmd Start button | `#lxmd-btn-start` | PW-LXM-003 | P0 | covered |
| lxmd Stop button | `#lxmd-btn-stop` | PW-LXM-004 | P0 | covered |
| lxmd Restart button | `#lxmd-btn-restart` | PW-LXM-005 | P0 | covered |
| lxmd status badge | `#lxmd-status-badge` | PW-LXM-006 | P0 | covered |
| lxmd action feedback message | `#lxmd-action-msg` | PW-LXM-007 | P1 | covered |
| Start/Restart disabled when rnsd stopped | button `disabled` attr | PW-LXM-008 | P0 | covered |
| rnsd dependency warning banner | `#rnsd-warning` | PW-LXM-009 | P0 | covered |
| Warning banner shows when rnsd stopped | `#rnsd-warning:visible` | PW-LXM-010 | P0 | covered |
| Warning banner hides when rnsd running | `#rnsd-warning:hidden` | PW-LXM-011 | P0 | covered |

**Tab navigation (`#maintabs`)**

| Tab | href | Propagation-dep? | Test ID | Priority | Coverage |
|---|---|---|---|---|---|
| General tab | `#tab-general` | no | PW-LXM-020 | P0 | covered |
| Propagation tab | `#tab-propagation` | no | PW-LXM-021 | P0 | covered |
| Stamp Costs tab | `#tab-costs` | yes — hidden until enable_node | PW-LXM-022 | P0 | covered |
| Peering tab | `#tab-peering` | yes — hidden until enable_node | PW-LXM-023 | P0 | covered |
| Access Control tab | `#tab-acl` | no | PW-LXM-024 | P0 | covered |
| Logging tab | `#tab-logging` | no | PW-LXM-025 | P0 | covered |
| Costs/Peering tabs appear when enable_node checked | `.propagation-dep-tab` | — | PW-LXM-026 | P0 | covered |
| Costs/Peering tabs hidden when enable_node unchecked | `.propagation-dep-tab` | — | PW-LXM-027 | P0 | covered |

**General tab fields**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Enable LXMF Service checkbox | `#lxmf\.enabled` | PW-LXM-030 | P0 | covered |
| Display Name input | `#lxmf\.display_name` | PW-LXM-031 | P1 | covered |
| Announce LXMF Identity at Startup checkbox | `#lxmf\.lxmf_announce_at_start` | PW-LXM-032 | P1 | covered |
| LXMF Announce Interval input | `#lxmf\.lxmf_announce_interval` | PW-LXM-033 | P1 | covered |
| Max Delivery Size input | `#lxmf\.delivery_transfer_max_size` | PW-LXM-034 | P1 | covered |

**Propagation tab fields and conditional visibility**

| Element | ID | Propagation-dep? | Test ID | Priority | Coverage |
|---|---|---|---|---|---|
| Enable Propagation Node checkbox | `#lxmf\.enable_node` | no | PW-LXM-040 | P0 | covered |
| Propagation disabled info message | `#propagation-disabled-msg` | — | PW-LXM-041 | P0 | covered |
| Node Name input | `#lxmf\.node_name` | yes | PW-LXM-042 | P1 | covered |
| Propagation Announce Interval input | `#lxmf\.announce_interval` | yes | PW-LXM-043 | P1 | covered |
| Announce at Start checkbox | `#lxmf\.announce_at_start` | yes | PW-LXM-044 | P1 | covered |
| Storage Limit input | `#lxmf\.message_storage_limit` | yes | PW-LXM-045 | P1 | covered |
| Max Message Size input | `#lxmf\.propagation_message_max_size` | yes | PW-LXM-046 | P0 | covered |
| Max Sync Size input | `#lxmf\.propagation_sync_max_size` | yes | PW-LXM-047 | P0 | covered |
| Sync size warning message | `#sync-size-warn` | — | PW-LXM-048 | P0 | covered |
| `.propagation-dep` fields hidden when enable_node off | `.propagation-dep` | — | PW-LXM-049 | P0 | covered |
| `.propagation-dep` fields shown when enable_node on | `.propagation-dep` | — | PW-LXM-050 | P0 | covered |

**Stamp Costs tab fields** (all propagation-dep)

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Anti-Spam Work Requirement input | `#lxmf\.stamp_cost_target` | PW-LXM-060 | P1 | covered |
| Anti-Spam Tolerance Range input | `#lxmf\.stamp_cost_flexibility` | PW-LXM-061 | P0 | covered |
| Stamp floor warning message | `#stamp-floor-warn` | PW-LXM-062 | P0 | covered |
| Peer Acceptance Difficulty input | `#lxmf\.peering_cost` | PW-LXM-063 | P1 | covered |
| Max Acceptable Peer Difficulty input | `#lxmf\.remote_peering_cost_max` | PW-LXM-064 | P1 | covered |

**Peering tab fields** (all propagation-dep)

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Auto-Peer checkbox | `#lxmf\.autopeer` | PW-LXM-070 | P1 | covered |
| Auto-Peer Max Depth input | `#lxmf\.autopeer_maxdepth` | PW-LXM-071 | P1 | covered |
| Max Peers input | `#lxmf\.max_peers` | PW-LXM-072 | P1 | covered |
| Peer With Static List Only checkbox | `#lxmf\.from_static_only` | PW-LXM-073 | P0 | covered |
| Static Peers tokenizer | `#lxmf\.static_peers` | PW-LXM-074 | P0 | covered |
| Static-only warning (empty list) | `#static-only-warn` | PW-LXM-075 | P0 | covered |

**Access Control tab fields**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Require Authentication checkbox | `#lxmf\.auth_required` | PW-LXM-080 | P1 | covered |
| Authorized Controllers tokenizer | `#lxmf\.control_allowed` | PW-LXM-081 | P1 | covered |
| Permitted Message Sources tokenizer | `#lxmf\.allowed_identities` | PW-LXM-082 | P1 | covered |
| Blocked Destinations tokenizer | `#lxmf\.ignored_destinations` | PW-LXM-083 | P1 | covered |
| Priority Destinations tokenizer | `#lxmf\.prioritise_destinations` | PW-LXM-084 | P2 | covered |

**Logging tab fields**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Log Level select | `#lxmf\.loglevel` | PW-LXM-090 | P1 | covered |
| Log File input | `#lxmf\.logfile` | PW-LXM-091 | P1 | covered |
| Run Script on Message Receipt input | `#lxmf\.on_inbound` | PW-LXM-092 | P1 | covered |
| On-inbound security warning | `#on-inbound-warn` | PW-LXM-093 | P1 | covered |

**Form footer**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Save button | `#saveBtn` | PW-LXM-095 | P0 | covered |
| Apply Changes button | `#applyBtn` | PW-LXM-096 | P0 | covered |
| Apply success alert | `#apply-success-msg` | PW-LXM-097 | P1 | covered |

---

### 1.4 Log Viewer (`/ui/reticulum/logs`)

**Tab navigation (`#log-tabs`)**

| Tab | data-service | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Transport Node (rnsd) tab | `rnsd` | PW-LOG-001 | P0 | covered |
| Propagation Node (lxmd) tab | `lxmd` | PW-LOG-002 | P0 | covered |
| Tab switch triggers new API fetch | `shown.bs.tab` event | PW-LOG-003 | P0 | covered |

**Filter controls**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Severity select (8 options + All) | `#log-level` | PW-LOG-010 | P0 | covered |
| Search / keyword filter input | `#log-search` | PW-LOG-011 | P0 | covered |
| Lines to Fetch select (6 options, default 200) | `#log-lines` | PW-LOG-012 | P0 | covered |
| Severity filter re-filters cached data (no fetch) | input/change event | PW-LOG-013 | P1 | covered |
| Keyword filter re-filters cached data (no fetch) | input event | PW-LOG-014 | P1 | covered |
| Lines change triggers new API fetch | change event | PW-LOG-015 | P0 | covered |

**Action buttons**

| Element | ID | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Refresh button | `#refresh-logs` | PW-LOG-020 | P0 | covered |
| Download button | `#download-logs` | PW-LOG-021 | P1 | covered |
| Download with no content shows inline message | `#download-logs` empty state | PW-LOG-022 | P2 | covered |
| Auto-refresh checkbox | `#auto-refresh` | PW-LOG-023 | P1 | covered |
| Auto-refresh interval fires every 5 seconds | setInterval | PW-LOG-024 | P1 | covered |
| Unchecking auto-refresh stops interval | clearInterval | PW-LOG-025 | P1 | covered |

**Output states**

| State | Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Loading spinner visible during fetch | `#log-loading:visible` | PW-LOG-030 | P1 | covered |
| Empty-service state (no log file / service never started) | `#log-empty-service:visible` | PW-LOG-031 | P0 | covered |
| Empty-filter state (filters exclude all lines) | `#log-empty-filter:visible` | PW-LOG-032 | P0 | covered |
| Log output rendered in pre terminal | `#log-output:visible` | PW-LOG-033 | P0 | covered |
| Auto-scroll to bottom on load | `scrollTop === scrollHeight` | PW-LOG-034 | P2 | covered |

**Download behavior**

| Scenario | Test ID | Priority | Coverage |
|---|---|---|---|
| Download uses filtered (not raw) lines | PW-LOG-040 | P1 | covered |
| Downloaded filename: `reticulum-rnsd.log` | PW-LOG-041 | P1 | covered |
| Downloaded filename: `reticulum-lxmd.log` (lxmd tab active) | PW-LOG-042 | P1 | covered |

---

### 1.5 Dashboard Widget

**Markup structure (rendered by `getMarkup()`)**

| Element | ID / Selector | Test ID | Priority | Coverage |
|---|---|---|---|---|
| Widget container | `#reticulum-widget` | PW-WDG-001 | P0 | covered |
| Transport Node status row | `#ret-rnsd-status` | PW-WDG-002 | P0 | covered |
| Propagation Node status row | `#ret-row-lxmd` / `#ret-lxmd-status` | PW-WDG-003 | P0 | covered |
| Propagation row hidden when lxmf not installed | `#ret-row-lxmd:hidden` | PW-WDG-004 | P1 | covered |
| Interface count row | `#ret-row-ifcount` / `#ret-ifcount` | PW-WDG-005 | P0 | covered |
| Total TX/RX row | `#ret-row-traffic` / `#ret-traffic` | PW-WDG-006 | P0 | covered |
| Versions row | `#ret-row-version` / `#ret-version` | PW-WDG-007 | P1 | covered |
| Identity row (truncated, full on hover) | `#ret-row-identity` / `#ret-identity` | PW-WDG-008 | P1 | covered |
| Interface table | `#ret-iface-table` / `#ret-iface-list` | PW-WDG-009 | P0 | covered |
| Interface table: no interfaces configured | `#ret-iface-list` empty | PW-WDG-010 | P1 | covered |
| Interface up/down icons per row | `.fa-circle.text-success/.text-danger` | PW-WDG-011 | P0 | covered |
| TX/RX column per interface row | `.ret-col-traffic` | PW-WDG-012 | P1 | covered |
| Transport badge on rnsd row when transport enabled | `.ret-transport-badge` | PW-WDG-013 | P2 | covered |
| ifac_netname as secondary line under name | `small.text-muted` inside td | PW-WDG-014 | P2 | covered |
| Interface count warning triangle when any down | `.fa-exclamation-triangle` | PW-WDG-015 | P1 | covered |
| Degraded state message | `#ret-degraded` | PW-WDG-016 | P0 | covered |
| Degraded message contains link to General page | `#ret-degraded a[href]` | PW-WDG-017 | P1 | covered |
| Compact micro summary | `#ret-compact` | PW-WDG-018 | P1 | covered |
| Compact rnsd icon | `#ret-compact-rnsd` | PW-WDG-019 | P1 | covered |
| Compact lxmd icon | `#ret-compact-lxmd` | PW-WDG-020 | P1 | covered |
| 15-second tick interval fires `_fetchAll` | tickTimeout | PW-WDG-021 | P1 | covered |

**Responsive breakpoints (`onWidgetResize`)**

| Breakpoint | Width | Visible elements | Hidden elements | Test ID | Priority | Coverage |
|---|---|---|---|---|---|---|
| Full | ≥ 400px | all rows, TX/RX col | compact | PW-WDG-030 | P0 | covered |
| Medium | 300–399px | all rows, no TX/RX | compact, `.ret-col-traffic` | PW-WDG-031 | P1 | covered |
| Narrow | 200–299px | health banner, detail, ifcount, traffic; no identity, no interface table | compact, `#ret-row-identity`, `#ret-iface-section` | PW-WDG-032 | P1 | covered |
| Micro | < 200px | compact icons only | everything else | PW-WDG-033 | P1 | covered |

**Degraded state interactions with breakpoints**

| Scenario | Test ID | Priority | Coverage |
|---|---|---|---|
| Degraded at ≥200px: degraded banner shown, iface section hidden | PW-WDG-040 | P0 | covered |
| Degraded at <200px (micro): degraded banner hidden (micro mode wins) | PW-WDG-041 | P1 | covered |
| Recovery from degraded: iface section re-shown respecting current breakpoint | PW-WDG-042 | P1 | covered |

**API call results**

| API endpoint called | DOM target updated | Success scenario | Failure/error scenario | Test ID | Priority | Coverage |
|---|---|---|---|---|---|---|
| `GET /api/reticulum/service/rnsdStatus` | `#ret-rnsd-status`, `#ret-compact-rnsd` | Running (green) | Stopped or error (red/amber) | PW-WDG-050 | P0 | covered |
| `GET /api/reticulum/service/lxmdStatus` | `#ret-lxmd-status`, `#ret-compact-lxmd` | Running (green) | Stopped or error | PW-WDG-051 | P0 | covered |
| `GET /api/reticulum/service/info` | `#ret-version`, `#ret-identity` | Versions + identity | "Unavailable" spans | PW-WDG-052 | P1 | covered |
| `GET /api/reticulum/service/rnstatus` | interface table, ifcount, traffic | Interface rows built | "No interface data available" | PW-WDG-053 | P0 | covered |

---

## 2. User Flow Coverage

### Flow 1 — First-Time Setup

> Enable rnsd → configure general settings → add first interface → apply

| Step | Actions | Test IDs | Priority |
|---|---|---|---|
| 1. Navigate to General | `goto /ui/reticulum/general` | PW-NAV-001 | P0 |
| 2. Check "Enable Reticulum Service" | click `#general\.enabled` | PW-GEN-020 | P0 |
| 3. Configure sharing ports | enter values in port fields | PW-GEN-041, PW-GEN-042 | P0 |
| 4. Save settings | click `#saveBtn` → verify `result: saved` | PW-GEN-070 | P0 |
| 5. Apply changes | click `#applyBtn` → verify success banner | PW-GEN-071, PW-GEN-072 | P0 |
| 6. Navigate to Interfaces | `goto /ui/reticulum/interfaces` | PW-NAV-002 | P0 |
| 7. Confirm empty state shown | `#grid-interfaces` has empty message | PW-IFC-016 | P1 |
| 8. Click Add Interface | click `#addInterfaceBtn` → modal opens | PW-IFC-001, PW-IFC-020 | P0 |
| 9. Fill name + select type | enter name, choose TCPServer | PW-IFC-032, PW-IFC-034 | P0 |
| 10. Fill network fields | enter listen port | PW-IFC-052 | P0 |
| 11. Save interface | submit modal → interface appears in grid | PW-IFC-021 | P0 |
| 12. Apply interface changes | click `#applyInterfacesBtn` | PW-IFC-002 | P0 |

### Flow 2 — Interface Management (All 12 Types)

For each interface type: TCPServer, TCPClient, Backbone, UDP, Auto, RNode, RNodeMulti, Serial, KISS, AX25, Pipe, I2P.

| Step | Actions | Test IDs | Priority |
|---|---|---|---|
| Add each type | select type → verify correct fields appear, wrong type fields hidden | PW-IFC-080–091 | P0 |
| Edit existing | click edit button → modal opens populated | PW-IFC-021 | P0 |
| Toggle enabled inline | click rowtoggle → fires `toggleInterface` API | PW-IFC-018 | P0 |
| Delete | click delete → confirm modal → record removed from grid | PW-IFC-140–143 | P0 |

### Flow 3 — LXMF Configuration with Dependency Handling

| Step | Actions | Test IDs | Priority |
|---|---|---|---|
| 1. Navigate to LXMF page with rnsd stopped | verify `#rnsd-warning` banner visible, Start/Restart disabled | PW-LXM-009, PW-LXM-008 | P0 |
| 2. Enable LXMF service | check `#lxmf\.enabled` | PW-LXM-030 | P0 |
| 3. Enable propagation node | check `#lxmf\.enable_node` → Costs and Peering tabs appear | PW-LXM-040, PW-LXM-026 | P0 |
| 4. Configure stamp costs | set target, tolerance → verify floor constraint | PW-LXM-060–062 | P0 |
| 5. Set sync size | enter max_message_size → enter sync_max_size < 40× → verify warning | PW-LXM-046–048 | P0 |
| 6. Configure static peering | check from_static_only, leave static_peers empty → verify warning | PW-LXM-073–075 | P0 |
| 7. Save and apply | PW-LXM-095, PW-LXM-096 | P0 |
| 8. Simulate rnsd starting | badge updates to Running, warning banner hides, Start button enabled | PW-LXM-010, PW-LXM-011, PW-LXM-008 | P0 |
| 9. Click lxmd Start | verify `lxmdStart` API called, badge updates | PW-LXM-003, PW-LXM-006 | P0 |
| 10. Click lxmd Stop | verify `lxmdStop` API called | PW-LXM-004 | P0 |
| 11. Click lxmd Restart with rnsd stopped | verify error result displayed | PW-LXM-008 | P0 |

### Flow 4 — Log Viewing and Filtering

| Step | Actions | Test IDs | Priority |
|---|---|---|---|
| 1. Navigate to logs | page loads, rnsd tab active, fetches `/rnsdLogs` | PW-LOG-001 | P0 |
| 2. Loading state shown | `#log-loading` visible during fetch | PW-LOG-030 | P1 |
| 3. Log lines rendered | `#log-output` visible | PW-LOG-033 | P0 |
| 4. Switch to lxmd tab | `shown.bs.tab` fires, fetches `/lxmdLogs` | PW-LOG-002, PW-LOG-003 | P0 |
| 5. Filter by severity | select level → lines re-filtered from cache, no new fetch | PW-LOG-010, PW-LOG-013 | P0 |
| 6. Filter by keyword | type in search → lines re-filtered | PW-LOG-011, PW-LOG-014 | P0 |
| 7. All lines filtered out | `#log-empty-filter` shown | PW-LOG-032 | P0 |
| 8. Change line count | select different value → new fetch | PW-LOG-012, PW-LOG-015 | P0 |
| 9. Click Refresh | explicit fetch | PW-LOG-020 | P0 |
| 10. Enable auto-refresh | check `#auto-refresh` → wait >5s → verify new fetch | PW-LOG-023, PW-LOG-024 | P1 |
| 11. Download filtered log | click `#download-logs` → file downloaded with correct name | PW-LOG-021, PW-LOG-040–042 | P1 |

### Flow 5 — Dashboard Monitoring

| Step | Actions | Test IDs | Priority |
|---|---|---|---|
| 1. Widget appears on dashboard | markup rendered | PW-WDG-001 | P0 |
| 2. Initial fetch: all 4 API calls fire | network intercept | PW-WDG-050–053 | P0 |
| 3. rnsd running: green icon, iface table populated | PW-WDG-002, PW-WDG-009 | P0 |
| 4. rnsd stopped: degraded state, banner shown | PW-WDG-016 | P0 |
| 5. Resize to < 200px | compact view only | PW-WDG-033 | P1 |
| 6. Resize to 300–399px | TX/RX column hidden | PW-WDG-031 | P1 |
| 7. Resize to ≥ 400px | full view | PW-WDG-030 | P0 |
| 8. 15s tick fires another fetch | PW-WDG-021 | P1 |

---

## 3. Validation Coverage

### 3.1 Client-Side Validations

| Validation | Trigger | Error element | Test ID | Priority |
|---|---|---|---|---|
| **Port conflict** — shared_instance_port equals instance_control_port | `input`/`change` on either port field | `#port-conflict-msg` | PW-GEN-043 | P0 |
| **Port conflict clears** — ports made different | update either field | `#port-conflict-msg:hidden` | PW-GEN-043 | P0 |
| **Port conflict: same on load** — if API returns identical values, error shows on load | page load | `#port-conflict-msg` | PW-GEN-043 | P1 |
| **Name uniqueness** — duplicate interface name in same session | enter existing name in modal | `#interface-name-conflict` | PW-IFC-033 | P0 |
| **Name uniqueness clears** — name changed to unique | edit name field | `#interface-name-conflict:hidden` | PW-IFC-033 | P0 |
| **Stamp floor** — stamp_cost_target minus stamp_cost_flexibility < 13 | `input`/`change` on either field | `#stamp-floor-warn` | PW-LXM-062 | P0 |
| **Stamp floor clears** — values adjusted to satisfy constraint | edit either field | `#stamp-floor-warn:hidden` | PW-LXM-062 | P0 |
| **Sync size** — propagation_sync_max_size < 40 × propagation_message_max_size | `input`/`change` on either field | `#sync-size-warn` with computed minimum | PW-LXM-048 | P0 |
| **Sync size clears** — sync size set to ≥ 40× | edit sync field | `#sync-size-warn:hidden` | PW-LXM-048 | P0 |
| **Static-only with empty peers** — from_static_only checked, static_peers empty | check `#lxmf\.from_static_only` with empty tokenizer | `#static-only-warn` | PW-LXM-075 | P0 |
| **Static-only clears** — peer added or checkbox unchecked | either action | `#static-only-warn:hidden` | PW-LXM-075 | P0 |
| **On-inbound security warning** — any value entered in on_inbound field | `input` event | `#on-inbound-warn` | PW-LXM-093 | P1 |
| **Identity hash tokenizer rejection** — invalid (non-32-hex) token entered | tokenizer for remote_management_allowed, static_peers, control_allowed, etc. | inline tokenizer error | PW-GEN-051-V, PW-LXM-074-V, PW-LXM-081-V | P1 |

### 3.2 Server-Side Validations (API returns `validations` key)

| Validation | Endpoint | Validation key | Test ID | Priority |
|---|---|---|---|---|
| Required field: interface name empty | `POST /rnsd/addInterface` | `interface.name` | PW-IFC-032-V | P0 |
| Required field: interface type empty | `POST /rnsd/addInterface` | `interface.type` | PW-IFC-034-V | P0 |
| Invalid port number (out of range) | `POST /rnsd/set` | `general.shared_instance_port` | PW-GEN-041-V | P1 |
| Invalid log level (out of range) | `POST /rnsd/set` | `general.loglevel` | PW-GEN-060-V | P2 |
| Invalid stamp cost range (target < 13) | `POST /lxmd/set` | `lxmf.stamp_cost_target` | PW-LXM-060-V | P1 |
| Logfile path outside allowed directory | `POST /lxmd/set` | `lxmf.logfile` | PW-LXM-091-V | P1 |
| Server validation error displayed in form | any `set` endpoint | `result.validations` object rendered in UI | PW-GEN-070-V | P0 |

> **Note:** Server-side validation display behavior depends on how `saveFormToEndpoint` (general page) and `setBase` (interfaces) surface the `validations` object back to the form. The exact DOM display mechanism (inline error spans vs. modal alert) should be confirmed against the OPNsense `formDialogPlugin` behavior during test implementation.

---

## 4. State Coverage

### 4.1 Service States

| State | Description | Pages affected | Test IDs | Priority |
|---|---|---|---|---|
| rnsd running | `GET /service/status` → `running` | General, Interfaces, LXMF, Widget | PW-GEN-003, PW-IFC-019, PW-LXM-001, PW-WDG-002 | P0 |
| rnsd stopped | `GET /service/status` → `stopped` | same | PW-GEN-003, PW-IFC-019, PW-LXM-009, PW-WDG-016 | P0 |
| lxmd running | `GET /service/lxmdStatus` → `running` | LXMF, Widget | PW-LXM-006, PW-WDG-003 | P0 |
| lxmd stopped | `GET /service/lxmdStatus` → `stopped` | LXMF, Widget | PW-LXM-006, PW-WDG-003 | P0 |
| lxmd running, rnsd stopped | unusual degraded state | LXMF, Widget | PW-LXM-010, PW-WDG-040 | P1 |
| Both services stopped | full degraded | all pages | PW-WDG-016, PW-LXM-009 | P0 |

### 4.2 Interface Count States

| State | Where visible | Test IDs | Priority |
|---|---|---|---|
| No interfaces configured (empty grid) | Interfaces grid, Widget | PW-IFC-016, PW-WDG-010 | P1 |
| Single interface, enabled, up | Interfaces grid, Widget | PW-IFC-010, PW-WDG-009 | P0 |
| Multiple interfaces, all up (count summary: green) | Widget ifcount | PW-WDG-005 | P0 |
| Multiple interfaces, some down (count summary: warning icon) | Widget ifcount | PW-WDG-015 | P1 |
| Many interfaces triggering pagination (>10 rows) | Interfaces grid | PW-IFC-017 | P1 |

### 4.3 Log States

| State | Selector | Test IDs | Priority |
|---|---|---|---|
| Loading (fetch in progress) | `#log-loading:visible` | PW-LOG-030 | P1 |
| No log entries (service never started / empty file) | `#log-empty-service:visible` | PW-LOG-031 | P0 |
| Entries exist but all filtered out | `#log-empty-filter:visible` | PW-LOG-032 | P0 |
| Entries exist and pass filter | `#log-output:visible` with text | PW-LOG-033 | P0 |

### 4.4 Propagation Node States

| State | Description | Test IDs | Priority |
|---|---|---|---|
| enable_node off | Costs/Peering tabs hidden, dep fields hidden | PW-LXM-027, PW-LXM-049 | P0 |
| enable_node on | Costs/Peering tabs visible, dep fields shown | PW-LXM-026, PW-LXM-050 | P0 |
| from_static_only on, static_peers empty | `#static-only-warn` visible | PW-LXM-075 | P0 |
| from_static_only on, static_peers populated | `#static-only-warn` hidden | PW-LXM-075 | P0 |

---

## 5. API Interaction Coverage

All endpoints called by the UI, grouped by controller.

### ServiceController (`/api/reticulum/service/`)

| Endpoint | Method | Called from | Test IDs |
|---|---|---|---|
| `GET /status` | GET | General, Interfaces (service bar via `updateServiceControlUI`) | PW-GEN-003, PW-IFC-019 |
| `POST /start` | POST | General, Interfaces (service bar start button) | PW-GEN-004, PW-IFC-019 |
| `POST /stop` | POST | General, Interfaces (service bar stop button) | PW-GEN-005, PW-IFC-019 |
| `POST /restart` | POST | General, Interfaces (service bar restart button) | PW-GEN-006, PW-IFC-019 |
| `GET /rnsdStatus` | GET | LXMF page (rnsd badge), Widget (_fetchAll) | PW-LXM-001, PW-WDG-050 |
| `POST /rnsdStart` | POST | (used by service bar duplicate path) | PW-GEN-004 |
| `POST /rnsdStop` | POST | (used by service bar duplicate path) | PW-GEN-005 |
| `POST /rnsdRestart` | POST | (used by service bar duplicate path) | PW-GEN-006 |
| `POST /lxmdStart` | POST | LXMF page (lxmd Start button) | PW-LXM-003 |
| `POST /lxmdStop` | POST | LXMF page (lxmd Stop button) | PW-LXM-004 |
| `POST /lxmdRestart` | POST | LXMF page (lxmd Restart button) | PW-LXM-005 |
| `GET /lxmdStatus` | GET | LXMF page (badge polling), Widget | PW-LXM-006, PW-WDG-051 |
| `POST /reconfigure` | POST | General Apply button, Interfaces Apply button, LXMF Apply button | PW-GEN-071, PW-IFC-002, PW-LXM-096 |
| `GET /rnstatus` | GET | Widget (_fetchAll interface table) | PW-WDG-053 |
| `GET /info` | GET | Widget (_fetchAll versions/identity) | PW-WDG-052 |
| `GET /rnsdInfo` | GET | General runtime info bar | PW-GEN-001 |
| `GET /lxmdInfo` | GET | (available but not currently called from UI volt files) | — |
| `GET /rnsdLogs?lines=N` | GET | Log viewer (rnsd tab, line count change, refresh) | PW-LOG-001, PW-LOG-015, PW-LOG-020 |
| `GET /lxmdLogs?lines=N` | GET | Log viewer (lxmd tab, line count change, refresh) | PW-LOG-002, PW-LOG-015, PW-LOG-020 |

### RnsdController (`/api/reticulum/rnsd/`)

| Endpoint | Method | Called from | Test IDs |
|---|---|---|---|
| `GET /get` | GET | General page (form population on load) | PW-GEN-070 (load side) |
| `POST /set` | POST | General page Save button | PW-GEN-070 |
| `GET /searchInterfaces` | GET | Interfaces grid (bootgrid on load, sort, page) | PW-IFC-010 |
| `GET /getInterface/{uuid}` | GET | Interfaces grid Edit button (modal population) | PW-IFC-021 |
| `POST /addInterface` | POST | Interfaces modal save (new record) | PW-IFC-020 |
| `POST /setInterface/{uuid}` | POST | Interfaces modal save (existing record) | PW-IFC-021 |
| `POST /delInterface/{uuid}` | POST | Delete confirmation modal confirm | PW-IFC-142 |
| `POST /toggleInterface/{uuid}` | POST | Inline enabled rowtoggle click | PW-IFC-018 |

### LxmdController (`/api/reticulum/lxmd/`)

| Endpoint | Method | Called from | Test IDs |
|---|---|---|---|
| `GET /get` | GET | LXMF page (form population on load) | PW-LXM-095 (load side) |
| `POST /set` | POST | LXMF page Save button | PW-LXM-095 |

---

## 6. Priority Summary

### By Page

| Page | P0 | P1 | P2 | Total |
|---|---|---|---|---|
| General Settings (PW-GEN-*) | 22 | 18 | 4 | **44** |
| Interfaces (PW-IFC-*) | 40 | 38 | 17 | **95** |
| Propagation Node (PW-LXM-*) | 28 | 32 | 5 | **65** |
| Log Viewer (PW-LOG-*) | 14 | 18 | 3 | **35** |
| Dashboard Widget (PW-WDG-*) | 17 | 22 | 5 | **44** |
| Navigation / Cross-page (PW-NAV-*) | 5 | 3 | 0 | **8** |
| **Total** | **126** | **131** | **34** | **291** |

> The counts above include individual element, flow step, validation, state, and API test IDs. Many IDs share a single Playwright `test()` block (e.g., a single "add TCPServer interface" test exercises PW-IFC-020, PW-IFC-032, PW-IFC-034, PW-IFC-051, PW-IFC-052, PW-IFC-080, PW-IFC-091). Expect approximately **80–100 distinct `test()` blocks** to cover all P0 and P1 IDs.

### P0 Coverage Priorities

The following P0 tests are the minimum set that must pass to consider the UI functionally complete for a release:

1. **PW-GEN-020, 070, 071** — enable service, save, apply
2. **PW-GEN-043** — port conflict validation
3. **PW-IFC-001, 020, 032, 034, 080–091** — add interface + type-visibility correctness
4. **PW-IFC-012, 018** — enable toggle in grid
5. **PW-IFC-140–142** — delete confirmation
6. **PW-LXM-003, 004, 008, 009** — lxmd service control + rnsd dependency enforcement
7. **PW-LXM-026, 027, 049, 050** — propagation node tab/field visibility
8. **PW-LXM-048, 062, 075** — all three cross-field validators
9. **PW-LOG-001–003, 031–033** — basic log fetch and empty states
10. **PW-WDG-002, 009, 016, 050–053** — widget service status and degraded state

### Known Coverage Gaps

| Gap | Affected IDs | Notes |
|---|---|---|
| Interface modal Advanced tab field inventory | PW-IFC-131 | `interfaces.volt` lines 800+ not read; ingress control field ID unconfirmed |
| `lxmdInfo` endpoint not called from any volt | — | Endpoint exists in ServiceController but no UI consumer found |
| Interface name uniqueness JS logic | PW-IFC-033 | `#interface-name-conflict` span exists in HTML; note in project memory says "logic not yet wired" — test should verify gap exists, not that it passes |
| RNodeMulti raw text area field ID | PW-IFC-124 | Described in requirements but field ID not confirmed from volt source |
