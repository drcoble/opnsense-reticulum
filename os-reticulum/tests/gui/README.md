# GUI Manual Test Guide — G-501 to G-525

This directory contains documentation and checklists for manual GUI tests of
the `os-reticulum` OPNsense plugin.  These tests cannot be automated without
a live OPNsense instance and a browser; they must be executed by a human
tester.

---

## Test scope

| Range     | Area               | Count |
|-----------|--------------------|-------|
| G-501–507 | General Settings   | 7     |
| G-508–516 | Interfaces Page    | 9     |
| G-517–520 | LXMF Page          | 4     |
| G-521–525 | Log Viewer         | 5     |
| **Total** |                    | **25**|

Widget tests W-601–W-606 (6 tests) are documented separately in
`../widget/test_widget.md`.

---

## Prerequisites

1. **OPNsense VM** — A running OPNsense 23.7 or later instance with the
   `os-reticulum` package installed.  A local VM (e.g. VirtualBox) is fine.

2. **Plugin installed** — Verify with:
   ```
   pkg info os-reticulum
   ```

3. **Browser with DevTools** — Firefox or Chrome/Chromium.  Keep the DevTools
   console (F12) open throughout testing to catch JavaScript errors.

4. **rnsd binary present** — The virtualenv must be installed:
   ```
   /usr/local/reticulum-venv/bin/rnsd --version
   ```

5. **At least one interface configured** — Some tests (G-508, G-516, W-603)
   require at least one interface to be present in the grid.

---

## How to run

There is no automated runner for GUI tests.  Follow the checklist in
`gui_checklist.md` (located in this directory) and mark each test as you go.

**Step-by-step:**

1. Open `gui_checklist.md` in a text editor or Markdown viewer.
2. Open OPNsense in your browser and navigate to **Services > Reticulum**.
3. Work through each test section in order:
   - G-501–507: General Settings page
   - G-508–516: Interfaces page
   - G-517–520: LXMF page
   - G-521–525: Logs page
4. For each test, perform the listed steps and compare the result against the
   "Expected" column.
5. Mark the "Pass" checkbox (change `☐` to `☑`) or record a failure in the
   Notes column.
6. Fill in the Summary section at the bottom before filing a release.

---

## Checklist file

The full test checklist with steps, expected outcomes, and result checkboxes
is in:

```
tests/gui/gui_checklist.md
```

---

## Test descriptions (quick reference)

### G-501–507: General Settings

| ID    | Description                                      |
|-------|--------------------------------------------------|
| G-501 | Page loads without JavaScript errors             |
| G-502 | Form populated with correct defaults on install  |
| G-503 | Saving valid data shows success banner           |
| G-504 | Invalid port triggers validation error           |
| G-505 | share_instance toggle hides/shows port fields    |
| G-506 | Service status bar auto-refreshes every 10 s     |
| G-507 | Start / Stop / Restart buttons change status     |

### G-508–516: Interfaces

| ID    | Description                                          |
|-------|------------------------------------------------------|
| G-508 | Interface grid loads and shows existing rows         |
| G-509 | "Add interface" modal opens on "+" click             |
| G-510 | Selecting interface type shows correct field set     |
| G-511 | Add a TCPServerInterface end-to-end                  |
| G-512 | Add an RNodeInterface end-to-end                     |
| G-513 | Add an AutoInterface (minimal required fields)       |
| G-514 | Edit existing interface pre-populates all fields     |
| G-515 | Delete interface with confirmation dialog            |
| G-516 | Toggle enabled in grid row works without page reload |

### G-517–520: LXMF

| ID    | Description                                              |
|-------|----------------------------------------------------------|
| G-517 | rnsd dependency warning banner when rnsd is stopped      |
| G-518 | Propagation-specific fields hide when node disabled      |
| G-519 | Hash tag input fields validate 32-char hex format        |
| G-520 | from_static_only=yes with empty peers shows warning      |

### G-521–525: Log Viewer

| ID    | Description                                          |
|-------|------------------------------------------------------|
| G-521 | rnsd log tab shows log lines                         |
| G-522 | lxmd log tab shows log lines (or empty message)      |
| G-523 | Severity filter filters to warning/error only        |
| G-524 | Keyword search filters to matching lines             |
| G-525 | Auto-refresh toggle starts/stops live refresh        |

---

## Filing a failure

If a test fails, record the following in the checklist Notes column:

- OPNsense version and `os-reticulum` package version
- Browser and version
- Exact steps that caused the failure
- Any JavaScript console errors (copy the full error message)
- Screenshot or screen recording if possible

Open a GitHub issue with the label `bug` and `gui` and attach the filled-in
checklist.

---

## Relationship to automated tests

The GUI tests complement (but do not replace) the automated tests:

| Automated suite                         | Covers                            |
|-----------------------------------------|-----------------------------------|
| `tests/model/test_model_validation.py`  | Field validation logic (M-201–209)|
| `tests/template/test_template_output.py`| Config file rendering (T-101–112) |
| `tests/security/test_config_injection.py` | Injection safety (X-701–710)   |
| `tests/api/test_api_endpoints.sh`       | REST API (A-301–309)              |
| `tests/service/smoke_test.sh`           | Post-install filesystem (S-401)   |
| `tests/service/test_service_lifecycle.sh` | Service start/stop (S-402–407) |
| `tests/edge_cases/test_edge_cases.sh`   | Edge cases (E-901–910)            |

Run all automated tests with:

```sh
cd os-reticulum
sh tests/run_all.sh
```
