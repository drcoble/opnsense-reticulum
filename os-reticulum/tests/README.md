# os-reticulum Test Suite

Phase 7 testing implementation for the OPNsense Reticulum plugin.

## Structure

```
tests/
├── conftest.py                    # Shared pytest fixtures (template rendering helpers)
├── template/
│   └── test_template_output.py   # T-101–T-112: Jinja2 template rendering tests
├── model/
│   └── test_model_validation.py  # M-201–M-209: Model field constraint tests
├── reference/
│   ├── t101_minimal_rnsd.config  # Expected output for T-101
│   └── t109_minimal_lxmd.config  # Expected output for T-109
├── api/
│   └── test_api_endpoints.sh     # A-301–A-309: curl-based API tests (on VM)
├── service/
│   ├── smoke_test.sh             # Quick post-install smoke test (on VM)
│   └── test_service_lifecycle.sh # S-401–S-407: Service lifecycle tests (on VM)
├── security/
│   ├── test_security.sh          # X-701–X-710: Security checks (on VM)
│   └── test_config_injection.py  # X-710: Config injection Python test (local)
├── edge_cases/
│   └── test_edge_cases.sh        # E-901–E-910: Edge cases (on VM)
└── gui/
    └── gui_checklist.md          # G-501–G-525, W-601–W-606: Manual GUI checklist
```

## Local Tests (no VM required)

These run against the Jinja2 templates and model XML directly.

### Prerequisites

```sh
pip install jinja2 pytest
```

### Run all local tests

```sh
cd os-reticulum
pytest tests/template/ tests/model/ tests/security/test_config_injection.py -v
```

### Run a specific test file

```sh
pytest tests/template/test_template_output.py -v
pytest tests/model/test_model_validation.py -v
pytest tests/security/test_config_injection.py -v -s   # -s shows print output
```

## VM Tests (require OPNsense VM)

### Prerequisites

1. OPNsense VM with os-reticulum installed
2. SSH access as root
3. Plugin configured with at least one interface

### API tests

```sh
# Copy to VM and run
scp tests/api/test_api_endpoints.sh root@opnsense:/tmp/
ssh root@opnsense "sh /tmp/test_api_endpoints.sh https://localhost admin yourpassword"
```

### Smoke test (post-install)

```sh
scp tests/service/smoke_test.sh root@opnsense:/tmp/
ssh root@opnsense "sh /tmp/smoke_test.sh"
```

### Service lifecycle tests

```sh
scp tests/service/test_service_lifecycle.sh root@opnsense:/tmp/
ssh root@opnsense "sh /tmp/test_service_lifecycle.sh"
```

### Security tests

```sh
scp tests/security/test_security.sh root@opnsense:/tmp/
ssh root@opnsense "sh /tmp/test_security.sh https://localhost admin yourpassword"
```

### Edge case tests

```sh
scp tests/edge_cases/test_edge_cases.sh root@opnsense:/tmp/
ssh root@opnsense "sh /tmp/test_edge_cases.sh https://localhost admin yourpassword"
```

## GUI Tests

Open `tests/gui/gui_checklist.md` and work through the checklist manually in a browser.

## Test ID Reference

| Range | Category | Environment |
|-------|----------|-------------|
| T-101–T-112 | Template output | Local (pytest) |
| M-201–M-209 | Model validation | Local (pytest) |
| A-301–A-309 | API endpoints | OPNsense VM |
| S-401–S-407 | Service lifecycle | OPNsense VM |
| G-501–G-525 | GUI pages | Browser (manual) |
| W-601–W-606 | Dashboard widget | Browser (manual) |
| X-701–X-710 | Security | VM + Local (X-710) |
| E-901–E-910 | Edge cases | OPNsense VM |
