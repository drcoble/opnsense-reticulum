# Phase 7 — VM Setup Guide
**Date:** 2026-03-10
**Status:** final
**Source:** Phase 7 runbook (`docs/phase7-runbook.md`) + plugin source review

---

## Overview

This guide covers the fastest path from zero to a running test environment: stand up a fresh OPNsense 24.x VM, build the plugin package, install it, and verify the installation with the smoke test script.

**Time required:** approximately 30–45 minutes for a first-time setup.

---

## 1. VM Requirements

| Resource | Minimum | Notes |
|----------|---------|-------|
| RAM | 2 GB | 4 GB recommended if running multiple services |
| Disk | 20 GB | Python virtualenv + source clones add ~1 GB |
| Network adapter 1 | LAN (NAT or bridged) | Must be reachable from your workstation |
| Network adapter 2 | WAN (optional) | Required only for internet-connected testing |
| Internet access | Required | `pkg install` and git clones happen during post-install |
| OPNsense version | 24.x | FreeBSD 14.x base |

Do not test on a production firewall.

---

## 2. OPNsense Installation (brief)

1. Download the OPNsense 24.x ISO from https://opnsense.org/download/.
2. Boot the VM from the ISO and follow the installer (`opnsense-installer`).
3. After first boot, complete the console setup wizard:
   - Assign interfaces (at minimum one LAN interface).
   - Set the root password.
4. Confirm the web GUI is reachable at `https://<VM-LAN-IP>`.

---

## 3. Enable SSH Access

SSH is not enabled by default. Enable it before attempting to copy the package.

**Via GUI:** System > Settings > Administration > Secure Shell — check "Enable Secure Shell" and "Permit root login", then Save.

**Via console (alternative):**
```sh
# On the OPNsense console, option 8 (Shell)
/usr/sbin/sshd -o PermitRootLogin=yes
```

Confirm from your workstation:
```sh
ssh root@<VM-LAN-IP>
# Accept the host key on first connection
```

---

## 4. Verify Baseline

```sh
# SSH to VM
ssh root@<VM-LAN-IP>

# Confirm FreeBSD version (expect 14.x-RELEASE-...)
uname -r

# Confirm pkg is functional
pkg update
```

If `pkg update` fails, check network connectivity and DNS from the OPNsense console.

---

## 5. Prerequisites on the VM

The plugin post-install script (`pkg-install`) requires these packages. Install them before running `pkg install os-reticulum`:

```sh
pkg install python311 py311-setuptools git
```

These are checked automatically by `pkg-install` and will cause installation to abort with a clear error if missing.

---

## 6. Build the Plugin Package (on workstation)

```sh
cd /path/to/Opnsense_Reticulum/os-reticulum
make package
```

This produces `os-reticulum-1.0.0.pkg` (or similar) in the current directory.

**If `make package` is not available:** The OPNsense plugin build toolchain requires the `opnsense-tools` repository. See the OPNsense developer documentation for the full build environment setup. As a fallback, install the plugin files directly from source (not recommended for reproducible testing).

---

## 7. Copy and Install the Package

```sh
# From workstation: copy to VM
scp os-reticulum-*.pkg root@<VM-LAN-IP>:/tmp/

# On VM: install
ssh root@<VM-LAN-IP>
pkg install /tmp/os-reticulum-*.pkg
```

Expected output during installation:
- Package files extracted to `/usr/local/opnsense/...`
- Post-install script runs: creates `reticulum` user, adds to `dialer` group
- Directories created: `/usr/local/etc/reticulum/`, `/usr/local/etc/lxmf/`, `/var/db/reticulum/`, `/var/db/lxmf/`, `/var/log/reticulum/`
- Python virtualenv created at `/usr/local/reticulum-venv/`
- Reticulum and LXMF installed from GitHub source into venv
- Installed versions recorded to `/var/db/reticulum/.pkg-versions`

**Note:** The `git clone` and `pip install` steps require internet access and may take 3–10 minutes depending on network speed.

---

## 8. Confirm Plugin Visible in GUI

1. Open `https://<VM-LAN-IP>` in a browser.
2. Navigate to **Services > Reticulum**.
3. Verify these menu items are present: **General**, **Interfaces**, **LXMF**, **Logs**.

If the menu is absent, the package install may have failed silently. Check `/var/log/opnsense.log` and confirm the Menu.xml is present:
```sh
ls /usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Menu/Menu.xml
```

---

## 9. Smoke Test Verification

Run the smoke test script immediately after installation to confirm all installation artifacts are in place. Run as root on the VM.

```sh
# Copy smoke test to VM (from workstation)
scp /path/to/os-reticulum/tests/service/smoke_test.sh root@<VM-LAN-IP>:/tmp/

# Run on VM
ssh root@<VM-LAN-IP> "sh /tmp/smoke_test.sh"
```

**Expected result:** All PASS lines, zero FAIL lines.

Key checks performed:
- `reticulum` user exists and is in the `dialer` group
- `rnsd` and `lxmd` binaries present in `/usr/local/reticulum-venv/bin/`
- Required directories exist with correct ownership
- Both services stopped (expected on fresh install)
- `configctl reticulum status.rnsd` action responds
- Template reload succeeds without error
- `Menu.xml` and model files present

If any check shows FAIL, do not proceed to functional tests. Investigate before continuing.

---

## 10. SSH Convenience Tip

Add the VM to `~/.ssh/config` on your workstation to avoid typing the IP repeatedly:

```
Host opnsense-test
    HostName <VM-LAN-IP>
    User root
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

Then use `ssh opnsense-test` and `scp file opnsense-test:/tmp/` for all subsequent commands.

`StrictHostKeyChecking no` is acceptable for a disposable test VM. Do not use this pattern for production systems.

---

## 11. What the Post-Install Script Creates

For reference, here is the complete set of artifacts created by `pkg-install`:

| Artifact | Path | Owner | Mode |
|----------|------|-------|------|
| Service user | `reticulum` | — | nologin shell |
| Config dir (rnsd) | `/usr/local/etc/reticulum/` | `reticulum` | 700 |
| Config dir (lxmf) | `/usr/local/etc/lxmf/` | `reticulum` | 700 |
| Runtime data (rnsd) | `/var/db/reticulum/` | `reticulum` | 700 |
| Runtime data (lxmf) | `/var/db/lxmf/` | `reticulum` | 700 |
| Log directory | `/var/log/reticulum/` | `reticulum` | 750 |
| Python venv | `/usr/local/reticulum-venv/` | root | — |
| rnsd binary | `/usr/local/reticulum-venv/bin/rnsd` | — | executable |
| lxmd binary | `/usr/local/reticulum-venv/bin/lxmd` | — | executable |
| Version record | `/var/db/reticulum/.pkg-versions` | `reticulum` | — |
| Source clone (rnsd) | `/usr/local/reticulum-src/reticulum/` | root | — |
| Source clone (lxmf) | `/usr/local/reticulum-src/lxmf/` | root | — |
