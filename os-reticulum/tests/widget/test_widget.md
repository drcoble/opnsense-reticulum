# Widget Manual Test Checklist — W-601 to W-606

These are manual browser tests that verify the Reticulum dashboard widget
(`src/opnsense/www/js/widgets/Reticulum.js`) behaves correctly in the
OPNsense web UI.  Run these tests on a real OPNsense installation (or VM)
with the `os-reticulum` package installed.

**Prerequisites**
- `os-reticulum` package installed and menu items visible
- At least one TCPServerInterface configured and rnsd able to start
- Browser DevTools available (F12)

---

## W-601: Widget appears in the Add Widget panel

**Test ID:** W-601
**Category:** Widget discovery

**Steps:**
1. Log in to OPNsense and navigate to the Dashboard (Lobby > Dashboard).
2. Click the "Add Widget" button (or the "+" icon in the widget bar).
3. Scroll through the list of available widgets.

**Expected behaviour:**
- "Reticulum" (or "Reticulum Status") appears as a selectable widget entry.
- The description or subtitle references the Reticulum / LXMF service.

**Pass criteria:** [ ] Widget listed in Add Widget panel

**Notes:** ____________________________________________________________

---

## W-602: Widget shows correct service status when services are running

**Test ID:** W-602
**Category:** Status display

**Steps:**
1. Ensure rnsd is running (start from Services > Reticulum > General or via CLI).
2. Optionally start lxmd as well.
3. Add the Reticulum widget to the Dashboard if not already present.
4. Wait up to 15 seconds for the first data fetch.

**Expected behaviour:**
- The widget's health banner shows a green "Running" (or equivalent) state.
- rnsd status row reads "Running".
- lxmd status row reads "Running" if lxmd is started, otherwise "Stopped".
- No red error banners.
- No JavaScript errors in the browser console (F12 > Console).

**Pass criteria:** [ ] rnsd status correct   [ ] lxmd status correct   [ ] No JS errors

**Notes:** ____________________________________________________________

---

## W-603: Widget shows interface table with TX/RX rates

**Test ID:** W-603
**Category:** Interface data display

**Steps:**
1. Ensure rnsd is running with at least one interface configured.
2. With the widget on the Dashboard, wait for the 15-second auto-refresh tick.
3. Observe the interface table section of the widget.

**Expected behaviour:**
- A table row appears for each active interface.
- Columns include at minimum: Interface Name, Type.
- At normal viewport width (>400 px) TX and RX rate columns are visible.
- Values update on each 15-second tick (or show "0 b/s" / "—" if no traffic).
- No "undefined" or empty cells where a value is expected.

**Pass criteria:** [ ] Interface rows present   [ ] TX/RX columns visible at normal width

**Notes:** ____________________________________________________________

---

## W-604: Widget shows graceful degraded state when rnsd is stopped

**Test ID:** W-604
**Category:** Error / degraded handling

**Steps:**
1. Stop rnsd (Services > Reticulum > General > Stop, or `service rnsd stop`).
2. Wait up to 15 seconds for the widget's next auto-refresh tick.
3. Observe the widget appearance.

**Expected behaviour:**
- The widget transitions to a degraded state.
- A degraded/warning banner or message is displayed (e.g. "rnsd not running"
  or the `#ret-degraded` element becomes visible with an appropriate message).
- The interface table either hides or shows an empty/placeholder state.
- No JavaScript exceptions are thrown (check F12 > Console).
- The widget does NOT crash or display a blank white box.

**Pass criteria:** [ ] Degraded state visible   [ ] No JS errors   [ ] Widget still renders

**Notes:** ____________________________________________________________

---

## W-605: Widget auto-refreshes every 15 seconds

**Test ID:** W-605
**Category:** Auto-refresh behaviour

**Steps:**
1. Ensure rnsd is running.
2. With the widget visible on the Dashboard, open F12 > Network tab and filter
   by `api/reticulum`.
3. Watch for a minimum of 35 seconds.

**Expected behaviour:**
- Four API calls are made on each refresh tick (matching the 4 endpoints
  declared in `Reticulum.xml`: rnsdStatus, lxmdStatus, rnstatus, and
  lxmdStatus or equivalent).
- Calls repeat approximately every 15 seconds (the widget's `tickTimeout`).
- Data displayed in the widget updates to reflect any changes in service state.

**Pass criteria:** [ ] API calls observed at ~15 s intervals   [ ] Data updates in widget

**Notes:** ____________________________________________________________

---

## W-606: Widget is responsive — columns collapse at narrow widths

**Test ID:** W-606
**Category:** Responsive layout

**Steps:**
1. Ensure rnsd is running with at least one interface so the interface table
   is populated.
2. Use browser DevTools Device Toolbar (F12 > Toggle Device Toolbar) to
   resize the viewport, or drag the browser window to narrow widths.
3. Test at the following approximate breakpoints:
   - Normal: > 400 px column width
   - Narrow: 300–400 px
   - Very narrow: 200–300 px
   - Micro: < 200 px

**Expected behaviour (per `onWidgetResize` breakpoints in `Reticulum.js`):**

| Column width | Expected behaviour |
|--------------|--------------------|
| > 400 px     | Full table: Name, Type, TX rate, RX rate columns all visible |
| 300–400 px   | TX/RX rate columns hidden; Name and Type remain |
| 200–300 px   | Type column also hidden; only Name remains |
| < 200 px     | Compact "micro" view with minimal information |

- No horizontal scroll bar appears due to overflow.
- No JavaScript errors at any width.
- The widget height adjusts gracefully.

**Pass criteria:**
[ ] > 400 px: all columns visible
[ ] 300–400 px: TX/RX columns hidden
[ ] 200–300 px: Type column also hidden
[ ] < 200 px: micro/compact view shown
[ ] No JS errors at any width

**Notes:** ____________________________________________________________

---

## Summary

| ID    | Description                             | Pass | Fail | Blocked |
|-------|-----------------------------------------|------|------|---------|
| W-601 | Widget in Add Widget panel              | ☐    | ☐    | ☐       |
| W-602 | Shows correct service status            | ☐    | ☐    | ☐       |
| W-603 | Shows interface table with TX/RX rates  | ☐    | ☐    | ☐       |
| W-604 | Graceful degraded state when stopped    | ☐    | ☐    | ☐       |
| W-605 | Auto-refreshes every 15 seconds         | ☐    | ☐    | ☐       |
| W-606 | Responsive columns at narrow widths     | ☐    | ☐    | ☐       |

**Tester:** ______________________
**Date:** ________________________
**OPNsense version:** ____________
**os-reticulum version:** ________
**Browser / version:** ___________
