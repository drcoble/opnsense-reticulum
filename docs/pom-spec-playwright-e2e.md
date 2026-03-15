# Playwright E2E Page Object Model Specification
**Date:** 2026-03-12
**Status:** final
**Source:** Technical documentarian — derived directly from Volt template sources and widget JS

---

## Overview

This document specifies the Page Object Model (POM) layer for a Playwright E2E test suite targeting the OPNsense Reticulum plugin. Every selector listed here is grounded in the actual HTML/JS produced by the Volt templates and the dashboard widget. No selector is inferred or approximate.

**Playwright version assumption:** v1.40+
**Base URL pattern:** `https://<opnsense-host>`
**Auth:** OPNsense uses cookie-based sessions; tests must log in first via the `LoginPage` object and carry the session cookie across all subsequent navigations.

**File layout convention:**
```
tests/e2e/
  pages/
    LoginPage.ts
    NavigationMenu.ts
    ServiceBar.ts
    GeneralSettingsPage.ts
    InterfacesPage.ts
    InterfaceModal.ts
    DeleteInterfaceModal.ts
    LxmfPage.ts
    LogViewerPage.ts
    DashboardWidgetPage.ts
  fixtures/
    auth.fixture.ts
  helpers/
    wait.ts
```

---

## 1. Shared Components

### 1.1 `LoginPage`
**File:** `tests/e2e/pages/LoginPage.ts`

#### Locators
| Name | Selector | Notes |
|---|---|---|
| `usernameField` | `input[name="usernamefld"]` | Standard OPNsense login form |
| `passwordField` | `input[name="passwordfld"]` | |
| `submitButton` | `input[type="submit"]` or `button[type="submit"]` | |
| `errorMessage` | `.alert-danger` | Shown on bad credentials |

#### Action methods
- `goto()` — navigate to `/`
- `login(username: string, password: string)` — fill credentials and submit
- `loginAs(role: 'admin')` — wrapper that reads credentials from env vars `OPNSENSE_USER` / `OPNSENSE_PASSWORD`

#### Assertion helpers
- `expectLoginSucceeded()` — assert URL does not contain `/index.php?login` after submit
- `expectLoginFailed()` — assert `.alert-danger` is visible

#### Waiting strategy
After `login()`: wait for navigation to complete (`waitForURL` not matching `/index.php`) before returning. OPNsense redirects to `/ui/dashboard` on success.

---

### 1.2 `NavigationMenu`
**File:** `tests/e2e/pages/NavigationMenu.ts`

OPNsense uses a multi-level Bootstrap navbar. The Reticulum entries live under **Services** > **Reticulum**.

#### Locators
| Name | Selector | Notes |
|---|---|---|
| `servicesMenu` | `li.dropdown:has(a:text("Services"))` | Top-level nav item |
| `reticulumSubmenu` | `li.dropdown:has(a:text("Reticulum"))` | Nested under Services |
| `generalLink` | `a[href="/ui/reticulum/general"]` | Inside Reticulum submenu |
| `interfacesLink` | `a[href="/ui/reticulum/interfaces"]` | |
| `lxmfLink` | `a[href="/ui/reticulum/lxmf"]` | |
| `logsLink` | `a[href="/ui/reticulum/logs"]` | |

#### Action methods
- `navigateToGeneral()` — hover Services, hover Reticulum, click General link
- `navigateToInterfaces()` — hover Services, hover Reticulum, click Interfaces link
- `navigateToLxmf()` — hover Services, hover Reticulum, click LXMF link
- `navigateToLogs()` — hover Services, hover Reticulum, click Logs link

#### Waiting strategy
After each navigation: wait for `page.waitForLoadState('networkidle')` plus the specific page's landmark element to be visible (e.g., `#maintabs` for settings pages, `#grid-interfaces` for interfaces).

---

### 1.3 `ServiceBar`
**File:** `tests/e2e/pages/ServiceBar.ts`

The standard OPNsense service bar is injected into `#service_status_container` by the `updateServiceControlUI('reticulum')` JS call. It renders Start/Stop/Restart buttons and a status indicator. This component appears on `GeneralSettingsPage` and `InterfacesPage`.

**Note:** `LxmfPage` uses a custom dual service bar — do not use this component for that page. See section 4.

#### Locators
All selectors are scoped to `#service_status_container`.

| Name | Selector | Notes |
|---|---|---|
| `container` | `#service_status_container` | Populated async after `updateServiceControlUI()` resolves |
| `startButton` | `#service_status_container button:has-text("Start")` | Injected by OPNsense framework |
| `stopButton` | `#service_status_container button:has-text("Stop")` | |
| `restartButton` | `#service_status_container button:has-text("Restart")` | |
| `statusIndicator` | `#service_status_container .label` | Bootstrap label element; text is "Running" / "Stopped" |

#### Action methods
- `clickStart()` — click Start, then wait for status to update
- `clickStop()` — click Stop, then wait for status to update
- `clickRestart()` — click Restart, then wait for status to update
- `getStatus()` — return trimmed text of `statusIndicator`

#### Assertion helpers
- `expectServiceRunning()` — assert status indicator text is "Running" and has class `label-success`
- `expectServiceStopped()` — assert status indicator text is "Stopped" and has class `label-danger`

#### Waiting strategy
The service bar container is empty on page load and populated after the first `ajaxCall` returns. Before any interaction: `await page.waitForSelector('#service_status_container button', { state: 'visible' })`.
After clicking Start/Stop/Restart: poll `getStatus()` with a 10-second timeout (the page refreshes the bar every 10 seconds via `setInterval`).

---

## 2. `GeneralSettingsPage`
**File:** `tests/e2e/pages/GeneralSettingsPage.ts`
**URL:** `/ui/reticulum/general`

### 2.1 Locators

#### Page landmark
| Name | Selector |
|---|---|
| `tabBar` | `#maintabs` |
| `form` | `form#general` |

#### Runtime info bar
| Name | Selector | Notes |
|---|---|---|
| `runtimeInfoRow` | `#rnsd-runtime-info` | Populated async; text starts as "loading..." |
| `versionSpan` | `#rnsd-version` | |
| `identitySpan` | `#rnsd-identity` | Truncated to 16 chars + "..."; full hash in `title` attribute |
| `uptimeSpan` | `#rnsd-uptime` | |

#### Tabs (click targets)
| Name | Selector |
|---|---|
| `generalTab` | `#maintabs a[href="#tab-general"]` |
| `transportTab` | `#maintabs a[href="#tab-transport"]` |
| `sharingTab` | `#maintabs a[href="#tab-sharing"]` |
| `managementTab` | `#maintabs a[href="#tab-management"]` |
| `loggingTab` | `#maintabs a[href="#tab-logging"]` |

#### Tab panes (visibility assertions)
| Name | Selector |
|---|---|
| `generalPane` | `#tab-general` |
| `transportPane` | `#tab-transport` |
| `sharingPane` | `#tab-sharing` |
| `managementPane` | `#tab-management` |
| `loggingPane` | `#tab-logging` |

#### General tab fields
| Name | Selector | Type |
|---|---|---|
| `enabledCheckbox` | `#general\\.enabled` | checkbox |

#### Transport tab fields
| Name | Selector | Type |
|---|---|---|
| `enableTransportCheckbox` | `#general\\.enable_transport` | checkbox |
| `respondToProbesCheckbox` | `#general\\.respond_to_probes` | checkbox |
| `panicOnInterfaceErrorCheckbox` | `#general\\.panic_on_interface_error` | checkbox |

#### Sharing tab fields
| Name | Selector | Type |
|---|---|---|
| `shareInstanceCheckbox` | `#general\\.share_instance` | checkbox |
| `sharedInstancePortInput` | `#general\\.shared_instance_port` | text; placeholder "37428" |
| `instanceControlPortInput` | `#general\\.instance_control_port` | text; placeholder "37429" |
| `sharingDisabledMsg` | `#sharing-disabled-msg` | shown when share_instance is unchecked |
| `portConflictMsg` | `#port-conflict-msg` | shown when both port fields have the same non-empty value |
| `shareInstanceDepFields` | `.share_instance_dep` | two `.form-group` elements; hidden when share_instance unchecked |

#### Management tab fields
| Name | Selector | Type |
|---|---|---|
| `enableRemoteMgmtCheckbox` | `#general\\.enable_remote_management` | checkbox |
| `remoteMgmtDepFields` | `#remote-mgmt-dep-fields` | container div; hidden when above is unchecked |
| `remoteManagementAllowedInput` | `#general\\.remote_management_allowed` | tokenizer (data-allownew) |
| `rpcKeyInput` | `#general\\.rpc_key` | password field; never pre-filled |
| `remoteMgmtDisabledMsg` | `#remote-mgmt-disabled-msg` | shown when enableRemoteMgmt is unchecked |

#### Logging tab fields
| Name | Selector | Type |
|---|---|---|
| `loglevelSelect` | `#general\\.loglevel` | `<select>`; options 0–7 |
| `logfileInput` | `#general\\.logfile` | text; placeholder "/var/log/reticulum/rnsd.log" |

#### Form action buttons
| Name | Selector |
|---|---|
| `saveButton` | `#saveBtn` |
| `applyButton` | `#applyBtn` |
| `applySuccessMsg` | `#apply-success-msg` |

### 2.2 Action methods

- `goto()` — navigate to `/ui/reticulum/general`
- `selectTab(tab: 'general' | 'transport' | 'sharing' | 'management' | 'logging')` — click the appropriate tab anchor; wait for the target pane to have class `active`
- `setEnabled(value: boolean)` — check or uncheck `enabledCheckbox`
- `setShareInstance(value: boolean)` — check or uncheck; then assert visibility update of `.share_instance_dep` before proceeding
- `fillSharingPorts(appPort: string, mgmtPort: string)` — fill both port fields; used to trigger port conflict validation
- `setRemoteManagement(value: boolean)` — check or uncheck; assert `#remote-mgmt-dep-fields` visibility
- `addRemoteAdmin(hexHash: string)` — type into `remoteManagementAllowedInput` and press Enter (tokenizer pattern)
- `setLoglevel(value: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7')` — select by value
- `save()` — click `saveButton`; wait for the POST to `/api/reticulum/rnsd/set` to complete
- `applyChanges()` — click `applyButton`; wait for `applySuccessMsg` to become visible, then fade out (3s delay)
- `getRuntimeInfo()` — return `{ version, identity, uptime }` from the three spans

### 2.3 Assertion helpers

- `expectTabActive(tab)` — assert the tab pane has classes `active in`
- `expectShareInstanceDepVisible()` — assert `.share_instance_dep` elements are visible
- `expectShareInstanceDepHidden()` — assert `.share_instance_dep` elements are hidden; `#sharing-disabled-msg` is visible
- `expectPortConflictVisible()` — assert `#port-conflict-msg` is visible
- `expectPortConflictHidden()` — assert `#port-conflict-msg` is hidden
- `expectRemoteMgmtFieldsVisible()` — assert `#remote-mgmt-dep-fields` is visible
- `expectRemoteMgmtFieldsHidden()` — assert `#remote-mgmt-dep-fields` is hidden; `#remote-mgmt-disabled-msg` is visible
- `expectApplySuccessVisible()` — assert `#apply-success-msg` is visible
- `expectVersionLoaded()` — assert `#rnsd-version` text is not "loading..."

### 2.4 Waiting strategies

| Trigger | Wait for |
|---|---|
| `goto()` | `#maintabs` visible |
| `setShareInstance(false)` | `.share_instance_dep` hidden (CSS `display:none`) |
| `setShareInstance(true)` | `.share_instance_dep` visible |
| `setRemoteManagement(false)` | `#remote-mgmt-dep-fields` hidden |
| `setRemoteManagement(true)` | `#remote-mgmt-dep-fields` visible |
| `save()` | Network idle after `/api/reticulum/rnsd/set` returns |
| `applyChanges()` | `#apply-success-msg` visible (`fadeIn`), then not visible (`fadeOut` after 3s) |
| Port field input | `#port-conflict-msg` visibility state settles (synchronous JS, no wait needed) |
| Runtime info bar | Poll `#rnsd-version` until text != "loading..." — API call on page load |

---

## 3. `InterfacesPage` + `InterfaceModal` + `DeleteInterfaceModal`
**File (page):** `tests/e2e/pages/InterfacesPage.ts`
**File (modal):** `tests/e2e/pages/InterfaceModal.ts`
**File (delete modal):** `tests/e2e/pages/DeleteInterfaceModal.ts`
**URL:** `/ui/reticulum/interfaces`

### 3.1 `InterfacesPage` Locators

#### Page landmarks and toolbar
| Name | Selector |
|---|---|
| `addInterfaceButton` | `#addInterfaceBtn` |
| `applyInterfacesButton` | `#applyInterfacesBtn` |
| `applySuccessMsg` | `#apply-success-msg` |
| `grid` | `#grid-interfaces` |

#### Grid columns (data-column-id)
The bootgrid renders rows with cells corresponding to: `name`, `type`, `enabled`, `mode`, `commands`.

| Name | Selector pattern | Notes |
|---|---|---|
| `gridRows` | `#grid-interfaces tbody tr` | All data rows |
| `gridRowByName(name)` | `#grid-interfaces tbody tr:has(td:text-is("${name}"))` | First column is Name |
| `editButtonForRow(name)` | row locator → `.command-edit` button | Bootgrid command formatter injects `.command-edit` |
| `deleteButtonForRow(name)` | row locator → `.command-delete` button | Bootgrid command formatter injects `.command-delete` |
| `enabledToggleForRow(name)` | row locator → `.command-toggle` or `input[type=checkbox]` | Rendered by `rowtoggle` formatter |
| `searchInput` | `#grid-interfaces-search-phrase` | Bootgrid injects this ID pattern |
| `refreshButton` | `#grid-interfaces button.refresh` | Bootgrid toolbar |

### 3.2 `InterfacesPage` Action methods

- `goto()` — navigate to `/ui/reticulum/interfaces`
- `clickAdd()` — click `#addInterfaceBtn`; wait for `#DialogInterface` to become visible
- `clickEditRow(name: string)` — locate row by name, click its edit command; wait for modal
- `clickDeleteRow(name: string)` — locate row by name, click its delete command; wait for `#DialogDeleteInterface`
- `clickApply()` — click `#applyInterfacesBtn`; wait for `#apply-success-msg` to appear
- `searchGrid(term: string)` — fill search input; wait for grid to re-render
- `getRowCount()` — return count of `#grid-interfaces tbody tr`
- `rowExists(name: string)` — return boolean; checks `#grid-interfaces tbody` for a row with matching name cell

### 3.3 `InterfacesPage` Assertion helpers

- `expectRowPresent(name)` — assert `rowExists(name)` is true
- `expectRowAbsent(name)` — assert `rowExists(name)` is false
- `expectGridEmpty()` — assert the empty-state message is shown (`data-empty` attribute text)
- `expectApplySuccessVisible()` — assert `#apply-success-msg` is visible
- `expectRowCount(n)` — assert `getRowCount()` equals `n`

### 3.4 `InterfacesPage` Waiting strategies

| Trigger | Wait for |
|---|---|
| `goto()` | `#grid-interfaces` visible; bootgrid initial load complete (tbody not in loading state) |
| `clickAdd()` / `clickEditRow()` | `#DialogInterface` has CSS class `in` (Bootstrap modal open) |
| `clickDeleteRow()` | `#DialogDeleteInterface` has CSS class `in` |
| `clickApply()` | `#apply-success-msg` visible |
| `searchGrid()` | Grid tbody re-renders (wait for network idle after bootgrid AJAX) |
| Modal save → grid reload | `#grid-interfaces tbody` re-renders after `bootgrid('reload')` |

---

### 3.5 `InterfaceModal` Locators

The edit/add modal is `#DialogInterface`. All form fields are inside `form#interface`.

#### Modal shell
| Name | Selector |
|---|---|
| `modal` | `#DialogInterface` |
| `tabBar` | `#interface-tabs` |
| `saveButton` | `#btn-save-interface` |
| `cancelButton` | `#DialogInterface .modal-footer button:not(#btn-save-interface)` or `.btn-default` in the modal footer |

#### Modal tabs
| Name | Selector |
|---|---|
| `basicTab` | `#interface-tabs a[href="#tab-interface-basic"]` |
| `networkTab` | `#interface-tabs a[href="#tab-interface-network"]` |
| `radioSerialTab` | `#interface-tabs a[href="#tab-interface-radio"]` |
| `advancedTab` | `#interface-tabs a[href="#tab-interface-advanced"]` |

#### Basic Settings tab (`#tab-interface-basic`)
| Name | Selector | Type |
|---|---|---|
| `enabledCheckbox` | `#interface\\.enabled` | checkbox |
| `nameInput` | `#interface\\.name` | text |
| `nameConflictMsg` | `#interface-name-conflict` | error span; hidden unless duplicate |
| `typeSelect` | `#interface\\.type` | `<select>`; values: `TCPServerInterface`, `TCPClientInterface`, `UDPInterface`, `AutoInterface`, `RNodeInterface`, `SerialInterface`, `KISSInterface`, `AX25KISSInterface`, `PipeInterface`, `I2PInterface`, `RNodeMultiInterface` |
| `modeSelect` | `#interface\\.mode` | `<select>`; values: `full`, `gateway`, `access_point`, `roaming`, `boundary` |
| `outgoingCheckbox` | `#interface\\.outgoing` | checkbox |
| `bootstrapOnlyCheckbox` | `#interface\\.bootstrap_only` | checkbox |
| `networkNameInput` | `#interface\\.network_name` | text |
| `passphraseInput` | `#interface\\.passphrase` | password |
| `ifacSizeInput` | `#interface\\.ifac_size` | text |

#### Network tab (`#tab-interface-network`) — fields visible per type

**TCP Server / UDP shared fields** (class `type-tcp-server type-udp`):
| Name | Selector |
|---|---|
| `listenIpInput` | `#interface\\.listen_ip` |
| `listenPortInput` | `#interface\\.listen_port` |

**TCP Client only** (class `type-tcp`):
| Name | Selector |
|---|---|
| `targetHostInput` | `#interface\\.target_host` |
| `targetPortInput` | `#interface\\.target_port` |
| `preferIpv6Checkbox` | `#interface\\.prefer_ipv6` |
| `deviceInput` | `#interface\\.device` |
| `i2pTunneledCheckbox` | `#interface\\.i2p_tunneled` |
| `kissFramingCheckbox` | `#interface\\.kiss_framing` |
| `fixedMtuInput` | `#interface\\.fixed_mtu` |

**UDP only** (class `type-udp`):
| Name | Selector |
|---|---|
| `forwardIpInput` | `#interface\\.forward_ip` |
| `forwardPortInput` | `#interface\\.forward_port` |

**AutoInterface only** (class `type-auto`):
| Name | Selector |
|---|---|
| `groupIdInput` | `#interface\\.group_id` |
| `discoveryScopeSelect` | `#interface\\.discovery_scope` |
| `discoveryPortInput` | `#interface\\.discovery_port` |
| `dataPortInput` | `#interface\\.data_port` |
| `devicesInput` | `#interface\\.devices` |
| `ignoredDevicesInput` | `#interface\\.ignored_devices` |
| `multicastAddressTypeSelect` | `#interface\\.multicast_address_type` |

#### Radio/Serial tab (`#tab-interface-radio`)

**RNode** (class `type-rnode`):
| Name | Selector |
|---|---|
| `frequencyInput` | `#interface\\.frequency` |
| `bandwidthInput` | `#interface\\.bandwidth` |
| `txpowerInput` | `#interface\\.txpower` |
| `spreadingfactorInput` | `#interface\\.spreadingfactor` |
| `codingrateInput` | `#interface\\.codingrate` |
| `airtimeLimitLongInput` | `#interface\\.airtime_limit_long` |
| `airtimeLimitShortInput` | `#interface\\.airtime_limit_short` |

**RNode / Serial / KISS shared** (class `type-rnode type-serial type-kiss`):
| Name | Selector |
|---|---|
| `portInput` | `#interface\\.port` |
| `flowControlCheckbox` | `#interface\\.flow_control` |

**RNode / KISS shared** (class `type-rnode type-kiss`):
| Name | Selector |
|---|---|
| `idCallsignInput` | `#interface\\.id_callsign` |
| `idIntervalInput` | `#interface\\.id_interval` |

**Serial / KISS shared** (class `type-serial type-kiss`):
| Name | Selector |
|---|---|
| `speedInput` | `#interface\\.speed` |
| `paritySelect` | `#interface\\.parity` |
| `stopbitsInput` | `#interface\\.stopbits` |

**Serial only** (class `type-serial`):
| Name | Selector |
|---|---|
| `databitsInput` | `#interface\\.databits` |

**KISS only** (class `type-kiss`):
| Name | Selector |
|---|---|
| `preambleInput` | `#interface\\.preamble` |
| `txtailInput` | `#interface\\.txtail` |
| `persistenceInput` | `#interface\\.persistence` |
| `slottimeInput` | `#interface\\.slottime` |

**AX.25** (class `type-ax25`):
| Name | Selector |
|---|---|
| `callsignInput` | `#interface\\.callsign` |
| `ssidInput` | `#interface\\.ssid` |

**Pipe** (class `type-pipe`):
| Name | Selector |
|---|---|
| `commandInput` | `#interface\\.command` |
| `respawnDelayInput` | `#interface\\.respawn_delay` |

**I2P** (class `type-i2p`):
| Name | Selector |
|---|---|
| `connectableCheckbox` | `#interface\\.connectable` |
| `i2pPeersInput` | `#interface\\.i2p_peers` |

#### Advanced tab (`#tab-interface-advanced`)
| Name | Selector | Notes |
|---|---|---|
| `announceCapInput` | `#interface\\.announce_cap` | All types |
| `bitrateInput` | `#interface\\.bitrate` | All types |
| `discoverableCheckbox` | `#interface\\.discoverable` | class `type-discover` |
| `discoveryNameInput` | `#interface\\.discovery_name` | class `type-discover` |
| `announceIntervalInput` | `#interface\\.announce_interval` | class `type-discover` |
| `reachableOnInput` | `#interface\\.reachable_on` | class `type-discover` |
| `latitudeInput` | `#interface\\.latitude` | class `type-discover` |

### 3.6 `InterfaceModal` Action methods

- `waitForOpen()` — wait for `#DialogInterface.in` (Bootstrap modal fully open)
- `waitForClose()` — wait for `#DialogInterface` to not have class `in`
- `selectTab(tab: 'basic' | 'network' | 'radio' | 'advanced')` — click tab, wait for target pane to be active
- `selectType(type: string)` — select `#interface\\.type` by value; wait for type visibility classes to settle (synchronous JS)
- `fillBasic(opts: { name, type, mode?, enabled?, outgoing?, bootstrapOnly? })` — fill Basic tab fields
- `fillTcpServer(opts: { listenIp?, listenPort })` — fill Network tab for TCP Server
- `fillTcpClient(opts: { targetHost, targetPort, preferIpv6? })` — fill Network tab for TCP Client
- `fillUdp(opts: { listenIp?, listenPort, forwardIp?, forwardPort? })` — fill Network tab for UDP
- `fillAuto(opts: { groupId? })` — fill Network tab for AutoInterface
- `fillRnode(opts: { port, frequency, bandwidth, txpower, spreadingfactor, codingrate })` — fill Radio tab for RNode
- `fillSerial(opts: { port, speed, databits?, parity?, stopbits? })` — fill Radio tab for Serial
- `save()` — click `#btn-save-interface`; wait for modal to close and grid to reload
- `cancel()` — click cancel button; wait for modal to close

### 3.7 `InterfaceModal` Assertion helpers

- `expectOpen()` — assert `#DialogInterface` has class `in`
- `expectClosed()` — assert `#DialogInterface` does not have class `in`
- `expectNameConflictVisible()` — assert `#interface-name-conflict` is visible
- `expectTypeFieldsVisible(type)` — assert that the CSS class block for that type is visible (e.g., `.type-tcp` visible when type is TCP Client)
- `expectTypeFieldsHidden(type)` — assert type-specific fields for a different type are hidden
- `expectSaveButtonEnabled()` — assert `#btn-save-interface` is not disabled
- `expectSaveButtonDisabled()` — assert `#btn-save-interface` has `disabled` attribute

#### Type visibility CSS class mapping
| Type value | Visible CSS class |
|---|---|
| `TCPServerInterface` | `.type-tcp-server` |
| `TCPClientInterface` | `.type-tcp` |
| `UDPInterface` | `.type-udp` |
| `AutoInterface` | `.type-auto` |
| `RNodeInterface` | `.type-rnode` |
| `SerialInterface` | `.type-serial` |
| `KISSInterface` | `.type-kiss` |
| `AX25KISSInterface` | `.type-ax25` |
| `PipeInterface` | `.type-pipe` |
| `I2PInterface` | `.type-i2p` |
| `RNodeMultiInterface` | `.type-multi` |

Fields with multiple classes (e.g., `type-rnode type-serial type-kiss`) are shown when any of their listed types is selected.

### 3.8 `InterfaceModal` Waiting strategies

| Trigger | Wait for |
|---|---|
| `selectType()` | Type visibility JS runs synchronously; no async wait needed, but use `expect(locator).toBeVisible()` before interacting with type-specific fields |
| `save()` | POST to `/api/reticulum/interfaces/addItem` or `setItem` completes; grid `bootgrid('reload')` fires; tbody updates |
| Modal open | `#DialogInterface` has class `in` and `#btn-save-interface` is visible |

---

### 3.9 `DeleteInterfaceModal` Locators

| Name | Selector |
|---|---|
| `modal` | `#DialogDeleteInterface` |
| `confirmMessage` | `#delete-confirm-msg` |
| `confirmButton` | `#DialogDeleteInterface .btn-danger` or button with "Delete" text |
| `cancelButton` | `#DialogDeleteInterface .btn-default` |

### 3.10 `DeleteInterfaceModal` Action methods

- `waitForOpen()` — wait for `#DialogDeleteInterface.in`
- `getConfirmMessage()` — return text of `#delete-confirm-msg`
- `confirm()` — click confirm button; wait for modal close and grid reload
- `cancel()` — click cancel; wait for modal close; grid must not reload

### 3.11 `DeleteInterfaceModal` Assertion helpers

- `expectOpen()` — assert modal has class `in`
- `expectConfirmMessageContains(name)` — assert `#delete-confirm-msg` text includes the interface name

### 3.12 Waiting strategies

After `confirm()`: wait for `#DialogDeleteInterface` to not have class `in`, then wait for `#grid-interfaces tbody` to update (grid calls `bootgrid('reload')`).

---

## 4. `LxmfPage`
**File:** `tests/e2e/pages/LxmfPage.ts`
**URL:** `/ui/reticulum/lxmf`

### 4.1 Locators

#### Dual service bar (custom — not `ServiceBar` component)
| Name | Selector | Notes |
|---|---|---|
| `rnsdStatusBadge` | `#rnsd-status-badge` | Read-only; text: "Running" / "Stopped" / "loading..." |
| `rnsdStatusRow` | `#rnsd-status-row` | Container row |
| `lxmdStartButton` | `#lxmd-btn-start` | `.btn-success` |
| `lxmdStopButton` | `#lxmd-btn-stop` | `.btn-danger` |
| `lxmdRestartButton` | `#lxmd-btn-restart` | `.btn-default` |
| `lxmdStatusBadge` | `#lxmd-status-badge` | Text: "Running" / "Stopped" / "loading..." |
| `lxmdActionMsg` | `#lxmd-action-msg` | Transient feedback span; hidden by default |
| `rnsdWarningBanner` | `#rnsd-warning` | Alert shown when rnsd is not running |

#### Tabs
| Name | Selector |
|---|---|
| `tabBar` | `#maintabs` |
| `generalTab` | `#maintabs a[href="#tab-general"]` |
| `propagationTab` | `#maintabs a[href="#tab-propagation"]` |
| `costsTab` | `#maintabs a[href="#tab-costs"]` |
| `peeringTab` | `#maintabs a[href="#tab-peering"]` |
| `aclTab` | `#maintabs a[href="#tab-acl"]` |
| `loggingTab` | `#maintabs a[href="#tab-logging"]` |
| `propagationDepTabs` | `.propagation-dep-tab` | Two `<li>` elements (Stamp Costs, Peering); hidden unless `lxmf.enable_node` is checked |

#### General tab fields
| Name | Selector | Type |
|---|---|---|
| `enabledCheckbox` | `#lxmf\\.enabled` | checkbox |
| `displayNameInput` | `#lxmf\\.display_name` | text |
| `lxmfAnnounceAtStartCheckbox` | `#lxmf\\.lxmf_announce_at_start` | checkbox |
| `lxmfAnnounceIntervalInput` | `#lxmf\\.lxmf_announce_interval` | text |
| `deliveryTransferMaxSizeInput` | `#lxmf\\.delivery_transfer_max_size` | text |

#### Propagation tab fields
| Name | Selector | Type |
|---|---|---|
| `enableNodeCheckbox` | `#lxmf\\.enable_node` | checkbox |
| `propagationDisabledMsg` | `#propagation-disabled-msg` | shown when `enable_node` unchecked |
| `propagationDepFields` | `.propagation-dep` | all fields gated on `enable_node`; hidden when unchecked |
| `nodeNameInput` | `#lxmf\\.node_name` | text |
| `announceIntervalInput` | `#lxmf\\.announce_interval` | text |
| `announceAtStartCheckbox` | `#lxmf\\.announce_at_start` | checkbox |
| `messageStorageLimitInput` | `#lxmf\\.message_storage_limit` | text |
| `propagationMessageMaxSizeInput` | `#lxmf\\.propagation_message_max_size` | text |
| `propagationSyncMaxSizeInput` | `#lxmf\\.propagation_sync_max_size` | text |
| `syncSizeWarn` | `#sync-size-warn` | warning span |
| `syncSizeMin` | `#sync-size-min` | inner span showing computed minimum |

#### Costs tab fields
| Name | Selector | Type |
|---|---|---|
| `stampCostTargetInput` | `#lxmf\\.stamp_cost_target` | text |
| `stampCostFlexibilityInput` | `#lxmf\\.stamp_cost_flexibility` | text |
| `stampFloorWarn` | `#stamp-floor-warn` | warning span |
| `peeringCostInput` | `#lxmf\\.peering_cost` | text |
| `remotePeeringCostMaxInput` | `#lxmf\\.remote_peering_cost_max` | text |

#### Peering tab fields
| Name | Selector | Type |
|---|---|---|
| `autopeerCheckbox` | `#lxmf\\.autopeer` | checkbox |
| `autopeerMaxdepthInput` | `#lxmf\\.autopeer_maxdepth` | text |
| `maxPeersInput` | `#lxmf\\.max_peers` | text |
| `fromStaticOnlyCheckbox` | `#lxmf\\.from_static_only` | checkbox |
| `staticPeersInput` | `#lxmf\\.static_peers` | tokenizer |
| `staticOnlyWarn` | `#static-only-warn` | warning when `from_static_only` is true but list is empty |

#### ACL tab fields
| Name | Selector | Type |
|---|---|---|
| `authRequiredCheckbox` | `#lxmf\\.auth_required` | checkbox |
| `controlAllowedInput` | `#lxmf\\.control_allowed` | tokenizer |
| `allowedIdentitiesInput` | `#lxmf\\.allowed_identities` | tokenizer |
| `ignoredDestinationsInput` | `#lxmf\\.ignored_destinations` | tokenizer |
| `prioritiseDestinationsInput` | `#lxmf\\.prioritise_destinations` | tokenizer |

#### Logging tab fields
| Name | Selector | Type |
|---|---|---|
| `loglevelSelect` | `#lxmf\\.loglevel` | `<select>`; options 0–7 |
| `logfileInput` | `#lxmf\\.logfile` | text |
| `onInboundInput` | `#lxmf\\.on_inbound` | text |
| `onInboundWarn` | `#on-inbound-warn` | security warning span; shown when `on_inbound` is non-empty |

#### Form action buttons
| Name | Selector |
|---|---|
| `saveButton` | `#saveBtn` |
| `applyButton` | `#applyBtn` |
| `applySuccessMsg` | `#apply-success-msg` |

### 4.2 Action methods

- `goto()` — navigate to `/ui/reticulum/lxmf`
- `selectTab(tab: 'general' | 'propagation' | 'costs' | 'peering' | 'acl' | 'logging')` — click the tab; wait for pane to be active. Note: `costs` and `peering` tabs are hidden until `enableNodeCheckbox` is checked.
- `startLxmd()` — click `lxmdStartButton`; wait for `lxmdStatusBadge` to update
- `stopLxmd()` — click `lxmdStopButton`; wait for `lxmdStatusBadge` to update
- `restartLxmd()` — click `lxmdRestartButton`; wait for `lxmdStatusBadge` to update
- `setEnablePropagationNode(value: boolean)` — check/uncheck `enableNodeCheckbox`; wait for `.propagation-dep-tab` visibility and `.propagation-dep` field visibility to settle
- `fillGeneralSettings(opts)` — fill `displayNameInput`, set checkboxes
- `fillPropagationSettings(opts)` — fill propagation fields
- `fillCostSettings(opts)` — fill stamp cost fields; assert `stampFloorWarn` state as needed
- `fillPeeringSettings(opts)` — fill peering fields; add static peers via tokenizer
- `save()` — click `saveButton`; wait for POST to complete
- `applyChanges()` — click `applyButton`; wait for `applySuccessMsg`

### 4.3 Assertion helpers

- `expectRnsdWarningVisible()` — assert `#rnsd-warning` is visible (rnsd not running)
- `expectRnsdWarningHidden()` — assert `#rnsd-warning` is hidden
- `expectRnsdStatus(status: 'Running' | 'Stopped')` — assert `#rnsd-status-badge` text
- `expectLxmdStatus(status: 'Running' | 'Stopped')` — assert `#lxmd-status-badge` text
- `expectPropagationTabsVisible()` — assert `.propagation-dep-tab` items are visible
- `expectPropagationTabsHidden()` — assert `.propagation-dep-tab` items are hidden
- `expectPropagationDepFieldsVisible()` — assert `.propagation-dep` form groups are visible
- `expectSyncSizeWarnVisible()` — assert `#sync-size-warn` is visible
- `expectStampFloorWarnVisible()` — assert `#stamp-floor-warn` is visible
- `expectStaticOnlyWarnVisible()` — assert `#static-only-warn` is visible
- `expectApplySuccessVisible()` — assert `#apply-success-msg` is visible

### 4.4 Waiting strategies

| Trigger | Wait for |
|---|---|
| `goto()` | `#maintabs` visible; status badges polled by JS (wait until not "loading...") |
| `startLxmd()` / `stopLxmd()` | `#lxmd-status-badge` text changes from "loading..." to a final state |
| `setEnablePropagationNode(true)` | `.propagation-dep-tab` becomes visible; `.propagation-dep` fields become visible |
| `setEnablePropagationNode(false)` | `.propagation-dep-tab` hidden; `#propagation-disabled-msg` visible |
| Stamp cost field input | `#stamp-floor-warn` state is driven by synchronous JS |
| `from_static_only` + empty static peers | `#static-only-warn` state is synchronous |
| `save()` | POST to `/api/reticulum/lxmd/set` completes |
| `applyChanges()` | `#apply-success-msg` visible then fades out (3s) |

---

## 5. `LogViewerPage`
**File:** `tests/e2e/pages/LogViewerPage.ts`
**URL:** `/ui/reticulum/logs`

### 5.1 Locators

#### Tab bar (service selector)
| Name | Selector | Notes |
|---|---|---|
| `tabBar` | `#log-tabs` | `role="tablist"` |
| `rnsdTab` | `#log-tabs a[data-service="rnsd"]` | Default active tab |
| `lxmdTab` | `#log-tabs a[data-service="lxmd"]` | |

#### Filter controls
| Name | Selector | Notes |
|---|---|---|
| `severitySelect` | `#log-level` | `<select>`; options "" (All), 0–7 |
| `searchInput` | `#log-search` | Keyword filter; case-insensitive substring |
| `linesSelect` | `#log-lines` | `<select>`; values: 10, 25, 50, 100, 200, 500 |
| `refreshButton` | `#refresh-logs` | Triggers `loadLogs()` |
| `downloadButton` | `#download-logs` | Triggers Blob download |
| `autoRefreshCheckbox` | `#auto-refresh` | Enables 5-second polling |

#### Output states
| Name | Selector | Shown when |
|---|---|---|
| `loadingIndicator` | `#log-loading` | API fetch in progress |
| `emptyServiceMsg` | `#log-empty-service` | API returned empty logs (service never started) |
| `emptyFilterMsg` | `#log-empty-filter` | Filters excluded all lines from non-empty log |
| `logOutput` | `#log-output` | Log lines are available and pass filters |
| `outputPane` | `#log-output-pane` | Shared single pane for both tabs |

### 5.2 Action methods

- `goto()` — navigate to `/ui/reticulum/logs`; wait for initial `loadLogs()` to complete
- `selectService(service: 'rnsd' | 'lxmd')` — click the appropriate tab; wait for `shown.bs.tab` to fire and the API call to complete
- `setSeverity(value: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7')` — select by value; filters apply synchronously (no new API call)
- `setSearch(keyword: string)` — fill `searchInput`; filters apply synchronously
- `setLineCount(count: '10' | '25' | '50' | '100' | '200' | '500')` — select by value; triggers a new API call
- `clickRefresh()` — click `#refresh-logs`; wait for `#log-loading` to hide
- `enableAutoRefresh()` — check `#auto-refresh`
- `disableAutoRefresh()` — uncheck `#auto-refresh`
- `clickDownload()` — click `#download-logs`; no navigation occurs (Blob download)
- `getLogText()` — return text content of `#log-output`
- `getVisibleState()` — return which output element is currently shown: `'loading' | 'empty-service' | 'empty-filter' | 'log-output'`

### 5.3 Assertion helpers

- `expectServiceSelected(service)` — assert the correct tab has class `active`
- `expectLoadingVisible()` — assert `#log-loading` is visible
- `expectEmptyServiceVisible()` — assert `#log-empty-service` is visible
- `expectEmptyFilterVisible()` — assert `#log-empty-filter` is visible
- `expectLogOutputVisible()` — assert `#log-output` is visible and not empty
- `expectLogContains(text)` — assert `#log-output` text content includes `text`
- `expectLogNotContains(text)` — assert `#log-output` text content does not include `text`

### 5.4 Waiting strategies

| Trigger | Wait for |
|---|---|
| `goto()` | `#log-loading` hidden (initial fetch complete) |
| `selectService()` | `#log-loading` visible then hidden (new fetch fires on `shown.bs.tab`) |
| `setLineCount()` | `#log-loading` visible then hidden (new fetch fires) |
| `clickRefresh()` | `#log-loading` hidden |
| `setSeverity()` / `setSearch()` | Output state updates synchronously; no wait needed; use `expect().toBeVisible()` immediately |
| Auto-refresh | After enabling, assert `#log-loading` appears within 5.5 seconds |
| Download | No navigation; assert no error banner appears |

---

## 6. `DashboardWidgetPage`
**File:** `tests/e2e/pages/DashboardWidgetPage.ts`
**URL:** `/ui/dashboard` (OPNsense main dashboard)

**Note:** The widget is embedded in the OPNsense dashboard grid as a standard BaseTableWidget. All widget IDs are scoped within `#reticulum-widget`, which is itself inside the dashboard grid cell. Widget state is driven by 4 parallel API calls fired on `onMarkupRendered()` and every 15 seconds via `tickTimeout`.

### 6.1 Locators

#### Widget container
| Name | Selector | Notes |
|---|---|---|
| `widgetContainer` | `#reticulum-widget` | Rendered by `getMarkup()` |

All locators below are scoped inside `#reticulum-widget`.

#### Health banner rows
| Name | Selector | Notes |
|---|---|---|
| `rnsdStatusCell` | `#ret-rnsd-status` | Text: "Running" / "Stopped" / "Unknown"; contains `<i class="fa fa-circle ...">` |
| `lxmdStatusRow` | `#ret-row-lxmd` | Shown only when lxmf_version is present in info API response |
| `lxmdStatusCell` | `#ret-lxmd-status` | Text: "Running" / "Stopped" / "Unknown" |
| `ifcountRow` | `#ret-row-ifcount` | |
| `ifcountCell` | `#ret-ifcount` | Text pattern: "N / M up" |
| `trafficRow` | `#ret-row-traffic` | |
| `trafficCell` | `#ret-traffic` | Text pattern: "X.X KB / X.X KB" |

#### Detail block
| Name | Selector | Notes |
|---|---|---|
| `detailBlock` | `#ret-detail-block` | Hidden when rnsd stopped or width < 200px |
| `versionRow` | `#ret-row-version` | |
| `versionCell` | `#ret-version` | Text: "rns X.X.X" or "rns X.X.X / lxmf X.X.X" |
| `identityRow` | `#ret-row-identity` | |
| `identityCell` | `#ret-identity` | `<code>` element; 8-char preview + "…"; full hash in `title` |

#### Compact micro view (< 200px)
| Name | Selector |
|---|---|
| `compactView` | `#ret-compact` |
| `compactRnsd` | `#ret-compact-rnsd` |
| `compactLxmd` | `#ret-compact-lxmd` |

#### Interface table
| Name | Selector | Notes |
|---|---|---|
| `ifaceSection` | `#ret-iface-section` | Hidden when rnsd stopped or width < 300px |
| `ifaceTable` | `#ret-iface-table` | |
| `ifaceList` | `#ret-iface-list` | `<tbody>` |
| `ifaceRows` | `#ret-iface-list tr` | One row per interface |
| `trafficColumns` | `.ret-col-traffic` | Hidden at width < 400px |

#### Degraded state banner
| Name | Selector | Notes |
|---|---|---|
| `degradedBanner` | `#ret-degraded` | Shown when rnsd not running AND width >= 200px |
| `degradedSettingsLink` | `#ret-degraded a[href="/ui/reticulum/general"]` | Link to General settings |

### 6.2 Action methods

- `goto()` — navigate to `/ui/dashboard`
- `waitForWidgetLoad()` — wait for `#reticulum-widget` to be visible and `#ret-rnsd-status` text to not be "Loading…"
- `getTransportStatus()` — return text of `#ret-rnsd-status` (strips HTML tags)
- `getPropagationStatus()` — return text of `#ret-lxmd-status`
- `getInterfaceCount()` — return text of `#ret-ifcount`
- `getTraffic()` — return text of `#ret-traffic`
- `getVersionText()` — return text of `#ret-version`
- `getIdentityPreview()` — return text of `#ret-identity code` element
- `getIdentityFull()` — return `title` attribute of `#ret-identity code` element
- `getInterfaceRowCount()` — return count of `#ret-iface-list tr`
- `resizeWidget(widthPx: number)` — use Playwright `page.setViewportSize` or drag the dashboard grid cell handle to the target width; triggers `onWidgetResize`
- `clickDegradedLink()` — click `#ret-degraded a`; wait for navigation to `/ui/reticulum/general`
- `waitForNextTick()` — wait 16 seconds (one full tick cycle) for `onWidgetTick()` to fire and DOM to update

### 6.3 Assertion helpers

- `expectTransportRunning()` — assert `#ret-rnsd-status i.fa` has class `text-success`
- `expectTransportStopped()` — assert `#ret-rnsd-status i.fa` has class `text-danger`
- `expectPropagationRowVisible()` — assert `#ret-row-lxmd` is visible
- `expectPropagationRowHidden()` — assert `#ret-row-lxmd` is hidden
- `expectDegradedBannerVisible()` — assert `#ret-degraded` is visible
- `expectDegradedBannerHidden()` — assert `#ret-degraded` is hidden
- `expectDetailBlockVisible()` — assert `#ret-detail-block` is visible
- `expectDetailBlockHidden()` — assert `#ret-detail-block` is hidden
- `expectCompactViewVisible()` — assert `#ret-compact` is visible
- `expectCompactViewHidden()` — assert `#ret-compact` is hidden
- `expectIfaceSectionVisible()` — assert `#ret-iface-section` is visible
- `expectTrafficColumnsVisible()` — assert `.ret-col-traffic` elements are visible
- `expectTrafficColumnsHidden()` — assert `.ret-col-traffic` elements have `display:none`
- `expectTransportBadgePresent()` — assert `.ret-transport-badge` is present in `#ret-rnsd-status`
- `expectInterfaceRowCount(n)` — assert `#ret-iface-list tr` count equals `n`

### 6.4 Waiting strategies

| Trigger | Wait for |
|---|---|
| `goto()` / `waitForWidgetLoad()` | `#reticulum-widget` visible; `#ret-rnsd-status` text != "Loading…" (all 4 API calls fired in `onMarkupRendered`) |
| `resizeWidget()` | `onWidgetResize` fires synchronously; assert new layout state immediately |
| Service stopped externally | `waitForNextTick()` (up to 15s) then assert degraded state |
| `clickDegradedLink()` | Navigation to `/ui/reticulum/general` |

**Breakpoint test widths to cover:**

| Width | Expected state |
|---|---|
| >= 400px | All rows, all columns, `#ret-compact` hidden |
| 300–399px | `.ret-col-traffic` hidden; detail block and iface section shown |
| 200–299px | `#ret-iface-section` and `#ret-row-identity` hidden; health banner visible |
| < 200px | `#ret-compact` shown; everything else hidden (including `#ret-degraded`) |

---

## 7. Composition Patterns

This section documents how page objects chain together for multi-step flows.

### 7.1 "Create TCP Client interface and verify in grid"

```
1. LoginPage.loginAs('admin')
2. NavigationMenu.navigateToInterfaces()
3. InterfacesPage: note initial row count
4. InterfacesPage.clickAdd()
5. InterfaceModal.waitForOpen()
6. InterfaceModal.selectType('TCPClientInterface')
7. InterfaceModal.fillBasic({ name: 'MyTCP', type: 'TCPClientInterface' })
8. InterfaceModal.selectTab('network')
9. InterfaceModal.fillTcpClient({ targetHost: '10.0.0.1', targetPort: '4242' })
10. InterfaceModal.save()       // waits for grid reload
11. InterfacesPage.expectRowPresent('MyTCP')
12. InterfacesPage.clickApply()
13. InterfacesPage.expectApplySuccessVisible()
```

### 7.2 "Edit existing interface and verify type field visibility"

```
1. InterfacesPage.clickEditRow('MyTCP')
2. InterfaceModal.waitForOpen()
3. InterfaceModal.expectTypeFieldsVisible('type-tcp')   // target_host visible
4. InterfaceModal.selectType('UDPInterface')
5. InterfaceModal.expectTypeFieldsHidden('type-tcp')    // target_host hidden
6. InterfaceModal.expectTypeFieldsVisible('type-udp')   // listen_port visible
7. InterfaceModal.cancel()
```

### 7.3 "Delete interface and verify grid update"

```
1. InterfacesPage.clickDeleteRow('MyTCP')
2. DeleteInterfaceModal.waitForOpen()
3. DeleteInterfaceModal.expectConfirmMessageContains('MyTCP')
4. DeleteInterfaceModal.confirm()       // waits for grid reload
5. InterfacesPage.expectRowAbsent('MyTCP')
```

### 7.4 "Port conflict validation on General settings"

```
1. GeneralSettingsPage.goto()
2. GeneralSettingsPage.selectTab('sharing')
3. GeneralSettingsPage.setShareInstance(true)
4. GeneralSettingsPage.expectShareInstanceDepVisible()
5. GeneralSettingsPage.fillSharingPorts('37428', '37428')   // same value
6. GeneralSettingsPage.expectPortConflictVisible()
7. GeneralSettingsPage.fillSharingPorts('37428', '37429')   // different values
8. GeneralSettingsPage.expectPortConflictHidden()
```

### 7.5 "Enable propagation node and verify gated tab/field visibility on LXMF page"

```
1. LxmfPage.goto()
2. LxmfPage.selectTab('propagation')
3. LxmfPage.expectPropagationTabsHidden()           // Costs/Peering tabs not shown
4. LxmfPage.setEnablePropagationNode(true)
5. LxmfPage.expectPropagationTabsVisible()
6. LxmfPage.expectPropagationDepFieldsVisible()
7. LxmfPage.selectTab('costs')                       // now accessible
8. LxmfPage.fillCostSettings({ stampCostTarget: '20', stampCostFlexibility: '8' })
9. LxmfPage.expectStampFloorWarnVisible()            // 20 - 8 = 12, below min of 13
```

### 7.6 "Log viewer service tab switch and filter interaction"

```
1. LogViewerPage.goto()
2. LogViewerPage.expectServiceSelected('rnsd')
3. LogViewerPage.setSeverity('3')                // Notice and below
4. LogViewerPage.setSearch('error')              // apply keyword
5. // either log-output visible or log-empty-filter visible (no re-fetch needed)
6. LogViewerPage.selectService('lxmd')           // fires new fetch
7. LogViewerPage.expectServiceSelected('lxmd')
8. // wait for loading spinner to clear
9. LogViewerPage.setLineCount('500')             // triggers new fetch
```

### 7.7 "Dashboard widget degraded state when rnsd stopped"

```
1. DashboardWidgetPage.goto()
2. DashboardWidgetPage.waitForWidgetLoad()
3. DashboardWidgetPage.expectTransportRunning()
4. DashboardWidgetPage.expectDegradedBannerHidden()
5. // (external) stop rnsd via API or GeneralSettingsPage
6. DashboardWidgetPage.waitForNextTick()          // up to 15s for next poll
7. DashboardWidgetPage.expectTransportStopped()
8. DashboardWidgetPage.expectDegradedBannerVisible()
9. DashboardWidgetPage.expectDetailBlockHidden()
10. DashboardWidgetPage.expectIfaceSectionHidden()
11. DashboardWidgetPage.clickDegradedLink()
12. // page navigates to /ui/reticulum/general
```

---

## 8. Known Constraints and Test Authoring Notes

### OPNsense-specific selector caveats

- **Escaped dots in IDs:** OPNsense form field IDs use dots (e.g., `general.enabled`). In jQuery this is escaped as `#general\\.enabled`. In Playwright CSS selectors use `#general\\.enabled` (one backslash in the selector string, but requires `\\` in JS template literals). Prefer `page.locator('#general\\.enabled')` over `getByTestId` — no `data-testid` attributes exist in the current templates.
- **Tokenizer fields:** Fields with `data-allownew="true"` (e.g., `#general\\.remote_management_allowed`, `#lxmf\\.static_peers`) are rendered by the OPNsense tokenizer plugin (Bootstrap Tags Input or similar). To add a value: click the input, type the token, press Enter. To verify a token was added: assert a `.tag` or `.token` element with the expected text appears inside the tokenizer container.
- **Bootgrid AJAX timing:** `#grid-interfaces` loads data via AJAX after DOM ready. Always wait for at least one `tbody tr` to be visible before asserting row content, unless testing the empty state.
- **Bootstrap modal animation:** OPNsense uses Bootstrap 3. Modals fade in/out with a 300ms CSS transition. Use `waitForSelector('#DialogInterface.in')` (class `in` is added after the transition completes) rather than just `visible`.
- **Service bar injection:** `#service_status_container` is empty on initial render and populated by the first `updateServiceControlUI()` AJAX call. Do not attempt to interact with service buttons until the container has child elements.
- **Widget tick timing:** The dashboard widget polls every 15 seconds (`tickTimeout = 15`). For tests that change service state externally, allow at least 16 seconds before asserting widget state changes, or intercept the API responses to force an immediate update.

### Selector stability notes

All selectors in this document are derived from the current Volt template source. The following are load-bearing stable identifiers:

- `#service_status_container` — OPNsense framework standard; stable across versions
- `#grid-interfaces`, `#DialogInterface`, `#DialogDeleteInterface` — defined in `interfaces.volt`; not generated
- All `#general.*`, `#interface.*`, `#lxmf.*` field IDs — defined directly in Volt templates; only change if fields are added or removed
- `#reticulum-widget` — defined in `getMarkup()` in `Reticulum.js`; only changes if widget is refactored

The following are subject to change if OPNsense framework internals change:

- `#grid-interfaces-search-phrase` — bootgrid-generated ID; verify against actual rendered HTML
- Service bar button text ("Start", "Stop", "Restart") — rendered by OPNsense framework helper; may be translated in non-English locales. Use text selectors with `exact: true` or prefer structural selectors within `#service_status_container`.
