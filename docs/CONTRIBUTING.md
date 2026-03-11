# Contributing to os-reticulum
**Date:** 2026-03-10
**Status:** final
**Source:** Phase 7 source review + plugin architecture docs

---

## Project Structure

```
os-reticulum/
├── Makefile                     # OPNsense plugin build target (make package)
├── pkg-install                  # Post-install script: user, dirs, venv, pip install
├── pkg-deinstall                # Pre-deinstall script: stop services
├── pkg-plist                    # Manifest of all installed files
├── src/
│   ├── etc/
│   │   ├── rc.d/
│   │   │   ├── rnsd             # rc.d service script for rnsd
│   │   │   └── lxmd             # rc.d service script for lxmd (REQUIRE: rnsd)
│   │   ├── rc.syshook.d/
│   │   │   └── start/50-reticulum  # Syshook: triggers reconfigure on boot
│   │   └── newsyslog.conf.d/
│   │       └── reticulum.conf   # Log rotation config
│   └── opnsense/
│       ├── mvc/app/
│       │   ├── models/OPNsense/Reticulum/
│       │   │   ├── Reticulum.xml  # Data model: all fields, types, validators
│       │   │   ├── Reticulum.php  # Model class (extends BaseModel)
│       │   │   ├── Menu/Menu.xml  # GUI navigation menu entries
│       │   │   └── ACL/ACL.xml    # Privilege definitions
│       │   ├── controllers/OPNsense/Reticulum/
│       │   │   ├── Api/RnsdController.php     # /api/reticulum/rnsd/*
│       │   │   ├── Api/LxmdController.php     # /api/reticulum/lxmd/*
│       │   │   ├── Api/ServiceController.php  # /api/reticulum/service/*
│       │   │   └── IndexController.php        # Page routing
│       │   └── views/OPNsense/Reticulum/
│       │       ├── general.volt   # General settings page
│       │       ├── interfaces.volt  # Interface CRUD grid + modal
│       │       ├── lxmf.volt      # LXMF/lxmd configuration page
│       │       └── logs.volt      # Dual-tab log viewer
│       ├── service/
│       │   ├── conf/actions.d/
│       │   │   └── actions_reticulum.conf  # configd action definitions
│       │   └── templates/OPNsense/Reticulum/
│       │       ├── +TARGETS                # Maps templates to output paths
│       │       ├── reticulum_config.j2     # Renders /usr/local/etc/reticulum/config
│       │       ├── lxmf_config.j2          # Renders /usr/local/etc/lxmf/config
│       │       ├── lxmf_allowed.j2         # Renders /usr/local/etc/lxmf/allowed
│       │       ├── lxmf_ignored.j2         # Renders /usr/local/etc/lxmf/ignored
│       │       ├── rc.conf.d_rnsd.j2       # Renders /etc/rc.conf.d/rnsd
│       │       └── rc.conf.d_lxmd.j2       # Renders /etc/rc.conf.d/lxmd
│       ├── scripts/OPNsense/Reticulum/
│       │   ├── info.sh            # Returns installed rns/lxmf versions
│       │   ├── reconfigure.sh     # Runs template reload + service restart
│       │   ├── rnsd_status.sh     # Returns rnsd running/stopped
│       │   ├── lxmd_status.sh     # Returns lxmd running/stopped
│       │   └── rnstatus.sh        # Returns rnsd interface JSON (rnsd -s)
│       └── www/js/widgets/
│           ├── Reticulum.js              # Dashboard widget (extends BaseTableWidget)
│           └── Metadata/Reticulum.xml   # Widget ACL endpoint declarations
└── tests/
    ├── conftest.py                         # pytest fixtures (template renderer, context builder)
    ├── template/test_template_output.py   # T-101–T-112: Jinja2 template tests (local)
    ├── model/test_model_validation.py     # M-201–M-209: Model field constraint tests (local)
    ├── security/
    │   ├── test_config_injection.py       # X-710: Config injection test (local)
    │   └── test_security.sh               # X-701–X-710: Security checks (VM)
    ├── api/test_api_endpoints.sh          # A-301–A-309: API tests (VM)
    ├── service/
    │   ├── smoke_test.sh                  # Post-install smoke test (VM)
    │   └── test_service_lifecycle.sh      # S-401–S-407: Service lifecycle (VM)
    ├── edge_cases/test_edge_cases.sh      # E-901–E-910: Edge cases (VM)
    ├── gui/gui_checklist.md               # G-501–G-525, W-601–W-606: Manual checklist
    └── reference/                         # Expected config file outputs for template tests
        ├── t101_minimal_rnsd.config
        └── t109_minimal_lxmd.config
```

---

## Running Tests

### Local tests (no VM required)

These run against the Jinja2 templates and model XML on your workstation.

**Prerequisites:**
```sh
pip install jinja2 pytest
```

**Run all local tests:**
```sh
cd os-reticulum
pytest tests/template/ tests/model/ tests/security/test_config_injection.py -v
```

**Run individual suites:**
```sh
pytest tests/template/test_template_output.py -v
pytest tests/model/test_model_validation.py -v
pytest tests/security/test_config_injection.py -v -s
```

The `conftest.py` at `tests/conftest.py` provides shared fixtures:
- `render_rnsd(general, interfaces)` — renders `reticulum_config.j2`
- `render_lxmf(lxmf, general)` — renders `lxmf_config.j2`
- `render_rc_rnsd(general)` — renders `rc.conf.d_rnsd.j2`
- `render_rc_lxmd(general, lxmf)` — renders `rc.conf.d_lxmd.j2`
- `render_allowed(lxmf)` — renders `lxmf_allowed.j2`
- `make_ctx(general, interfaces, lxmf)` — builds a full OPNsense context dict

### VM tests (require OPNsense VM with plugin installed)

Copy each script to the VM and run as root:

```sh
VM=root@opnsense-test   # substitute your VM address

# Smoke test (post-install)
scp tests/service/smoke_test.sh $VM:/tmp/
ssh $VM "sh /tmp/smoke_test.sh"

# API tests
scp tests/api/test_api_endpoints.sh $VM:/tmp/
ssh $VM "sh /tmp/test_api_endpoints.sh https://localhost admin yourpassword"

# Service lifecycle
scp tests/service/test_service_lifecycle.sh $VM:/tmp/
ssh $VM "sh /tmp/test_service_lifecycle.sh"

# Security
scp tests/security/test_security.sh $VM:/tmp/
ssh $VM "sh /tmp/test_security.sh https://localhost admin yourpassword"

# Edge cases
scp tests/edge_cases/test_edge_cases.sh $VM:/tmp/
ssh $VM "sh /tmp/test_edge_cases.sh https://localhost admin yourpassword"
```

### GUI and widget tests

Open `tests/gui/gui_checklist.md` and work through it manually in a browser pointed at the VM. No automation is available for these tests.

---

## Code Conventions

### OPNsense MVC patterns

- **Model fields** are defined in `Reticulum.xml`. Field types come from the OPNsense BaseModel field library (`IntegerField`, `BooleanField`, `TextField`, `CSVListField`, etc.).
- **Sensitive fields** (passphrase, rpc_key) must use `UpdateOnlyTextField`. This type never returns the stored value in GET responses and preserves the existing value when the field is absent in a POST.
- **Cross-field validation** lives in `Reticulum.php` as `performValidation()` override. Do not put cross-field logic in XML.
- **API controllers** extend `ApiMutableModelControllerBase`. All service control goes through configd actions — never call `service` or shell commands directly from PHP.
- **configd actions** are defined in `actions_reticulum.conf`. Action names follow the pattern `reticulum.<verb>.<target>` (e.g., `reticulum.start.rnsd`).

### Jinja2 template conventions

- Templates receive the full OPNsense config context. Access the model at `OPNsense.Reticulum.general`, `OPNsense.Reticulum.lxmf`, and `OPNsense.Reticulum.interfaces.interface`.
- Boolean rendering: rnsd uses Python-style (`True`/`False`); lxmf uses INI-style (`yes`/`no`). Keep these consistent with the respective daemon's expected format.
- Optional fields: use `{% if value %}` guards so that unset optional fields produce no output line. Empty keys in the generated config are not acceptable.
- The `+TARGETS` file maps each template to its output path. Any new template must be registered there.

### Volt template conventions

- Field visibility in the interfaces modal uses CSS classes of the form `type-<typename>` (e.g., `type-tcpserver`, `type-rnode`). Fields hidden by default use `d-none`; JavaScript shows/hides them by toggling `d-none` based on the selected type.
- Service action buttons (Start/Stop/Restart) call the API via `ajaxCall` and should not submit the form.
- All user-visible validation messages must match the field's `ValidationMessage` attribute in `Reticulum.xml`.

---

## How to Add a New Interface Type

Follow this checklist in order. All four steps are required.

1. **XML model** (`src/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.xml`)
   - Add new fields under the `interfaces > interface` node.
   - Choose appropriate field types and set `<Constraints>` where needed.
   - If a field is specific to this type (not shared), name it unambiguously (e.g., `new_type_specific_field`).

2. **Volt template** (`src/opnsense/mvc/app/views/OPNsense/Reticulum/interfaces.volt`)
   - Add a `<option value="NewTypeName">New Type Label</option>` to the type selector.
   - Add a CSS visibility block: `.type-newtype { display: none; }`.
   - Add new form fields inside the modal, each wrapped in a `<div class="type-newtype d-none">`.
   - Add `'NewTypeName'` to the JavaScript type-visibility map that controls `d-none` toggling.

3. **Jinja2 template** (`src/opnsense/service/templates/OPNsense/Reticulum/reticulum_config.j2`)
   - Add a conditional block: `{% elif iface.type == 'NewTypeName' %}` with the new type's required and optional fields.
   - Follow the existing pattern for optional field guards (`{% if iface.field_name %}`).

4. **Test cases**
   - Add a sub-case to T-103 in `tests/template/test_template_output.py`: create one interface of the new type and assert the rendered section contains the correct `type = ` value and type-specific fields with no cross-contamination.
   - Add a row to `tests/gui/gui_checklist.md` under G-510 (type-switching modal visibility).
   - Update `docs/phase7-status.md` Notes column for T-103 to record the new type.

---

## PR Checklist

Before opening a pull request, verify:

- [ ] `pytest tests/template/ tests/model/ tests/security/test_config_injection.py` passes with no failures
- [ ] All new fields have `Constraints` defined in `Reticulum.xml` (type, min/max, mask as applicable)
- [ ] Sensitive fields use `UpdateOnlyTextField`
- [ ] No new configd actions are called directly from PHP (all via `configdpRun` or `configdRun`)
- [ ] `pkg-plist` updated if new files were added to `src/`
- [ ] New interface types follow the four-step checklist above
- [ ] Optional Jinja2 fields are guarded with `{% if %}` to avoid emitting empty keys
- [ ] `+TARGETS` updated if a new template was added
- [ ] Manual smoke test passed on OPNsense VM (`sh tests/service/smoke_test.sh` exits 0)
- [ ] `docs/phase7-status.md` Notes updated for any test cases affected by the change
