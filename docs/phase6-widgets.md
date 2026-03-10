# Phase 6 — Dashboard Widgets

## Overview
Two dashboard widgets display real-time Reticulum status on the OPNsense main dashboard. Built using OPNsense's JavaScript widget framework.

---

## Files

| File | Install Path | Purpose |
|------|-------------|---------|
| `Reticulum.js` | `/usr/local/opnsense/www/js/widgets/Reticulum.js` | Widget logic |
| `Metadata/Reticulum.xml` | `/usr/local/opnsense/www/js/widgets/Metadata/Reticulum.xml` | Widget registration |

Source paths: `src/opnsense/www/js/widgets/`

---

## 1. Metadata/Reticulum.xml — Widget Registration

```xml
<metadata>
    <widget>
        <id>Reticulum</id>
        <title>Reticulum</title>
        <filename>Reticulum.js</filename>
        <endpoints>
            <endpoint>api/reticulum/service/rnsdStatus</endpoint>
            <endpoint>api/reticulum/service/lxmdStatus</endpoint>
            <endpoint>api/reticulum/service/rnstatus</endpoint>
            <endpoint>api/reticulum/service/info</endpoint>
        </endpoints>
    </widget>
</metadata>
```

**Notes:**
- `<endpoints>` declares API dependencies — OPNsense's ACL system uses this to gate widget visibility
- Users without `page-services-reticulum-readonly` privilege won't see this widget option

---

## 2. Reticulum.js — Widget Implementation

### Class Structure Notes

OPNsense widgets extend `BaseTableWidget` (for widgets containing a data table) or `BaseWidget` (display-only). The Reticulum widget extends `BaseTableWidget` because it contains the interfaces table.

**Lifecycle methods:**
1. `getMarkup()` — returns initial HTML; called once during widget mount
2. `onMarkupRendered()` — DOM is ready; trigger first data fetch
3. `onWidgetTick()` — called on the polling interval (`this.tickTimeout`, in seconds)
4. `onWidgetResize(elem, width, height)` — called on container resize

**Key conventions applied:**

| Pattern | Wrong (old) | Correct |
|---|---|---|
| Status indicators | `<span class="label label-success">Running</span>` | `<i class="fa fa-circle text-success"></i> Running` |
| Key/value rows | `<table>` with two `<td>` cells | Bootstrap `.row` / `.col-xs-*` divs |
| Section headings | `<thead>` with colspan | `<div class="row"><div class="col-xs-12"><b>…</b></div></div>` |
| AJAX helper | `$.ajax()` | `ajaxCall(url, params, callback)` — handles CSRF globally |
| HTML escaping | Custom `escapeHtml()` | `this.htmlEncode()` from `BaseWidget` |
| Identity display | `style="font-family:monospace"` on `<span>` | `<code>` element |
| Error handling | Silent failure | `text-danger` message in affected section |
| Interface type | Table column | `title` attribute on `<tr>` (hover detail) |
| Interface traffic | Not shown | TX / RX column (formatted bytes) |

---

### Complete Widget

```javascript
/**
 * Reticulum Dashboard Widget
 *
 * Health banner: service status, interface count, aggregate traffic.
 * Detail section: versions, node identity.
 * Interface table: name, up/down status, per-interface TX/RX.
 *
 * Extends BaseTableWidget (OPNsense 24.x widget framework).
 */

import BaseTableWidget from "./BaseTableWidget.js";

export default class Reticulum extends BaseTableWidget {

    constructor() {
        super();
        this.tickTimeout = 15; // seconds between automatic refreshes
        this._isDegraded = false; // tracks rnsd stopped state for resize coordination
        this._lastWidth = 9999;   // tracks last known width for degraded-state coordination
    }

    getMarkup() {
        let $container = $('<div class="widget-content" id="reticulum-widget"></div>');

        // ── Health banner ───────────────────────────────────────────────────
        // Key/value pairs use Bootstrap grid rows — NOT a table.
        // Tables are reserved for the multi-row interfaces list only.
        $container.append(`
            <div class="row">
                <div class="col-xs-12"><b>Status</b></div>
            </div>
            <div class="row">
                <div class="col-xs-6 text-muted">Transport Node</div>
                <div class="col-xs-6" id="ret-rnsd-status">
                    <i class="fa fa-circle text-muted"></i> Loading&hellip;
                </div>
            </div>
            <div class="row" id="ret-row-lxmd">
                <div class="col-xs-6 text-muted">Propagation Node</div>
                <div class="col-xs-6" id="ret-lxmd-status">
                    <i class="fa fa-circle text-muted"></i> Loading&hellip;
                </div>
            </div>
            <div class="row" id="ret-row-ifcount">
                <div class="col-xs-6 text-muted">Interfaces</div>
                <div class="col-xs-6" id="ret-ifcount">&ndash;</div>
            </div>
            <div class="row" id="ret-row-traffic">
                <div class="col-xs-6 text-muted">Total TX / RX</div>
                <div class="col-xs-6" id="ret-traffic">&ndash;</div>
            </div>
        `);

        // ── Detail rows (lower priority; hidden when rnsd stopped) ──────────
        $container.append(`
            <div id="ret-detail-block">
                <div class="row" id="ret-row-version">
                    <div class="col-xs-6 text-muted">Versions</div>
                    <div class="col-xs-6" id="ret-version">&ndash;</div>
                </div>
                <div class="row" id="ret-row-identity">
                    <div class="col-xs-6 text-muted">Identity</div>
                    <div class="col-xs-6" id="ret-identity">&ndash;</div>
                </div>
            </div>
        `);

        // ── Compact summary (shown only below 200px) ────────────────────────
        $container.append(`
            <div id="ret-compact" style="display:none;">
                <span id="ret-compact-rnsd"><i class="fa fa-circle text-muted"></i> Transport</span>
                &nbsp;
                <span id="ret-compact-lxmd"><i class="fa fa-circle text-muted"></i> Propagation</span>
            </div>
        `);

        // ── Interface table ─────────────────────────────────────────────────
        // Table is appropriate here: homogeneous rows with aligned columns.
        // Type is demoted to a title attribute on each <tr> for hover access.
        $container.append(`
            <div id="ret-iface-section" style="margin-top:8px;">
                <div class="row">
                    <div class="col-xs-12"><b>Interfaces</b></div>
                </div>
                <div class="table-responsive">
                    <table class="table table-condensed" id="ret-iface-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th class="text-center">Status</th>
                                <th class="ret-col-traffic">TX / RX</th>
                            </tr>
                        </thead>
                        <tbody id="ret-iface-list">
                            <tr><td colspan="3" class="text-muted">Loading&hellip;</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `);

        // ── Degraded state message (hidden by default) ──────────────────────
        $container.append(`
            <div id="ret-degraded" style="display:none; margin-top:4px;" class="text-muted">
                rnsd is not running.<br>
                <a href="/ui/reticulum/general">Go to Services &rsaquo; Reticulum</a> to start it.
            </div>
        `);

        return $container;
    }

    onMarkupRendered() {
        this._fetchAll();
    }

    onWidgetTick() {
        this._fetchAll();
    }

    /**
     * Responsive layout.
     *
     * >= 400px  Full: all rows, all columns (Name / Status / TX/RX)
     * 300–399px Compact: TX/RX column hidden
     * 200–299px Narrow: Identity row + interface table hidden; health banner only
     * < 200px   Micro: compact icon summary only
     *
     * When rnsd is stopped (degraded), interface section / ifcount / traffic /
     * detail block stay hidden regardless of width — _applyDegradedState owns
     * those elements. This method only manages layout-driven visibility.
     */
    onWidgetResize(elem, width, height) {
        let $el = $(elem);
        this._lastWidth = width;

        if (width < 200) {
            // Micro: compact icons only — everything else hidden
            $el.find('#ret-detail-block, #ret-row-ifcount, #ret-row-traffic, #ret-iface-section, #ret-degraded').hide();
            $el.find('#ret-compact').show();

        } else if (width < 300) {
            // Narrow: health banner only
            $el.find('#ret-compact, #ret-row-identity, #ret-iface-section').hide();
            if (!this._isDegraded) {
                $el.find('#ret-detail-block, #ret-row-ifcount, #ret-row-traffic').show();
            }

        } else if (width < 400) {
            // Medium: hide TX/RX column, show everything else
            $el.find('#ret-compact').hide();
            if (!this._isDegraded) {
                $el.find('#ret-detail-block, #ret-row-ifcount, #ret-row-traffic, #ret-iface-section').show();
            }
            $el.find('#ret-row-identity').show();
            $el.find('.ret-col-traffic').hide();

        } else {
            // Full: show everything
            $el.find('#ret-compact').hide();
            if (!this._isDegraded) {
                $el.find('#ret-detail-block, #ret-row-ifcount, #ret-row-traffic, #ret-iface-section').show();
            }
            $el.find('#ret-row-identity').show();
            $el.find('.ret-col-traffic').show();
        }

        // Degraded banner shown at all widths >= 200 when degraded
        if (this._isDegraded && width >= 200) {
            $el.find('#ret-degraded').show();
        }
    }

    // ── Private methods ─────────────────────────────────────────────────────

    /**
     * Fire all four API calls in parallel. Each updates its own DOM region
     * independently so a slow or failing endpoint does not block others.
     * rnsd stopped state is coordinated after status is known.
     */
    _fetchAll() {
        let rnsdRunning = false;

        ajaxCall('/api/reticulum/service/rnsdStatus', {}, (data, status) => {
            rnsdRunning = (status === 'success' && data && data.status === 'running');
            this._setServiceStatus('#ret-rnsd-status', '#ret-compact-rnsd', rnsdRunning ? 'running' : (data && data.status || 'error'));
            this._applyDegradedState(!rnsdRunning);
        });

        ajaxCall('/api/reticulum/service/lxmdStatus', {}, (data, status) => {
            let s = (status === 'success' && data && data.status) ? data.status : 'error';
            this._setServiceStatus('#ret-lxmd-status', '#ret-compact-lxmd', s);
        });

        ajaxCall('/api/reticulum/service/info', {}, (data, status) => {
            if (status === 'success' && data) {
                this._updateInfo(data);
            } else {
                $('#ret-version').html('<span class="text-danger">Unavailable</span>');
                $('#ret-identity').html('<span class="text-danger">Unavailable</span>');
            }
        });

        ajaxCall('/api/reticulum/service/rnstatus', {}, (data, status) => {
            if (status === 'success' && data && !data.error) {
                this._updateInterfaces(data);
                this._updateTransportBadge(data);
            } else {
                $('#ret-iface-list').html('<tr><td colspan="3" class="text-muted">Service not running</td></tr>');
                $('#ret-ifcount').html('&ndash;');
                $('#ret-traffic').html('&ndash;');
            }
        });
    }

    /**
     * Show or hide the degraded state message and interface section.
     * When rnsd is stopped, suppress the interface table and detail rows
     * to avoid showing stale or meaningless data.
     *
     * Coordinates with onWidgetResize: stores degraded flag so resize
     * does not re-show elements that should stay hidden, and respects
     * the current width so recovery does not show elements outside
     * the active breakpoint.
     */
    _applyDegradedState(isDegraded) {
        this._isDegraded = isDegraded;

        if (isDegraded) {
            $('#ret-iface-section, #ret-row-ifcount, #ret-row-traffic, #ret-detail-block').hide();
            // Only show degraded banner when width allows (micro hides everything)
            if (this._lastWidth >= 200) {
                $('#ret-degraded').show();
            }
        } else {
            $('#ret-degraded').hide();
            // Re-show sections only when width breakpoint permits them
            if (this._lastWidth >= 200) {
                $('#ret-row-ifcount, #ret-row-traffic, #ret-detail-block').show();
            }
            if (this._lastWidth >= 300) {
                $('#ret-iface-section').show();
            }
        }
    }

    /**
     * Render a FA circle status icon into a detail row and the compact span.
     */
    _setServiceStatus(detailSel, compactSel, status) {
        let iconClass, label;
        switch (status) {
            case 'running':
                iconClass = 'text-success'; label = 'Running'; break;
            case 'stopped':
                iconClass = 'text-danger';  label = 'Stopped'; break;
            default:
                iconClass = 'text-warning'; label = 'Unknown';
        }
        let icon = `<i class="fa fa-circle ${iconClass}"></i>`;
        $(detailSel).html(`${icon} ${label}`);
        $(compactSel).find('i').attr('class', `fa fa-circle ${iconClass}`);
    }

    /**
     * Append "(Transport)" indicator to the Transport Node row when enabled.
     * Called after rnstatus data is received.
     */
    _updateTransportBadge(data) {
        let $el = $('#ret-rnsd-status');
        // Remove any existing badge before re-adding
        $el.find('.ret-transport-badge').remove();
        if (data.transport_enabled === true) {
            $el.append(' <small class="text-muted ret-transport-badge">(Transport)</small>');
        }
    }

    /**
     * Populate Versions and Identity rows from the info API response.
     * Shows both rns and lxmf versions when lxmf_version is present.
     * Truncates identity to 8 chars; full hash available on hover.
     */
    _updateInfo(data) {
        let rnsVer  = data.rns_version  ? this.htmlEncode(data.rns_version)  : '?';
        let lxmfVer = data.lxmf_version ? this.htmlEncode(data.lxmf_version) : null;

        let versionText = `rns ${rnsVer}`;
        if (lxmfVer) {
            versionText += ` / lxmf ${lxmfVer}`;
            // Ensure Propagation Node row is visible only when lxmf is installed
            $('#ret-row-lxmd').show();
        } else {
            $('#ret-row-lxmd').hide();
        }
        $('#ret-version').html(versionText);

        if (data.node_identity) {
            let full    = this.htmlEncode(data.node_identity);
            let preview = this.htmlEncode(data.node_identity.substring(0, 8));
            $('#ret-identity').html(`<code title="${full}">${preview}&hellip;</code>`);
        } else {
            $('#ret-identity').html('&ndash;');
        }
    }

    /**
     * Rebuild the interface table and health banner aggregates from rnstatus.
     *
     * - Counts up/down interfaces for the summary row.
     * - Sums tx_bytes/rx_bytes for aggregate traffic display.
     * - Renders per-row TX/RX using formatBytes().
     * - Interface type is set as a title attribute on <tr> for hover detail.
     * - ifac_netname is shown as secondary text under the interface name.
     */
    _updateInterfaces(data) {
        let $tbody = $('#ret-iface-list');
        $tbody.empty();

        let interfaces = data.interfaces || [];

        if (interfaces.length === 0) {
            $tbody.html('<tr><td colspan="3" class="text-muted">No interfaces configured</td></tr>');
            $('#ret-ifcount').html('0 configured');
            $('#ret-traffic').html('&ndash;');
            return;
        }

        let upCount  = 0;
        let totalTx  = 0;
        let totalRx  = 0;

        interfaces.forEach((iface) => {
            let isUp = iface.status === 'up';
            if (isUp) upCount++;

            let tx = iface.tx_bytes || 0;
            let rx = iface.rx_bytes || 0;
            totalTx += tx;
            totalRx += rx;

            let name = this.htmlEncode(iface.name || '—');
            // ifac_netname shown as secondary line under name when present
            let nameHtml = name;
            if (iface.ifac_netname) {
                nameHtml += `<br><small class="text-muted">${this.htmlEncode(iface.ifac_netname)}</small>`;
            }

            let statusIcon = isUp
                ? '<i class="fa fa-circle text-success"></i>'
                : '<i class="fa fa-circle text-danger"></i>';

            // TX/RX: muted when both are zero (uninformative regardless of status)
            let trafficClass = (tx === 0 && rx === 0) ? 'text-muted' : '';
            let trafficText  = `${this._formatBytes(tx)} / ${this._formatBytes(rx)}`;

            // Type stripped of "Interface" suffix, set as row hover title
            let shortType = (iface.type || '').replace(/Interface$/, '');

            $tbody.append(`
                <tr title="${this.htmlEncode(shortType)}">
                    <td>${nameHtml}</td>
                    <td class="text-center">${statusIcon}</td>
                    <td class="ret-col-traffic ${trafficClass}">${trafficText}</td>
                </tr>
            `);
        });

        // Interface count summary
        let countClass = upCount < interfaces.length ? 'text-warning' : '';
        let warning    = upCount < interfaces.length ? ' <i class="fa fa-exclamation-triangle text-warning"></i>' : '';
        $('#ret-ifcount').html(
            `<span class="${countClass}">${upCount} / ${interfaces.length} up</span>${warning}`
        );

        // Aggregate traffic
        $('#ret-traffic').html(
            `${this._formatBytes(totalTx)} / ${this._formatBytes(totalRx)}`
        );
    }

    /**
     * Format a byte count to a human-readable string.
     * @param {number} n  bytes
     * @returns {string}  e.g. "1.2 MB"
     */
    _formatBytes(n) {
        if (n >= 1073741824) return (n / 1073741824).toFixed(1) + ' GB';
        if (n >= 1048576)    return (n / 1048576).toFixed(1)    + ' MB';
        if (n >= 1024)       return (n / 1024).toFixed(1)       + ' KB';
        return n + ' B';
    }
}
```

---

## 3. Widget Display Behavior

### Normal State (all services running, all interfaces up)

```
┌─ Reticulum ──────────────────────────────────┐
│ Status                                        │
│ Transport Node    ● Running (Transport)       │
│ Propagation Node  ● Running                  │
│ Interfaces        3 / 3 up                   │
│ Total TX / RX     14.2 MB / 6.8 MB           │
│ Versions          rns 0.8.2 / lxmf 0.5.0    │
│ Identity          a1b2c3d4…                  │
│                                               │
│ Interfaces                                    │
│ Name              Status  TX / RX            │
│ My TCP Server       ●     8.1 MB / 3.2 MB    │
│ LoRa 915            ●     4.9 MB / 2.4 MB    │
│ Auto LAN            ●     1.2 MB / 1.2 MB    │
└───────────────────────────────────────────────┘
  ● = fa-circle text-success (green)
  (Transport) appears only when transport_enabled: true
```

### Degraded State (rnsd stopped)

```
┌─ Reticulum ──────────────────────────────────┐
│ Status                                        │
│ Transport Node    ● Stopped                  │
│ Propagation Node  ● Stopped                  │
│                                               │
│ rnsd is not running.                          │
│ Go to Services › Reticulum to start it.      │
└───────────────────────────────────────────────┘
  ● = fa-circle text-danger (red)
  Interface table, interface count, traffic, versions, and
  identity are all suppressed — no stale data shown.
```

### Partial-Degraded State (rnsd running, one interface down)

```
┌─ Reticulum ──────────────────────────────────┐
│ Status                                        │
│ Transport Node    ● Running (Transport)       │
│ Propagation Node  ● Running                  │
│ Interfaces        2 / 3 up  ⚠                │
│ Total TX / RX     9.3 MB / 4.4 MB            │
│ Versions          rns 0.8.2 / lxmf 0.5.0    │
│ Identity          a1b2c3d4…                  │
│                                               │
│ Interfaces                                    │
│ Name              Status  TX / RX            │
│ My TCP Server       ●     8.1 MB / 3.2 MB    │
│ LoRa 915            ●     0 B / 0 B          │  ← muted
│ Auto LAN            ●     1.2 MB / 1.2 MB    │
└───────────────────────────────────────────────┘
  ⚠ = fa-exclamation-triangle text-warning next to count
  "2 / 3 up" rendered in text-warning
  Down interface: red circle; 0 B / 0 B rendered muted (expected)
```

### No Interfaces Configured

```
┌─ Reticulum ──────────────────────────────────┐
│ Status                                        │
│ Transport Node    ● Running                  │
│ Propagation Node  ● Stopped                  │
│ Interfaces        0 configured               │
│                                               │
│ No interfaces configured.                     │
└───────────────────────────────────────────────┘
```

---

## 4. Responsive Behavior

| Widget Width | Layout | Hidden |
|-------------|--------|--------|
| ≥ 400px | Full: all health rows, interface table with Name / Status / TX/RX | Nothing |
| 300–399px | TX/RX column hidden; all other rows visible | `.ret-col-traffic` column |
| 200–299px | Health banner rows only (no interface table, no Identity) | Identity row, interface table section |
| < 200px | Micro: two compact icon spans only — Transport / Propagation | All detail rows, interface table |

**Breakpoint implementation:** `onWidgetResize` thresholds are 400, 300, and 200. The `< 200` micro state hides all detail and shows only `#ret-compact`, giving maximum information density at minimum size.

---

## 5. API Response Formats Expected

### rnsdStatus / lxmdStatus

```json
{"status": "running"}
```

`status` is `"running"` or `"stopped"`. Any other value or HTTP error → render `"Unknown"` with `text-warning` icon.

### info

```json
{
    "rns_version": "0.8.2",
    "lxmf_version": "0.5.0",
    "node_identity": "a1b2c3d4e5f67890abcdef1234567890"
}
```

- `lxmf_version` may be `null` or absent if lxmf is not installed — omit from Versions row and hide the Propagation Node status row entirely
- `node_identity` is a 32-character hex string (16 bytes) — truncate to 8 chars for display; full value in `title` attribute
- This endpoint may return data even when rnsd is stopped (reads from disk) — suppress Versions and Identity rows when rnsd status is `"stopped"`

### rnstatus

```json
{
    "transport_enabled": true,
    "identity": "a1b2c3d4e5f67890abcdef1234567890",
    "interfaces": [
        {
            "name": "My TCP Server",
            "type": "TCPServerInterface",
            "status": "up",
            "tx_bytes": 12345678,
            "rx_bytes": 67890123,
            "ifac_netname": "mynetwork"
        }
    ]
}
```

**Field handling:**

| Field | Handling |
|---|---|
| `transport_enabled` | When `true`, append `(Transport)` badge to Transport Node row. When `false`/absent, nothing — disabled transport is valid config. |
| `interfaces[].tx_bytes` / `rx_bytes` | Integer bytes, cumulative since daemon start. Format with `_formatBytes()`. Absent → treat as `0`. |
| `interfaces[].type` | Do NOT render as a column. Set as `title` on `<tr>` after stripping `"Interface"` suffix. |
| `interfaces[].ifac_netname` | When present and non-empty, render as `<small class="text-muted">` under interface name in Name cell. |
| `interfaces[].status` | `"up"` → green FA circle. Anything else → red FA circle. |
| Client-side aggregation | Sum `tx_bytes`/`rx_bytes` across all interfaces for Total TX/RX. Count `status === "up"` for interface count summary. |
| HTTP error / `data.error` | Treat as service not running — show muted message, hide interface table. |

---

## 6. Implementation Checklist

- [x] Create Metadata/Reticulum.xml with endpoint declarations
- [x] Create Reticulum.js extending BaseTableWidget
- [x] Implement `getMarkup()` — health banner, detail block, compact div, interface table, degraded message
- [x] Implement `_fetchAll()` with four parallel `ajaxCall()` invocations
- [x] Implement `_setServiceStatus()` using FA circle icons
- [x] Implement `_applyDegradedState()` to suppress stale data when rnsd stopped
- [x] Implement `_updateInfo()` — both versions, 8-char identity with hover
- [x] Implement `_updateInterfaces()` — count summary, aggregate TX/RX, per-row traffic, type as hover title, ifac_netname secondary text
- [x] Implement `_formatBytes()` helper (B / KB / MB / GB)
- [x] Implement `_updateTransportBadge()` — inline "(Transport)" indicator
- [x] Implement `onWidgetResize()` with breakpoints at 400 / 300 / 200px
- [x] Add both files to pkg-plist
- [x] Fix duplicate `style` attribute bug on `#ret-degraded` div (margin-top was silently dropped)
- [ ] Test widget appears in dashboard widget selection
- [ ] Test normal state: all green, interface count correct, TX/RX totals shown
- [ ] Test partial-degraded state: warning icon on count, down interface shows red circle
- [ ] Test degraded state: rnsd stopped suppresses interface table and detail rows, shows actionable link
- [ ] Test no-interfaces state: shows "0 configured" message
- [ ] Test lxmf absent: Propagation Node row hidden, version row shows rns only
- [ ] Test responsive layout at 400 / 300 / 200 / 150px
- [ ] Test 15-second auto-refresh
