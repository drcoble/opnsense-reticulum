# os-reticulum — OPNsense Reticulum Plugin

> **This plugin is a work in progress and is not yet production-ready.**

An OPNsense plugin that turns your firewall into a fully managed [Reticulum](https://reticulum.network/) transport node and [LXMF](https://github.com/markqvist/LXMF) propagation node, with complete GUI configuration and real-time diagnostics.

## Overview

[Reticulum](https://reticulum.network/) is a cryptography-based networking stack for building resilient, self-organizing local and wide-area networks. It uses X25519/Ed25519 elliptic curve cryptography for all communication and operates over diverse physical mediums — Ethernet, WiFi, LoRa radio, packet radio, serial modems, and the I2P anonymous network.

This plugin integrates Reticulum into OPNsense's standard MVC framework, providing full control through the web GUI without editing config files directly.

---

## Installation from Source

### Prerequisites

| Requirement | Notes |
|---|---|
| OPNsense | 24.1 or later (FreeBSD 13-based) |
| `python311` | Installed automatically via `PLUGIN_DEPENDS` |
| `py311-cryptography` | Installed automatically |
| `py311-setuptools` | Installed automatically |
| `py311-wheel` | Installed automatically |
| `git` | Required during install to clone upstream sources; installed automatically |
| Internet access | Required on first install — `pkg-install` clones `Reticulum` and `LXMF` from GitHub |

The build system uses the OPNsense `plugins.mk` infrastructure, which must be present on the build host. The standard location is `Mk/plugins.mk` relative to the plugin directory (i.e., the plugin must live inside an OPNsense ports/plugins tree checkout).

### Pinned upstream versions

The install script clones and installs exact upstream tags. Current pins are in `src/usr/local/share/os-reticulum/versions.env`:

```
RNS_TAG=1.1.4
LXMF_TAG=0.9.3
```

These are installed into a dedicated virtualenv at `/usr/local/reticulum-venv/`.

---

### Option A — Build and install via `pkg` (recommended)

This is the standard OPNsense plugin workflow. Run these commands on the OPNsense firewall or a FreeBSD 13 build host with the OPNsense ports tree checked out.

**1. Clone this repository inside an OPNsense plugins tree.**

The plugin directory must be at a path where `../../Mk/plugins.mk` resolves correctly. The canonical location is `net/os-reticulum/` inside the `opnsense/plugins` repository:

```sh
git clone https://github.com/opnsense/plugins /path/to/plugins
cd /path/to/plugins/net/os-reticulum
```

Or clone this repository and create a compatible directory layout:

```sh
mkdir -p /path/to/build/Mk
# copy or symlink plugins.mk from an OPNsense ports tree into /path/to/build/Mk/
cp /path/to/plugins/Mk/plugins.mk /path/to/build/Mk/
git clone <this-repo> /path/to/build/net/os-reticulum
cd /path/to/build/net/os-reticulum
```

**2. Build the package.**

```sh
make package
```

This produces a `.pkg` file (FreeBSD package) in the local directory.

**3. Copy the package to the OPNsense firewall.**

```sh
scp os-reticulum-*.pkg root@<opnsense-ip>:/tmp/
```

**4. Install on the firewall.**

```sh
ssh root@<opnsense-ip>
pkg install /tmp/os-reticulum-*.pkg
```

`pkg-install` runs automatically during `pkg install`. It will:

- Check that `python3.11`, `git`, and `py311-setuptools` are available
- Create the `reticulum` service user (`/var/db/reticulum` home, `nologin` shell)
- Add `reticulum` to the `dialer` group (required for serial/USB interfaces)
- Create config and runtime directories with correct ownership and permissions
- Create or update the virtualenv at `/usr/local/reticulum-venv/`
- Clone `Reticulum` at `RNS_TAG` and `LXMF` at `LXMF_TAG` from GitHub into `/usr/local/reticulum-src/`
- Install both packages into the virtualenv via `pip`

**This step requires outbound internet access from the OPNsense host.**

---

### Option B — Install directly from source tree (development)

For development and testing, you can copy the source files directly without building a package. This requires either an OPNsense VM or a running OPNsense system you have SSH access to.

**1. Copy the source tree to the firewall.**

```sh
scp -r os-reticulum/src/* root@<opnsense-ip>:/
```

This places all files at their final installed paths under `/usr/local/`.

**2. Run `pkg-install` manually.**

```sh
ssh root@<opnsense-ip>
sh /path/to/os-reticulum/pkg-install
```

Or copy the install script first:

```sh
scp os-reticulum/pkg-install root@<opnsense-ip>:/tmp/pkg-install
ssh root@<opnsense-ip> sh /tmp/pkg-install
```

**3. Reload configd to pick up the new actions file.**

```sh
ssh root@<opnsense-ip>
service configd restart
```

**4. Fix script permissions.**

The configd action scripts must be executable:

```sh
chmod +x /usr/local/opnsense/scripts/OPNsense/Reticulum/*.sh
```

---

### Post-install steps

After installation (either method), complete the following steps from the OPNsense web GUI.

**1. Configure the transport node.**

Navigate to **Services → Reticulum → General** and configure at minimum:

- One or more interfaces (TCP, UDP, I2P, RNode, serial, etc.)
- Optionally enable the LXMF propagation node under **Services → Reticulum → LXMF**

**2. Start the services.**

From **Services → Reticulum → General**, click **Start** on the rnsd service bar.

If using LXMF propagation, start lxmd from **Services → Reticulum → LXMF** after rnsd is running. **lxmd requires rnsd to be running first** — the rc.d script enforces this dependency and will refuse to start if rnsd's pidfile is absent.

**3. Verify services are running.**

Check the dashboard widget (add "Reticulum" from the widget picker) or review log output under **Services → Reticulum → Logs**.

From the command line:

```sh
# Check rnsd
service rnsd status
cat /var/log/reticulum/rnsd.log

# Check lxmd
service lxmd status
cat /var/log/reticulum/lxmd.log
```

**4. (Optional) Enable services at boot.**

Services are started at boot via the syshook at `/usr/local/etc/rc.syshook.d/start/50-reticulum`, which regenerates config files from `config.xml`. Enable/disable is controlled through the GUI, which writes `rc.conf.d` fragments.

---

### Directory layout after installation

| Path | Purpose |
|---|---|
| `/usr/local/reticulum-venv/` | Python virtualenv containing `rnsd` and `lxmd` binaries |
| `/usr/local/reticulum-src/` | Cloned upstream sources (build artifact, removable) |
| `/usr/local/etc/reticulum/` | rnsd config and identity keys (mode 700, owned by `reticulum`) |
| `/usr/local/etc/reticulum/config` | Generated Reticulum config (written by configd template) |
| `/usr/local/etc/lxmf/` | lxmd config and identity keys (mode 700, owned by `reticulum`) |
| `/var/db/reticulum/` | rnsd runtime data (path tables, etc.) |
| `/var/db/lxmf/` | lxmd message storage |
| `/var/log/reticulum/` | `rnsd.log` and `lxmd.log` |
| `/var/run/rnsd.pid` | rnsd pidfile |
| `/var/run/lxmd.pid` | lxmd pidfile |
| `/usr/local/share/os-reticulum/versions.env` | Pinned upstream version tags |

---

### Uninstallation

```sh
pkg delete os-reticulum
```

`pkg-deinstall` runs automatically and will:

- Stop and disable both services
- Remove generated config files (`/usr/local/etc/reticulum/config`, `/usr/local/etc/lxmf/config`, `allowed`, `ignored`)
- Remove cloned source directories (`/usr/local/reticulum-src/`)

**The following are preserved for data safety and must be removed manually if desired:**

```
/usr/local/etc/reticulum/   (identity keys)
/usr/local/etc/lxmf/        (identity, stored messages)
/var/db/reticulum/
/var/db/lxmf/
/var/log/reticulum/
/usr/local/reticulum-venv/
```

---

### Troubleshooting

**`pkg-install` fails with "Could not reach GitHub"**

The install script clones from GitHub during installation. Ensure the OPNsense host has outbound internet access (port 443) and that DNS resolves `github.com`.

**`pkg-install` fails with "git: command not found"**

`git` is listed as a `PLUGIN_DEPENDS` dependency and should be installed automatically by `pkg`. If running `pkg-install` directly (not via `pkg install`), install it first:

```sh
pkg install git
```

**configd does not recognize new actions after a direct source install**

Restart configd after copying files:

```sh
service configd restart
```

**lxmd refuses to start**

lxmd's rc.d script checks for a running rnsd pidfile before starting. Start rnsd first and confirm it is healthy:

```sh
service rnsd onestart
cat /var/run/rnsd.pid   # must exist
service lxmd onestart
```

**Services show as stopped in the GUI but processes are running**

The plugin uses direct pidfile + PID checks for status (`/var/run/rnsd.pid`, `/var/run/lxmd.pid`) rather than `service X status`, because `rc.subr check_pidfile` is unreliable for Python daemons. If the GUI shows stale state, verify the pidfile is present and the PID is live:

```sh
kill -0 $(cat /var/run/rnsd.pid) && echo "running" || echo "not running"
```
