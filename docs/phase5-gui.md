# Phase 5 — GUI Pages (Volt Templates)

## Overview
Four Volt templates provide the user-facing GUI. Each uses OPNsense's standard JavaScript helpers (`ajaxCall`, `saveFormToEndpoint`, `stdBootgridUI`, etc.) and Bootstrap 3 layout.

---

## Files

| Template | URL | Purpose |
|----------|-----|---------|
| `general.volt` | `/ui/reticulum/general` | Reticulum service (rnsd) settings + service controls |
| `lxmf.volt` | `/ui/reticulum/lxmf` | LXMF propagation node (lxmd) settings |
| `interfaces.volt` | `/ui/reticulum/interfaces` | Interface list (grid) + add/edit modal |
| `logs.volt` | `/ui/reticulum/logs` | Log viewer for both services |

All in: `src/opnsense/mvc/app/views/OPNsense/Reticulum/`

---

## 1. general.volt — General Settings Page

### Layout Structure

```
┌──────────────────────────────────────────────────────────┐
│ [service_status_container]  ← updateServiceControlUI()   │
│   renders: Reticulum [●] [Start] [Stop] [Restart]        │
│ Version: rns 0.8.x | Identity: abc123... [copy icon]     │
│   ↑ populated by separate ajaxCall to /api/.../rnsdInfo  │
├──────────────────────────────────────────────────────────┤
│ Tab: General | Transport | Sharing | Management | Logging │
├──────────────────────────────────────────────────────────┤
│ [General Tab]                                     │
│   ☑ Enable Reticulum Service                     │
│                                                   │
│ [Transport Tab]                                   │
│   ☑ Enable Transport Node                        │
│   ☑ Respond to Probes                            │
│   ☐ Stop Service on Interface Failure            │
│                                                   │
│ [Sharing Tab]                                     │
│   ☑ Allow Application Sharing                    │
│   Application Sharing Port: [37428]              │
│   Service Management Port: [37429]               │
│                                                   │
│ [Management Tab]                                  │
│   ☐ Enable Remote Management                     │
│   Authorized Administrators: [tag input]         │
│   Remote Management Key: [password field]        │
│                                                   │
│ [Logging Tab]                                     │
│   Log Level: [Info ▾]                            │
│   Log File: [/var/log/reticulum/rnsd.log]        │
├─────────────────────────────────────────────────┤
│                    [Save] [Apply Changes]         │
└─────────────────────────────────────────────────┘
```

### Key JavaScript Behavior

```javascript
// On page load
$(document).ready(function() {
    // Load settings
    ajaxCall('/api/reticulum/rnsd/get', {}, function(data, status) {
        mapDataToFormUI(data).done(function() {
            formatTokenizersUI();
            updateServiceControlUI('reticulum', 'rnsd');
            updateRnsdRuntimeInfo();
        });
    });

    // Refresh service status + runtime info every 10s
    setInterval(function() {
        updateServiceControlUI('reticulum', 'rnsd');
        updateRnsdRuntimeInfo();
    }, 10000);

    // Fetch version, identity hash, and uptime for the runtime info row
    // ServiceController::rnsdInfoAction() returns {version, identity, uptime}
    function updateRnsdRuntimeInfo() {
        ajaxCall('/api/reticulum/service/rnsdInfo', {}, function(data) {
            if (data.version) {
                $('#rnsd-version').text(data.version);
            }
            if (data.identity) {
                // Truncate to 16 chars + ellipsis; full hash in title tooltip
                $('#rnsd-identity').text(data.identity.substring(0, 16) + '...')
                    .attr('title', data.identity);
            }
            if (data.uptime) {
                $('#rnsd-uptime').text(data.uptime);
            }
        });
    }

    // Conditional visibility: share_instance controls port fields
    $('#general\\.share_instance').change(function() {
        $('.share_instance_dep').toggle($(this).is(':checked'));
    });

    // Save button
    $('#saveBtn').click(function() {
        saveFormToEndpoint('/api/reticulum/rnsd/set', 'general', function() {
            // success callback
        });
    });

    // Apply changes button — saves config then signals rnsd to reload
    // Note: a hard Restart is only available via the service status bar,
    // not from the form footer. Apply Changes performs a config reload
    // without a full daemon cycle where supported.
    $('#applyBtn').click(function() {
        ajaxCall('/api/reticulum/service/reconfigure', {}, function() {
            updateServiceControlUI('reticulum', 'rnsd');
        });
    });
});
```

### Service Status Bar Pattern

OPNsense provides `updateServiceControlUI('reticulum', 'rnsd')` which populates a
`<div id="service_status_container"></div>` placeholder with the colored status dot,
service label, and Start/Stop/Restart buttons. **Do not hand-write button HTML** —
the framework generates all button markup and wires click handlers internally.

Status dot CSS classes (applied by the framework):
- `.label-success` — Running (green)
- `.label-danger` — Stopped (red)
- `.label-warning` — Starting/stopping in progress (yellow)
- `.label-default` — Unknown/disabled (grey)

Button disabled states are managed automatically by `updateServiceControlUI`:
Start is disabled when running; Stop/Restart disabled when stopped; all disabled
during transitional states.

The runtime info row (version, identity, uptime) is **not** injected by
`updateServiceControlUI`. It requires a separate `ajaxCall` to
`/api/reticulum/service/rnsdInfo` (see JS block above). The identity hash is
truncated to 16 hex characters for display; the full 64-character hash is stored
in the element's `title` attribute for tooltip access.

---

## 2. interfaces.volt — Interface List & Editor

### Layout Structure

```
┌─────────────────────────────────────────────────┐
│ [service_status_container]  ← read-only rnsd dot │
├─────────────────────────────────────────────────┤
│ [+ Add Interface]                    [Apply]     │
├──────────┬──────────────────────────┬────────┬──────────┤
│ Name     │ Type                     │ Enabled│ Actions  │
├──────────┼──────────────────────────┼────────┼──────────┤
│ My TCP   │ TCP Server               │ ✓      │ [✏][🗑] │
│ LoRa 915 │ RNode LoRa Radio         │ ✓      │ [✏][🗑] │
│ Auto LAN │ Local Network (Auto)     │ ✓      │ [✏][🗑] │
└──────────┴──────────────────────────┴────────┴──────────┘
```

**Type column display names** — the grid Type column and the type dropdown must
display human-friendly names. The internal Python class name is used only in API
calls; it is never shown to the user:

| Internal value | Display name |
|---|---|
| `TCPServerInterface` | TCP Server (accepts connections) |
| `TCPClientInterface` | TCP Client (connects outbound) |
| `BackboneInterface` | TCP Backbone |
| `UDPInterface` | UDP |
| `AutoInterface` | Local Network (Auto-Discovery) |
| `RNodeInterface` | RNode LoRa Radio |
| `RNodeMultiInterface` | RNode LoRa Radio (Multi-Channel) |
| `SerialInterface` | Serial Port |
| `KISSInterface` | KISS TNC |
| `AX25KISSInterface` | AX.25 / KISS TNC |
| `PipeInterface` | Pipe / Command |
| `I2PInterface` | I2P Network |

**Empty state** — when no interfaces are configured, the grid must display:
> *"No interfaces configured. Click 'Add Interface' to create your first Reticulum interface."*

**Grid row action buttons** must use `btn-xs` (not `btn-sm`). Edit icon requires
`aria-label="Edit interface"`; delete icon requires `aria-label="Delete interface"`
plus a tooltip showing the interface name (e.g. "Delete: My TCP").

**Delete confirmation dialog** — the trash icon must show a confirmation dialog:
- Title: *"Delete Interface?"*
- Body: *"Are you sure you want to delete the interface '[Name]'? This cannot be undone."*
- Buttons: `[Delete Interface]` (`btn-danger`) + `[Cancel]`

### Grid Configuration (Bootgrid)

**Required HTML attributes:** The grid `<table>` element must carry
`data-editDialog="DialogInterface"` so `UIBootgrid` can find the modal on edit.
The modal `<div>` must have `id="DialogInterface"`.

```html
<table id="grid-interfaces" data-editDialog="DialogInterface" ...>
```
```html
<div id="DialogInterface" class="modal fade" ...>
```

```javascript
$(document).ready(function() {
    // Service status for rnsd (read-only indicator; no Start/Stop on this page)
    updateServiceControlUI('reticulum', 'rnsd');
    setInterval(function() {
        updateServiceControlUI('reticulum', 'rnsd');
    }, 10000);

    $('#grid-interfaces').UIBootgrid({
        search: '/api/reticulum/rnsd/searchInterfaces',
        get: '/api/reticulum/rnsd/getInterface/',
        set: '/api/reticulum/rnsd/setInterface/',
        add: '/api/reticulum/rnsd/addInterface/',
        del: '/api/reticulum/rnsd/delInterface/',
        toggle: '/api/reticulum/rnsd/toggleInterface/',
        options: {
            selection: false,
            multiSelect: false,
            rowCount: [10, 25, 50],
            formatters: {
                toggle: function(column, row) {
                    // Render enabled toggle
                },
                commands: function(column, row) {
                    // Render edit (btn-xs) and delete (btn-xs) buttons
                    // Edit: aria-label="Edit interface"
                    // Delete: aria-label="Delete interface", title="Delete: " + row.name
                }
            }
        }
    });

    // Apply button — signals rnsd to reload interface config from stored XML.
    // This is not a form save (there is no form); it only triggers reconfigure.
    $('#applyInterfacesBtn').click(function() {
        ajaxCall('/api/reticulum/service/reconfigure', {}, function() {
            updateServiceControlUI('reticulum', 'rnsd');
        });
    });
});
```

### Modal Dialog — Interface Editor

The modal contains tabbed sections. Field visibility changes based on the selected `type`.

**Tab structure** (consolidated to 4 tabs to avoid Bootstrap 3 `modal-lg` overflow
at common viewport widths — 7 horizontal tabs wrap at ≈1100px):

1. **Basic Settings** — name, type, enabled, mode, outgoing, IFAC/Security fields
   (network_name, passphrase, ifac_size)
2. **Network** — IP/port fields (TCP/UDP/Auto types)
3. **Radio / Serial** — port, speed, frequency, etc. (RNode/Serial/KISS/AX.25 types)
4. **Advanced** — announce_cap, bitrate, discoverable settings, rate control,
   ingress control (all ic_* fields), and sub_interfaces_raw textarea
   (RNodeMultiInterface only)

> **Note on modal form layout:** Fields inside the modal use Bootstrap 3
> `col-sm-4` for label columns and `col-sm-8` for input columns. Full-page
> forms (general.volt, lxmf.volt) use `col-sm-2` / `col-sm-10`.

### Type-Dependent Visibility Logic

```javascript
$('#interface\\.type').change(function() {
    var type = $(this).val();

    // Hide all type-specific sections
    $('.type-tcp, .type-udp, .type-auto, .type-rnode, .type-serial, .type-kiss, .type-ax25, .type-pipe, .type-i2p, .type-multi, .type-discover').hide();

    // Show relevant sections
    switch(type) {
        case 'TCPServerInterface':
        case 'BackboneInterface':
            $('.type-tcp, .type-discover').show();
            break;
        case 'TCPClientInterface':
            $('.type-tcp').show();
            break;
        case 'UDPInterface':
            $('.type-udp').show();
            break;
        case 'AutoInterface':
            $('.type-auto').show();
            break;
        case 'RNodeInterface':
            $('.type-rnode').show();
            break;
        case 'RNodeMultiInterface':
            $('.type-rnode, .type-multi').show();
            break;
        case 'SerialInterface':
            $('.type-serial').show();
            break;
        case 'KISSInterface':
            $('.type-kiss').show();
            break;
        case 'AX25KISSInterface':
            $('.type-ax25, .type-kiss').show();
            break;
        case 'PipeInterface':
            $('.type-pipe').show();
            break;
        case 'I2PInterface':
            $('.type-i2p').show();
            break;
    }
});
```

### Field Groups by CSS Class

| CSS Class | Fields | Shown For Types |
|-----------|--------|-----------------|
| `.type-tcp` | listen_ip, listen_port, target_host, target_port, prefer_ipv6, device, i2p_tunneled, kiss_framing, fixed_mtu | TCPServer, TCPClient, Backbone |
| `.type-udp` | listen_ip, listen_port, forward_ip, forward_port | UDP |
| `.type-auto` | group_id, discovery_scope, discovery_port, data_port, devices, ignored_devices, multicast_address_type | Auto |
| `.type-rnode` | port, frequency, bandwidth, txpower, spreadingfactor, codingrate, flow_control, airtime limits, id_callsign, id_interval | RNode, RNodeMulti |
| `.type-serial` | port, speed, databits, parity, stopbits, flow_control | Serial |
| `.type-kiss` | port, speed, parity, stopbits, flow_control, preamble, txtail, persistence, slottime, id_callsign, id_interval | KISS, AX25KISS |
| `.type-ax25` | callsign, ssid | AX25KISS |
| `.type-pipe` | command, respawn_delay | Pipe |
| `.type-i2p` | connectable, i2p_peers | I2P |
| `.type-multi` | sub_interfaces_raw textarea | RNodeMulti |
| `.type-discover` | discoverable, discovery_name, announce_interval, reachable_on, lat/lon/height, discovery_stamp_value, discovery_encrypt, publish_ifac | TCPServer, Backbone |

---

## 3. lxmf.volt — LXMF / Propagation Node Page

### Layout Structure

```
┌─────────────────────────────────────────────────┐
│ Reticulum: [service_status_container_rnsd]        │
│   ↑ read-only status dot for rnsd (dependency)   │
│ LXMF:      [service_status_container_lxmd]        │
│   ↑ full Start/Stop/Restart controls for lxmd     │
│ ⚠ Reticulum is not running — LXMF cannot start   │
│   (banner shown only when rnsd is stopped;        │
│    auto-hides when rnsd starts)                   │
├─────────────────────────────────────────────────┤
│ Tab: General | Propagation | Costs | Peering | ACL | Logging │
├─────────────────────────────────────────────────┤
│ [General Tab]                                     │
│   ☑ Enable LXMF Service                         │
│   Display Name: [My Node]                        │
│   ☑ Announce LXMF Identity at Startup           │
│   LXMF Announce Interval: [360] minutes          │
│   Max Delivery Size: [1000] KB                   │
│                                                   │
│ [Propagation Tab]                                 │
│   ☑ Enable Propagation Node ← prominent toggle   │
│     (Store & Forward Relay)                      │
│   Node Name: [My Propagation Node]               │
│   Propagation Announce Interval: [360] min       │
│   ☑ Announce Propagation Node at Startup        │
│   Storage Limit: [500] MB                        │
│   Max Message Size: [256] KB                     │
│   Max Sync Size: [10240] KB                      │
│                                                   │
│ [Costs Tab]                                       │
│   ─ Stamp costs are a lightweight proof-of-work  │
│     mechanism that discourages message spam.     │
│     Senders must perform a small calculation     │
│     whose difficulty is set here.                │
│   Anti-Spam Work Requirement: [16]               │
│   Anti-Spam Tolerance Range: [3]                 │
│   Peer Acceptance Difficulty: [18]               │
│   Maximum Acceptable Peer Difficulty: [26]       │
│                                                   │
│ [Peering Tab]                                     │
│   ☑ Auto-Peer                                    │
│   Auto-Peer Max Depth: [6]                       │
│   Max Peers: [20]                                │
│   ☐ Peer With Static List Only                  │
│   Static Peers: [tag input for hex hashes]       │
│                                                   │
│ [ACL Tab]                                         │
│   ☐ Require Authentication for Control           │
│   Permitted Message Sources: [tag input]         │
│   Blocked Destinations: [tag input]              │
│   Authorized Controllers: [tag input]            │
│   Priority Destinations: [tag input]             │
│                                                   │
│ [Logging Tab]                                     │
│   Log Level: [Info ▾]                            │
│   Run Script on Message Receipt: [path input]    │
├─────────────────────────────────────────────────┤
│                    [Save] [Apply Changes]         │
└─────────────────────────────────────────────────┘
```

### Key Behaviors

1. **rnsd dependency warning**: On page load and every 10s, check `/api/reticulum/service/rnsdStatus`.
   If stopped, show the `#rnsd-warning` alert banner. The banner auto-hides when rnsd starts.
   **Do not attempt to disable the lxmd Start button by ID** — the button is rendered by
   `updateServiceControlUI` and has no stable, addressable ID. Rely on the server-side guard
   (the API returns an error if lxmd is started without rnsd) and the alert banner for user
   feedback. The banner is dismissible only while rnsd remains stopped.

2. **Conditional visibility**: Propagation fields shown only when `enable_node` is checked.

3. **Warning for from_static_only + empty static_peers**: Show non-blocking alert.

4. **Hash tag inputs**: `CSVListField` renders as tokenizer/tag-input widgets. Each tag
   validated for 32-char hex format. Placeholder text: *"Paste a 32-character hex identity hash and press Enter"*.

```javascript
$(document).ready(function() {
    ajaxCall('/api/reticulum/lxmd/get', {}, function(data, status) {
        mapDataToFormUI(data).done(function() {
            formatTokenizersUI();
            // lxmd controls (full Start/Stop/Restart)
            updateServiceControlUI('reticulum', 'lxmd');
            // rnsd read-only status dot (dependency indicator)
            updateServiceControlUI('reticulum', 'rnsd');
            checkRnsdDependency();
        });
    });

    // Check rnsd status for dependency warning banner
    // Do NOT target individual buttons generated by updateServiceControlUI —
    // those have no stable IDs. Show/hide the warning banner only.
    function checkRnsdDependency() {
        ajaxCall('/api/reticulum/service/rnsdStatus', {}, function(data) {
            if (data.status !== 'running') {
                $('#rnsd-warning').show();
            } else {
                $('#rnsd-warning').hide();
            }
        });
    }

    // Propagation fields visibility
    $('#lxmf\\.enable_node').change(function() {
        $('.propagation-dep').toggle($(this).is(':checked'));
    });

    // Save button
    $('#saveBtn').click(function() {
        saveFormToEndpoint('/api/reticulum/lxmd/set', 'lxmf', function() {
            // success callback
        });
    });

    // Apply changes button — saves config then signals lxmd to reload
    $('#applyBtn').click(function() {
        ajaxCall('/api/reticulum/service/reconfigure', {}, function() {
            updateServiceControlUI('reticulum', 'lxmd');
            updateServiceControlUI('reticulum', 'rnsd');
        });
    });

    setInterval(function() {
        updateServiceControlUI('reticulum', 'lxmd');
        updateServiceControlUI('reticulum', 'rnsd');
        checkRnsdDependency();
    }, 10000);
});
```

---

## 4. logs.volt — Log Viewer

### Layout Structure

```
┌─────────────────────────────────────────────────┐
│ Tab: Reticulum Logs | LXMF Logs                  │
├─────────────────────────────────────────────────┤
│ Severity: [Info ▾]  Search: [______]  Max Lines: [200]│
│ [☐ Auto-refresh]                    [Download]   │
├─────────────────────────────────────────────────┤
│ 2026-03-06 12:00:01 [4] Interface started: TCP  │
│ 2026-03-06 12:00:02 [4] Transport node active   │
│ 2026-03-06 12:00:15 [5] Path request from abc...│
│ ...                                               │
│                                                   │
│ ← Empty state (no logs yet):                     │
│   "No log entries found. The service may not     │
│    have started yet, or the log file is empty."  │
│                                                   │
│ ← Empty state (filter returns nothing):          │
│   "No log lines match the current filter."       │
└─────────────────────────────────────────────────┘
```

> **logs.volt intentionally omits the service status bar.** It is a read-only viewer
> and performs no service control actions.

> **Download button implementation:** The Download button constructs a URL with a
> `download=1` query parameter: `window.location.href = '/api/reticulum/service/' +
> service + 'Logs?download=1&lines=' + lines`. The controller action detects this
> parameter and sets `Content-Disposition: attachment; filename="reticulum.log"` on
> the response. Alternatively, a JavaScript Blob may be used from the already-fetched
> log data — specify which approach during implementation.

### Implementation

```javascript
function loadLogs(service) {
    var lines = $('#log-lines').val() || 200;
    ajaxCall('/api/reticulum/service/' + service + 'Logs', {lines: lines}, function(data) {
        var filtered = filterByLevel(data.logs, $('#log-level').val());
        filtered = filterByKeyword(filtered, $('#log-search').val());
        $('#log-output').text(filtered.join('\n'));
        scrollToBottom();
    });
}

// Auto-refresh
var refreshInterval = null;
$('#auto-refresh').change(function() {
    if ($(this).is(':checked')) {
        refreshInterval = setInterval(function() {
            loadLogs($('.log-tab.active').data('service'));
        }, 5000);
    } else {
        clearInterval(refreshInterval);
    }
});
```

**Note:** The log viewer requires an additional configd action to tail log files. Add to `actions_reticulum.conf`:

```ini
[logs.rnsd]
command:tail -n %s /var/log/reticulum/rnsd.log
type:script_output
message:Fetching rnsd logs
parameters:%s

[logs.lxmd]
command:tail -n %s /var/log/reticulum/lxmd.log
type:script_output
message:Fetching lxmd logs
parameters:%s
```

And add corresponding ServiceController endpoints:
```php
public function rnsdLogsAction()
{
    $lines = $this->request->get('lines', 'int', 200);
    $lines = min(max($lines, 10), 500);
    $backend = new Backend();
    $result = trim($backend->configdRun("reticulum logs.rnsd", [$lines]));
    return ['logs' => explode("\n", $result)];
}
```

---

## 5. Common UI Patterns

### Service Status Bar

The standard OPNsense pattern uses a single empty placeholder div. **Do not
hand-write button HTML** — `updateServiceControlUI()` generates all content:

```html
<!-- Single service (general.volt) -->
<div class="content-box">
    <div id="service_status_container"></div>
</div>

<!-- Two services (lxmf.volt): suffixed container IDs for each -->
<div class="content-box">
    <div class="row">
        <div class="col-sm-1"><strong>Reticulum:</strong></div>
        <div class="col-sm-11" id="service_status_container_rnsd"></div>
    </div>
    <div class="row">
        <div class="col-sm-1"><strong>LXMF:</strong></div>
        <div class="col-sm-11" id="service_status_container_lxmd"></div>
    </div>
</div>
```

Below the status container, a separate runtime info row is populated by
`ajaxCall('/api/reticulum/service/rnsdInfo', ...)`:

```html
<div id="rnsd-runtime-info">
    Version: <span id="rnsd-version"></span> |
    Identity: <span id="rnsd-identity" title=""></span> |
    Uptime: <span id="rnsd-uptime"></span>
</div>
```

Identity hash display: truncate to 16 hex chars + ellipsis; full 64-char hash
in `title` attribute (tooltip). Optionally add a copy-to-clipboard icon.

**Stop button class:** The framework renders Stop as `btn-danger` (red). Do not
override to `btn-warning`.

### Form Save + Apply Pattern

Standard OPNsense two-step: Save persists to config.xml, Apply triggers reconfigure.
A Restart button is intentionally absent from the form footer — hard service restarts
are only available via the service status bar. Apply Changes performs a config reload
without a full daemon cycle where the service supports it.

```html
<button class="btn btn-primary" id="saveBtn">
    <i class="fa fa-save"></i> Save
</button>
<button class="btn btn-default" id="applyBtn">
    <i class="fa fa-check"></i> Apply Changes
</button>
```

After a successful Apply, show a brief inline notification:
*"Changes applied. Service restarting…"* (use a Bootstrap `alert-info` div that
auto-dismisses after 3 seconds).

### Form Layout Column Widths

| Context | Label column | Input column |
|---|---|---|
| Full-page forms (general.volt, lxmf.volt) | `col-sm-2` | `col-sm-10` |
| Modal dialog (interfaces.volt editor) | `col-sm-4` | `col-sm-8` |

### Tag Input for Hex Hashes
CSVListField renders as tokenizer widget. OPNsense's `formatTokenizersUI()` handles this.
Placeholder text for all hash tag inputs: *"Paste a 32-character hex identity hash and press Enter"*.
When a tag is rejected (not 32-char hex), show inline: *"'[value]' is not a valid identity hash.
Must be exactly 32 hex characters."*

### Dropdown Display Values

Use human-readable display labels in all `<select>` elements; send the internal value in API calls:

**`interface.mode`**

| Display label | Internal value |
|---|---|
| Full Router | `full` |
| Gateway | `gateway` |
| Access Point | `access_point` |
| Roaming Client | `roaming` |
| Boundary Node | `boundary` |

**`general.loglevel` / `lxmf.loglevel`**

| Display label | Internal value |
|---|---|
| Critical | `0` |
| Error | `1` |
| Warning | `2` |
| Notice | `3` |
| Info (default) | `4` |
| Debug | `5` |
| Extreme | `6` |
| Trace | `7` |

**`interface.multicast_address_type`**

| Display label | Internal value |
|---|---|
| Temporary (recommended) | `temporary` |
| Fixed | `permanent` |

**`interface.discovery_scope`**

| Display label | Internal value |
|---|---|
| Local Link (default) | `link` |
| Admin | `admin` |
| Site | `site` |
| Organization | `organisation` |
| Global | `global` |

---

## 6. Implementation Checklist

- [ ] Create general.volt with tabs, service bar, conditional visibility
- [ ] Create interfaces.volt with bootgrid + modal dialog
- [ ] Implement type-dependent field visibility in interfaces modal
- [ ] Create lxmf.volt with tabs, rnsd dependency warning, propagation toggle
- [ ] Create logs.volt with dual-tab viewer, filters, auto-refresh
- [ ] Add log configd actions and ServiceController log endpoints
- [ ] Implement `ServiceController::rnsdInfoAction()` returning `{version, identity, uptime}`
- [ ] Implement `ServiceController::lxmdInfoAction()` returning `{version, identity, uptime}`
- [ ] Wire `updateRnsdRuntimeInfo()` / `updateLxmdRuntimeInfo()` on both page load and polling interval
- [ ] Add type display-name mapping for interface type dropdown and grid Type column
- [ ] Add `data-editDialog="DialogInterface"` to grid table; `id="DialogInterface"` to modal div
- [ ] Add `$(document).ready` block with `updateServiceControlUI` + `setInterval` to interfaces.volt
- [ ] Add Apply button handler to interfaces.volt (calls reconfigure, not a form save)
- [ ] Add rnsd read-only status container to lxmf.volt (second `updateServiceControlUI` call)
- [ ] Add delete confirmation dialog to interface grid delete action
- [ ] Add empty-state messages to interface grid and log viewer
- [ ] Implement log Download button (controller `download=1` param or JS Blob)
- [ ] Add loading/spinner states for page load, log fetch, and service control buttons
- [ ] Add post-Apply success notification ("Changes applied. Service restarting…")
- [ ] Test all pages load without JavaScript errors
- [ ] Test form save/load cycle on each page
- [ ] Test conditional visibility (share_instance, enable_node, type selector)
- [ ] Test interface CRUD through the grid
- [ ] Test log viewer displays content from both services
- [ ] Test rnsd dependency warning shows/hides correctly on lxmf.volt
- [ ] Add all .volt files to pkg-plist

---

## 7. Help Text Reference

### 7.1 OPNsense Help Text Implementation Pattern

OPNsense renders help text via a clickable info icon (`fa-info-circle`) that toggles a hidden `<div>`. The pattern is:

```html
<!-- Help icon — rendered once per field row -->
<a id="help_for_general.enable_transport" href="#" class="showhelp">
    <i class="fa fa-info-circle"></i>
</a>

<!-- Hidden help text — placed below/after the field row -->
<div class="hidden" data-for="help_for_general.enable_transport">
    <small>Enable the rnsd transport node functionality. When enabled, this instance
    actively participates in path discovery and packet routing for the Reticulum
    network — i.e. it relays packets on behalf of other nodes.</small>
</div>
```

The JavaScript toggle is provided by OPNsense core:
```javascript
$(document).on('click', 'a.showhelp', function(e) {
    e.preventDefault();
    $('div[data-for="' + $(this).attr('id') + '"]').toggleClass('hidden');
});
```

**Naming convention:** `help_for_<section>.<fieldname>` — e.g. `help_for_general.shared_instance_port`, `help_for_interface.frequency`.

Help text may also be placed in the XML model `<help>` tag and the optional `<hint>` tag for short format/validation guidance. These are rendered automatically when using OPNsense's `base_form` partial.

---

### 7.2 general.volt — Reticulum Service Settings Help Text

#### General Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `general.enabled` | Enable Reticulum Service | Enable the Reticulum Network Stack daemon (rnsd). When disabled, all Reticulum interfaces and transport functionality are stopped. This must be enabled before any interfaces or the LXMF propagation node can function. |

#### Transport Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `general.enable_transport` | Enable Transport Node | When enabled, this device acts as a mesh router — relaying packets and participating in path discovery for the Reticulum network. Without this, the node only handles traffic for applications running locally. |
| `general.respond_to_probes` | Respond to Probes | When enabled, rnsd replies to diagnostic probe packets from other nodes. Useful for network troubleshooting and reachability testing, but disabled by default for privacy (probes can reveal node existence). |
| `general.panic_on_interface_error` | Stop Service on Interface Failure | When enabled, the Reticulum service stops if any configured interface encounters a fatal error. Recommended only for debugging — in production, leave this disabled so the service continues operating on surviving interfaces even if one fails (e.g. a disconnected serial radio). |

#### Sharing Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `general.share_instance` | Allow Application Sharing | Allow multiple applications on this machine (e.g. Nomad, Sideband) to share a single Reticulum connection via a local socket rather than each running their own instance. Almost always leave this enabled. Disable only if you need strict isolation between applications. |
| `general.shared_instance_port` | Application Sharing Port | TCP port used for inter-process communication between local applications and the shared Reticulum instance. Default: 37428. Must be unique — cannot match the Service Management Port. |
| `general.instance_control_port` | Service Management Port | TCP port for the Reticulum service management API. Default: 37429. Must be unique — cannot match the Application Sharing Port. Rarely needs changing unless another service conflicts. |

#### Management Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `general.enable_remote_management` | Enable Remote Management | Enable the remote management interface, allowing authorised administrators to manage this Reticulum node over the network. Requires at least one entry in Authorized Administrators. Disabled by default — only enable if you need remote administration. |
| `general.remote_management_allowed` | Authorized Administrators | Reticulum identity hashes of trusted administrators permitted to remotely manage this node. Each entry is a 32-character hexadecimal string identifying a Reticulum identity. Leave empty to allow no remote management even if the feature is enabled. |
| `general.rpc_key` | Remote Management Key | Authentication key for the remote management interface. Enter a hex string (up to 128 characters). Leave blank to auto-generate a key on next startup. **For security, the current value is never displayed. Enter a new value only if you want to change it; leave blank to keep the existing key.** Store this key securely — it controls administrative access to the node. |

#### Logging Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `general.loglevel` | Log Level | Controls how much detail the Reticulum service writes to the log file. Higher levels produce more output and are useful for debugging. Select from: Critical, Error, Warning, Notice, Info (recommended), Debug, Extreme, Trace. |
| `general.logfile` | Log File | Absolute path to the Reticulum log file. Default: `/var/log/reticulum/rnsd.log`. The reticulum service user must have write access to this path. Changing this requires a service restart. |

---

### 7.3 interfaces.volt — Interface Editor Help Text

#### Common Fields (All Interface Types)

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.enabled` | Enabled | Enable or disable this interface. Disabled interfaces are stored in configuration but not loaded by rnsd. Use this to temporarily take an interface offline without deleting its configuration. |
| `interface.name` | Name | A unique human-readable name for this interface. Used in log output and status displays. Allowed characters: letters, numbers, spaces, hyphens, underscores. Max 64 characters. Each interface must have a distinct name — duplicates will cause rnsd to reject the configuration. |
| `interface.type` | Type | The interface type determines the physical or logical transport medium used. Select the type that matches your hardware or connection method. The form will show only the fields relevant to the selected type. See the Type Reference below for a description of each type. |
| `interface.mode` | Mode | Controls how this interface participates in the Reticulum network. Select from the dropdown: **Full Router** — standard bidirectional relay (default for most interfaces); **Gateway** — accepts and forwards routes from external networks; **Access Point** — accepts connections from client/roaming nodes; **Roaming Client** — portable endpoint, minimises announcements; **Boundary Node** — edge node, limits routing scope. |
| `interface.outgoing` | Allow Outbound Packets | Allow the Reticulum service to send packets out through this interface. Uncheck to make this interface receive-only (it will still receive and process inbound packets but will not transmit). Useful for monitoring interfaces or one-way links. |
| `interface.network_name` | Network Segment Name | Network isolation group name (IFAC — Interface Addressing & Configuration). Interfaces across different nodes that share the same Network Segment Name and passphrase form a single isolated logical network. Leave blank if this interface should participate in the global Reticulum network. Must be alphanumeric. |
| `interface.passphrase` | Network Segment Passphrase | Passphrase used together with the Network Segment Name to derive cryptographic keying material for network isolation. All interfaces in the same segment must share the same name and passphrase. **Write-only — never returned by the API. Leave blank to keep the existing passphrase.** Leave blank if not using network isolation. |
| `interface.ifac_size` | Authentication Tag Size (bytes) | Size in bytes of the authentication tag appended to each packet for network isolation. Larger values (up to 512) provide stronger authentication but add overhead; smaller values (minimum 8) reduce overhead. Leave blank for automatic sizing based on interface bitrate. |
| `interface.bootstrap_only` | Bootstrap Only | When enabled, this interface is only used during initial route discovery (bootstrapping) and is not used for ongoing packet forwarding. Applies to: TCPServerInterface, BackboneInterface. Use when you have a dedicated bootstrap/seed node connection that should not carry data traffic. |
| `interface.announce_cap` | Max Announcements per Minute | Maximum number of route announcements per minute that the Reticulum service will emit on this interface. Range: 1–100. Reducing this value throttles outbound announcements — useful on slow or congested links (e.g. LoRa radio). Default is determined by the service based on interface type. |
| `interface.bitrate` | Bitrate | The physical or effective bitrate of this interface in bits per second (e.g. 1200 for a 1.2 kbps LoRa link, 1000000 for a 1 Mbps link). Used by rnsd to calculate routing costs and tune announce rates. Leave blank for automatic detection (works for most IP-based interfaces; required for serial/radio interfaces). |

#### Network Tab — TCP/IP Fields

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.listen_ip` | Listen IP | Local IP address to bind the listening socket to. Use `0.0.0.0` to accept connections on all network interfaces (recommended for most setups), or enter a specific IP to restrict to one interface (e.g. `192.168.1.1` for LAN-only). Applies to: TCPServerInterface, BackboneInterface. |
| `interface.listen_port` | Listen Port | TCP port number to listen on for incoming connections. Default: 4242. Ensure this port is reachable through your firewall if you want remote nodes to connect. Applies to: TCPServerInterface, BackboneInterface, UDPInterface. |
| `interface.target_host` | Target Host | Hostname or IP address of the remote Reticulum node to connect to. Accepts DNS names (e.g. `node.example.com`) or IP addresses. rnsd will automatically reconnect if the connection is lost. Applies to: TCPClientInterface. |
| `interface.target_port` | Target Port | TCP port of the remote node to connect to. Must match the Listen Port configured on the remote TCPServerInterface or BackboneInterface. Default: 4242. Applies to: TCPClientInterface. |
| `interface.prefer_ipv6` | Prefer IPv6 | When the target hostname resolves to both IPv4 and IPv6 addresses, prefer the IPv6 address. Useful on dual-stack networks when you want to ensure IPv6 paths are used. |
| `interface.device` | Restrict to Network Adapter | Name of the local network adapter to bind to (e.g. `em0`, `vtnet0`, `re0`). Leave blank to let the OS choose based on routing. Only needed if you have multiple network interfaces and want to pin this Reticulum interface to a specific adapter. |
| `interface.i2p_tunneled` | I2P Tunneled | Route this TCP interface through an I2P tunnel rather than directly over the internet. Requires a running I2P router on this host. Provides anonymity at the cost of higher latency. |
| `interface.kiss_framing` | KISS Framing | Use KISS (Keep It Simple Stupid) protocol framing instead of raw TCP. Enable this only when connecting to a legacy TNC (Terminal Node Controller) or radio device that requires KISS framing over a TCP connection. |
| `interface.fixed_mtu` | Fixed MTU | Override the Maximum Transmission Unit for this interface (bytes). Leave blank for automatic MTU discovery (recommended). Only set this if you experience fragmentation issues or are connecting to a device with a known fixed MTU. |
| `interface.forward_ip` | Forward IP | For UDPInterface: the destination IP address to forward UDP packets to. Leave blank if the same as Listen IP. Applies to: UDPInterface only. |
| `interface.forward_port` | Forward Port | For UDPInterface: the destination UDP port to forward packets to. Leave blank if the same as Listen Port. Applies to: UDPInterface only. |

#### Serial/Radio Tab — RNode Fields

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.port` | Serial Port | The serial device path for the connected radio or TNC hardware. On FreeBSD (OPNsense): `/dev/cuaU0`, `/dev/cuaU1`, etc. for USB serial devices. Use `ls /dev/cua*` to list available ports. The reticulum service user must be in the `dialer` group to access serial ports. |
| `interface.frequency` | Frequency (Hz) | Radio frequency in Hz for the RNode LoRa transceiver. Example: `915000000` for 915 MHz (Americas), `868000000` for 868 MHz (Europe), `433000000` for 433 MHz. Ensure you are licensed for the frequency and power level in your jurisdiction. Applies to: RNodeInterface, RNodeMultiInterface. |
| `interface.bandwidth` | Bandwidth (Hz) | LoRa signal bandwidth in Hz. Common values: `125000` (125 kHz, standard), `250000` (250 kHz, faster/shorter range), `500000` (500 kHz, fastest/shortest range), `62500` (62.5 kHz, slower/longer range). Narrower bandwidth = longer range but slower data rate. Applies to: RNodeInterface, RNodeMultiInterface. |
| `interface.txpower` | TX Power (dBm) | Transmit power in dBm. Range: 0–22 dBm. Higher power increases range but also power consumption, heat, and regulatory compliance requirements. Use the minimum power necessary to maintain reliable links. Ensure compliance with local radio regulations. Applies to: RNodeInterface, RNodeMultiInterface. |
| `interface.spreadingfactor` | Spreading Factor | LoRa spreading factor (SF7–SF12). Higher SF = longer range and better sensitivity, but much slower data rate. SF7 = fastest (lowest range); SF12 = slowest (greatest range). SF9 or SF10 is a common balance point for medium-range links. All nodes on a channel must use the same SF. |
| `interface.codingrate` | Coding Rate | LoRa error correction coding rate (5–8, representing 4/5 to 4/8). Higher values add more redundancy and improve reliability in noisy environments at the cost of throughput. CR5 (4/5) is most common; use CR8 (4/8) in very poor RF conditions. All nodes must match. |
| `interface.airtime_limit_long` | Daily Airtime Limit (%) | Maximum percentage of time this interface may transmit over a 24-hour rolling window (0–100). Example: `10` limits transmission to 10% of the day. Required by radio regulations in some regions (e.g. EU 868 MHz: 1%). Leave blank for no limit. |
| `interface.airtime_limit_short` | 10-Minute Airtime Limit (%) | Maximum percentage of time this interface may transmit over any 10-minute rolling window (0–100). Use in conjunction with the daily limit for regulatory compliance. Leave blank for no limit. |
| `interface.id_callsign` | ID Callsign | Amateur radio callsign to transmit for station identification (e.g. `W5XYZ`). Required by law in many jurisdictions when operating amateur radio equipment. If set, rnsd will periodically transmit an identification packet. Format: ITU callsign, optionally with SSID suffix (e.g. `W5XYZ-1`). |
| `interface.id_interval` | ID Interval (seconds) | How often (in seconds) to transmit the station identification callsign. Default: 600 (every 10 minutes). The interval must satisfy local regulatory requirements (e.g. FCC Part 97 requires ID every 10 minutes). Applies when ID Callsign is set. |

#### Serial/Radio Tab — Serial/KISS Fields

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.speed` | Baud Rate | Serial port baud rate. Must match the baud rate configured on the connected device. Common values: 9600, 19200, 38400, 57600, 115200, 230400. For RNodes: the USB-serial baud rate (the radio parameters are set separately via frequency/bandwidth/SF). |
| `interface.databits` | Data Bits | Number of data bits per character. Typically 8. Rarely needs changing unless the device specifies otherwise. Range: 5–8. |
| `interface.parity` | Parity | Serial parity check setting. Options: `none` (most common), `even`, `odd`. Must match the device. Virtually all modern devices use `none`. |
| `interface.stopbits` | Stop Bits | Number of stop bits per character. Typically 1. Use 2 only if the device specification requires it. |
| `interface.flow_control` | Flow Control | Enable RTS/CTS hardware flow control. Required for some serial devices to prevent buffer overruns. Most USB-serial adapters work without hardware flow control; enable only if the device documentation specifies it. |
| `interface.preamble` | Preamble (ms) | KISS TNC preamble duration in milliseconds — the time the TNC keys up the transmitter before sending data. Increasing this gives the radio's PA time to stabilise. Adjust based on your TNC/radio combination; leave blank for driver default. |
| `interface.txtail` | TX Tail (ms) | KISS TNC TX tail duration in milliseconds — how long the TNC keeps transmitting after the last byte, allowing the signal to fully clear. Increase if the last few bytes of packets are being lost. Leave blank for driver default. |
| `interface.persistence` | Persistence | KISS CSMA persistence value (0–255). Controls how aggressively the TNC attempts to transmit when the channel is clear. Higher = more aggressive (more collisions on busy channels); lower = more conservative (more delay). Leave blank for driver default. |
| `interface.slottime` | Slot Time (ms) | KISS CSMA slot time in milliseconds — the interval used in the random backoff algorithm before retrying transmission. Adjust for busy channels to reduce collisions. Leave blank for driver default. |

#### Serial/Radio Tab — AX.25 Fields

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.callsign` | Callsign | Your amateur radio callsign for this AX.25 interface (e.g. `W5XYZ`). Mandatory for AX.25KISSInterface — AX.25 protocol requires a valid callsign as the source address for all frames. Include SSID if needed (e.g. `W5XYZ-9`). |
| `interface.ssid` | SSID | Secondary Station ID (0–15) for this AX.25 station. Used to distinguish multiple stations operating under the same callsign. SSID 0 is the default/primary station. Choose any unused SSID if running multiple Reticulum interfaces under the same callsign. |

#### Network Tab — AutoInterface Fields

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.group_id` | Network Group Name | Auto-discovery group identifier. Interfaces across different nodes that share the same Group ID form a single logical Reticulum network via IPv6 multicast. Leave blank to use the default group (all AutoInterfaces on the local network). Use a custom alphanumeric string to create a private subnet isolated from other AutoInterface nodes. |
| `interface.devices` | Devices | Comma-separated list of OS network interface names to use for multicast discovery (e.g. `em0,wlan0`). Leave blank to automatically use all eligible interfaces. Use this to restrict AutoInterface to specific network adapters. |
| `interface.ignored_devices` | Ignored Devices | Comma-separated list of OS network interface names to exclude from AutoInterface discovery (e.g. `docker0,lo0,tap0`). Useful to prevent Reticulum from using virtual, loopback, or container interfaces. Supports wildcard patterns. |
| `interface.multicast_address_type` | Multicast Address Type | IPv6 multicast address type used for discovery: **temporary** (default) — uses a dynamically generated IPv6 address compatible with most networks; **permanent** — uses a fixed IPv6 address. Use `temporary` unless you have a specific reason to use a fixed address. |
| `interface.discovery_scope` | Discovery Scope | IPv6 multicast scope for neighbour discovery: **link** (default) — discovery is limited to the local network segment (same subnet); **admin**, **site**, **organisation**, **global** — progressively wider scopes. Use `link` for LAN discovery. Wider scopes require proper IPv6 routing and may not work without special configuration. |
| `interface.discovery_port` | Discovery Port | UDP port used for multicast discovery announcements. Default: 29716. All nodes on the same AutoInterface group must use the same discovery port. Only change this if you have a port conflict. |
| `interface.data_port` | Data Port | UDP port used for actual Reticulum data packets. Default: 42671. All nodes on the same AutoInterface group must use the same data port. Only change this if you have a port conflict. |

#### I2P Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.connectable` | Accept Inbound Connections | When enabled, this node creates an inbound I2P tunnel so other nodes can reach it directly through the I2P network. When disabled, this node only makes outbound connections to other I2P nodes listed below (client-only mode). Requires an I2P router running on this host. |
| `interface.i2p_peers` | I2P Peers | Comma-separated list of I2P peer addresses (b32.i2p format) to connect to. These are the I2P addresses of other Reticulum nodes running I2PInterface. Example: `abc123...xyz.b32.i2p`. Leave blank if this node only listens for incoming I2P connections. |

#### Pipe Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.command` | Command | The shell command to execute for this pipe interface. rnsd will communicate with the command's stdin/stdout as a Reticulum data channel. Example: `/usr/bin/nc 10.0.0.1 4242` (netcat tunnel) or `/usr/local/bin/ssh -T user@host reticulum-pipe`. The command must be a full absolute path. |
| `interface.respawn_delay` | Respawn Delay (seconds) | How many seconds to wait before restarting the command if it exits unexpectedly. Minimum: 1. Default: 5. Increase this if the command is prone to rapid restart loops (e.g. when a remote host is temporarily unreachable). |

#### Discoverable Settings Tab (TCPServer/Backbone only)

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.discoverable` | Advertise This Node | Broadcast this node's connection information (address, port) so other Reticulum nodes can automatically discover and connect to it. Applies to: TCP Server, TCP Backbone. |
| `interface.discovery_name` | Node Display Name | A human-friendly name for this node shown to others during discovery (e.g. `"Region 5 Gateway"`, `"Office Backbone"`). Not required to be unique, but should be descriptive enough to identify the node. |
| `interface.announce_interval` | Announce Interval (minutes) | How often (in minutes) to broadcast the discovery announcement. Minimum: 5 minutes. Example: 60 = announce every hour. Shorter intervals help nodes reconnect faster after a restart but increase network traffic. |
| `interface.reachable_on` | Reachable On | Network address or hostname where this interface can be reached by connecting nodes. If left blank, rnsd attempts to auto-detect the address. Useful when behind NAT or with multiple IPs — specify the public/routable address here (e.g. `203.0.113.10` or `mynode.dyndns.org`). |
| `interface.latitude` | Latitude | Geographic latitude of this node in decimal degrees (e.g. `37.7749` for San Francisco). Optional — used for geographic display in compatible Reticulum applications. Leave blank if location is not relevant or should not be disclosed. |
| `interface.longitude` | Longitude | Geographic longitude of this node in decimal degrees (e.g. `-122.4194` for San Francisco). Optional — used for geographic display in compatible Reticulum applications. Leave blank if location is not relevant or should not be disclosed. |
| `interface.height` | Height (m) | Altitude of this node above sea level in metres. Optional metadata for geographic systems. Leave blank if not needed. |
| `interface.discovery_stamp_value` | Discovery Stamp Cost | Proof-of-work cost value attached to discovery announcements from this interface. Leave blank to use the default. Higher values make it more expensive for nodes to announce on this interface, discouraging announcement spam. |
| `interface.discovery_encrypt` | Encrypt Discovery Announcements | Encrypt discovery announcements broadcast by this interface. When enabled, only nodes that know the network passphrase can process discovery announcements. Requires IFAC (network_name/passphrase) to be configured on this interface. |
| `interface.publish_ifac` | Publish IFAC Information | Publish interface access configuration (IFAC — network segment name and authentication parameters) in discovery announcements. Allows connecting nodes to automatically configure IFAC settings. Only enable on trusted networks. |

#### Announce/Discovery Tab — Rate Control

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.announce_rate_target` | Forwarded Announces Limit (per minute) | Maximum announces per minute forwarded through this interface. Leave blank for no rate limiting. Setting this helps protect slow or congested interfaces (e.g. LoRa) from being overwhelmed by announcement traffic from higher-speed interfaces. |
| `interface.announce_rate_grace` | Rate Limit Warm-Up Period (seconds) | Number of seconds during which the announce rate limit is not enforced after startup or after a quiet period. Allows an initial burst of announces before the rate cap kicks in. Leave blank for no warm-up period. |
| `interface.announce_rate_penalty` | Excess Rate Slowdown (seconds) | Additional delay (in seconds) applied per announce when the rate limit is exceeded, progressively slowing down announcement bursts. Leave blank for no additional slowdown beyond the basic rate limit. |

#### Ingress Control Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.ingress_control` | Enable Announcement Flood Protection | Enable the ingress control system for this interface. This limits the rate of incoming route announcements to protect against announcement floods (a form of denial-of-service). All fields below are only active when this is enabled. |
| `interface.ic_new_time` | New Source Classification Window (seconds) | Time window in seconds used to classify a source as "new" (not recently seen). Announcements from new sources are subject to tighter rate limits. |
| `interface.ic_burst_freq_new` | Max Burst Rate — New Sources (per window) | Maximum number of announces per time window accepted from new (previously unseen) sources. New sources are treated more strictly to prevent address-space flooding attacks. |
| `interface.ic_burst_freq` | Max Burst Rate — Known Sources (per window) | Maximum number of announces per time window accepted from known (previously seen) sources. Known sources are trusted slightly more than new ones. |
| `interface.ic_max_held_announces` | Queue Size During Suppression | Maximum number of announces to queue while suppressing a burst. Announces beyond this limit are dropped. |
| `interface.ic_burst_hold` | Burst Hold Time (seconds) | How long (in seconds) to suppress announces after a burst limit is exceeded. During this period, further announces from the offending source are queued up to the queue size limit. |
| `interface.ic_burst_penalty` | Repeat Violation Backoff Multiplier | Multiplier applied to the hold time for repeated burst violations. Higher values impose increasingly long suppression periods on persistent offenders. |
| `interface.ic_held_release_interval` | Queue Drain Interval (seconds) | Interval in seconds at which queued announces are gradually released after the suppression period ends. Prevents a large backlog from being released all at once. |

#### Raw Config Tab (RNodeMultiInterface only)

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `interface.sub_interfaces_raw` | Channel Definitions | Plain text configuration block for RNode LoRa Radio (Multi-Channel) sub-interfaces. Each sub-interface is defined with triple-bracket `[[[name]]]` syntax and its own `frequency`, `bandwidth`, `txpower`, `spreadingfactor`, and `codingrate` values. This field is required for RNodeMultiInterface and cannot be expressed as structured form fields due to its nested structure. Example:<br><br>`[[[Channel A]]]`<br>`frequency = 915000000`<br>`bandwidth = 125000`<br>`txpower = 17`<br>`spreadingfactor = 9`<br>`codingrate = 5`<br><br>`[[[Channel B]]]`<br>`frequency = 868000000`<br>`bandwidth = 250000`<br>`txpower = 14`<br>`spreadingfactor = 7`<br>`codingrate = 5`<br><br>⚠️ **Security note:** This field is emitted verbatim into the rnsd configuration file. Do not paste untrusted content. Only users with full admin access (`page-services-reticulum` privilege) can save this field. |

---

### 7.4 lxmf.volt — LXMF Service Settings Help Text

> **Page header note:** Add a one-sentence intro at the top of the lxmf.volt page:
> *"LXMF (Lightweight Extensible Message Format) is the messaging layer that runs
> over Reticulum. The Reticulum service (rnsd) must be running before LXMF can start."*

#### General Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `lxmf.enabled` | Enable LXMF Service | Enable the LXMF (Lightweight Extensible Message Format) service (lxmd). **Requires the Reticulum service (rnsd) to be running** — the LXMF service will fail to start if Reticulum is not active. Use this to turn this OPNsense device into a message relay and store-and-forward node for the LXMF messaging network. |
| `lxmf.display_name` | Display Name | Human-readable name for this LXMF node as it appears to other peers and messaging clients (e.g. `"My Home Node"`, `"Region 5 Relay"`). Max 128 characters. Default: `Anonymous Peer`. |
| `lxmf.lxmf_announce_at_start` | Announce LXMF Identity at Startup | Broadcast this node's LXMF identity to the network immediately when the LXMF service starts. Useful for quickly making this node visible to peers after a restart. If disabled, the node waits until the next scheduled announce interval. |
| `lxmf.lxmf_announce_interval` | LXMF Announce Interval (minutes) | How often this node announces its LXMF identity to the network, in minutes. Leave blank to disable periodic announcements (the node will only announce at startup if "Announce LXMF Identity at Startup" is enabled). Maximum: 44640 minutes (31 days). |
| `lxmf.delivery_transfer_max_size` | Max Delivery Size (KB) | Maximum size in kilobytes of an incoming LXMF message that this node will accept for direct delivery. Messages larger than this limit are rejected. Default: 1000 KB. Reduce this to conserve resources on limited systems. |

#### Propagation Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `lxmf.enable_node` | Enable Propagation Node | Enable store-and-forward message propagation. When enabled, this node stores messages destined for offline recipients and forwards them when those recipients reconnect — making this a full LXMF propagation node. All fields in the Propagation, Costs, and Peering tabs are only active when this is enabled. |
| `lxmf.node_name` | Node Name | Human-friendly name for this propagation node, shown to other propagation nodes during peering (e.g. `"Pacific Northwest Relay"`, `"Office Propagation Node"`). Max 128 characters. Leave blank to use the Display Name. |
| `lxmf.announce_interval` | Propagation Announce Interval (minutes) | How often (in minutes) this propagation node announces its availability to other nodes. Default: 360 (every 6 hours). Shorter intervals help new nodes discover this propagation node faster, but increase network traffic. Maximum: 44640 minutes (31 days). |
| `lxmf.announce_at_start` | Announce Propagation Node at Startup | Broadcast this propagation node's identity immediately when the LXMF service starts. Recommended — ensures the node is quickly visible to peers after restarts. Note: this is distinct from "Announce LXMF Identity at Startup" on the General tab, which announces the LXMF identity rather than the propagation node role. |
| `lxmf.message_storage_limit` | Storage Limit (MB) | Maximum disk space in megabytes allocated for storing messages awaiting delivery. Default: 500 MB. When this limit is reached, the oldest messages are deleted to make room. Set this based on available disk space; minimum is approximately 0.005 MB (5 KB). |
| `lxmf.propagation_message_max_size` | Max Message Size (KB) | Maximum size in kilobytes of a single message accepted into the propagation queue. Messages larger than this are rejected. Default: 256 KB. Note: the sync packet size (`Max Sync Size`) is constrained to 40× this value. |
| `lxmf.propagation_sync_max_size` | Max Sync Size (KB) | Maximum size in kilobytes of a sync packet exchanged with peer propagation nodes. Default: 10240 KB (10 MB). This is the maximum amount of message data transferred in a single peer sync operation. Should be at least 40× the Max Message Size. |

#### Costs Tab

> **Section intro text** (display above these fields): *"Stamp costs are a lightweight
> proof-of-work mechanism that discourages message spam. Senders must perform a small
> calculation whose difficulty is set here. Higher values require more computational
> work from senders before their messages are accepted."*

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `lxmf.stamp_cost_target` | Anti-Spam Work Requirement | Target computational difficulty required from message senders. Default: 16. Higher values require more work from senders, reducing spam but also increasing send time for legitimate users. Range: 13–64. The accepted range is `target ± tolerance`. **Constraint**: `target − tolerance` must be at least 13 (the accepted floor cannot drop below the minimum valid stamp cost). |
| `lxmf.stamp_cost_flexibility` | Anti-Spam Tolerance Range | Tolerance around the work requirement. Default: 3. Stamps with a cost between `target − tolerance` and `target + tolerance` are accepted. Example: target=16, tolerance=3 accepts stamps costing 13–19. Range: 0–16. **Constraint**: `target − tolerance` must be at least 13 (i.e., flexibility cannot exceed `target − 13`). |
| `lxmf.peering_cost` | Peer Acceptance Difficulty | Computational difficulty required for other nodes to establish peering with this node. Default: 18. Higher values reduce the risk of peer flooding by low-resource or malicious nodes. Range: 13–64. |
| `lxmf.remote_peering_cost_max` | Maximum Acceptable Peer Difficulty | Maximum difficulty value this node will accept from remote peers. Default: 26. Peers advertising a difficulty higher than this are rejected. Set to 1 to accept all peers regardless of their advertised difficulty. Range: 1–64. |

#### Peering Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `lxmf.autopeer` | Auto-Peer | Automatically discover and establish peering with other LXMF propagation nodes found on the network, up to the configured maximum depth. When disabled, this node only peers with entries in the Static Peers list. Recommended: enabled for most deployments. |
| `lxmf.autopeer_maxdepth` | Auto-Peer Max Depth (hops) | Maximum number of Reticulum hops away from this node to search for and accept automatic peers. Default: 6. Lower values (e.g. 1–3) restrict peering to nearby nodes; higher values build a larger peer mesh but increase sync traffic. Range: 1–128. |
| `lxmf.max_peers` | Max Peers | Maximum number of active propagation peers this node maintains simultaneously. Default: 20. Increase for high-capacity nodes or large networks; decrease to reduce sync overhead on resource-constrained systems. Range: 1–1000. |
| `lxmf.from_static_only` | Peer With Static List Only | When enabled, this node only peers with nodes explicitly listed in the Static Peers field. Auto-peering is disabled regardless of the Auto-Peer setting. Use this for controlled, manually-managed peer meshes. **Warning**: if enabled with an empty Static Peers list, this node will have no peers and will not sync messages. |
| `lxmf.static_peers` | Static Peers | Comma-separated list of Reticulum identity hashes (32 hex characters each) for propagation nodes to statically peer with. These peers are always attempted regardless of the Auto-Peer setting. Use this to ensure peering with specific trusted nodes even in auto-peer mode. Example: `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4` |

#### ACL Tab

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `lxmf.auth_required` | Require Authentication for Control | Require cryptographic authentication for management and control operations on this propagation node. When enabled, only identities in the "Authorized Controllers" list can issue control commands. Recommended for publicly accessible propagation nodes. |
| `lxmf.control_allowed` | Authorized Controllers | Identity hashes (32 hex characters each) of nodes permitted to issue control commands to this propagation node (e.g. requesting sync, querying status). Leave blank to allow no remote control (operations can still be performed locally). |
| `lxmf.allowed_identities` | Permitted Message Sources | Identity hashes (32 hex characters each) of nodes permitted to submit messages to this propagation node. **Leave blank to allow all sources** (open propagation node — recommended for community nodes). Populate this list to create a private, invitation-only propagation node. |
| `lxmf.ignored_destinations` | Blocked Destinations | Destination hashes (32 hex characters each) whose messages this node will refuse to store or forward. Use this to block known spam sources. Messages addressed to blocked destinations are silently dropped. |
| `lxmf.prioritise_destinations` | Priority Destinations | Destination hashes (32 hex characters each) that receive priority handling in the propagation queue. Messages for these destinations are delivered before lower-priority traffic. Use for critical services or users that must receive messages promptly. |

#### Logging Tab (lxmf.volt)

| Field ID | Label | Help Text |
|----------|-------|-----------|
| `lxmf.loglevel` | Log Level | Controls how much detail the LXMF service writes to the log file. Select from: Critical, Error, Warning, Notice, Info (recommended), Debug, Extreme, Trace. Higher levels produce significantly more output. |
| `lxmf.logfile` | Log File | Absolute path to the LXMF service log file. Default: `/var/log/reticulum/lxmd.log`. The reticulum service user must have write access to this path. |
| `lxmf.on_inbound` | Run Script on Message Receipt | Absolute path to a script or executable to run when the LXMF service receives an inbound message (e.g. `/usr/local/bin/notify.sh`). The script receives message metadata as arguments. Leave blank to disable. Useful for custom notification or integration workflows. |

---

### 7.5 logs.volt Help Text

| UI Element | Help Text |
|------------|-----------|
| Severity filter | Filter displayed log lines to show only entries at or above the selected severity. Levels: Critical, Error, Warning, Notice, Info, Debug, Extreme, Trace. Lower levels show more detail. |
| Search filter | Show only log lines containing the entered text. Case-insensitive substring match. Useful for filtering by interface name, identity hash, or error message. |
| Max Lines | Number of most recent log lines to fetch from the log file (10–500). Increase to see more history; decrease for faster load on large log files. |
| Auto-refresh | When checked, the log view automatically refreshes every 5 seconds. Useful for monitoring live service activity. Uncheck to freeze the view for inspection. |
| Download | Download the currently displayed (filtered) log content as a text file. |

---

### 7.6 Cross-Field Validation Messages

All validation messages appear **inline below the relevant field** using a
`<span class="text-danger small">` element, unless noted otherwise. Non-blocking
warnings use `text-warning`. The rnsd dependency message is a full-width
Bootstrap `alert-warning` banner.

| Constraint | Affected Fields | Display Location | Message to Display |
|-----------|----------------|------------------|--------------------|
| Port conflict | `shared_instance_port` / `instance_control_port` | Below the second (conflicting) port field | "Application Sharing Port and Service Management Port must be different." |
| Stamp cost floor | `stamp_cost_target` − `stamp_cost_flexibility` < 13 | Below the Anti-Spam Tolerance Range field | "Tolerance Range is too large. Work Requirement minus Tolerance must be at least 13 (current floor: [target − flexibility])." |
| Sync size constraint | `propagation_sync_max_size` < 40 × `propagation_message_max_size` | Below the Max Sync Size field | "Max Sync Size should be at least 40× the Max Message Size (currently: [calculated minimum] KB)." |
| Interface name uniqueness | `interface.name` | Below the Name field in the modal | "Interface name must be unique. This name is already used by another interface." |
| Static-only with empty peers | `from_static_only=1` + `static_peers` empty | Below the Static Peers tag input (non-blocking) | "Warning: 'Peer With Static List Only' is enabled but no Static Peers are configured. This node will have no propagation peers." |
| rnsd dependency | lxmd page loaded, rnsd stopped | Full-width `alert-warning` banner above the tab bar on lxmf.volt | "Reticulum is not running. The LXMF service requires Reticulum to be active. Start the Reticulum service first." The banner auto-hides when rnsd is detected as running (on the next 10s poll). It is not manually dismissible while rnsd remains stopped. |
| Write-only field reminder | `rpc_key`, `passphrase` | Placeholder text inside the input | "Enter new value to change (current value not shown)" |
| Invalid hex hash tag | Any tag-input field accepting identity hashes | Below the tag input, on tag rejection | "'[entered value]' is not a valid identity hash. Must be exactly 32 hex characters." |
