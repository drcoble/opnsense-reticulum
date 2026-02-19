# os-reticulum — OPNsense Reticulum Plugin

An OPNsense plugin that turns your firewall into a fully managed [Reticulum](https://reticulum.network/) transport node and [LXMF](https://github.com/markqvist/LXMF) propagation node, with complete GUI configuration, automatic firewall rules, and real-time diagnostics.

## Overview

[Reticulum](https://reticulum.network/) is a cryptography-based networking stack for building resilient, self-organizing local and wide-area networks. It uses X25519/Ed25519 elliptic curve cryptography for all communication and operates over diverse physical mediums — from Ethernet and WiFi to LoRa radio, packet radio, serial modems, and the I2P anonymous network.

This plugin integrates Reticulum into OPNsense's standard MVC framework, giving you full control through the web GUI without touching a config file.

### What It Does

- Runs the Reticulum daemon (`rnsd`) and LXMF propagation daemon (`lxmd`) as managed OPNsense services
- Provides GUI configuration for **all 9 Reticulum interface types**
- Automatically generates valid Reticulum and LXMF configuration files from your settings
- Automatically creates firewall allow rules for configured listener ports
- Provides real-time diagnostics: network status, path tables, announcements, interface statistics
- Exposes a full REST API for automation and scripting
- Supports OPNsense HA sync for high-availability deployments

### Two Node Roles

| Role | Daemon | Purpose |
|------|--------|---------|
| **Transport Node** | `rnsd` | Routes packets across hops, maintains path tables, propagates announcements — a router for the Reticulum network |
| **Propagation Node** | `lxmd` | Stores messages for offline recipients, synchronizes with peer nodes — a mail server for the Reticulum network |

## Screenshots

After installation, the plugin adds a **Services > Reticulum** section with five pages:

| Page | Description |
|------|-------------|
| **General** | Enable/disable Reticulum, transport mode, logging, instance settings |
| **Interfaces** | Add/edit/delete network interfaces (CRUD grid with type-specific fields) |
| **Transport** | Transport node best practices and configuration summary |
| **Propagation** | LXMF store-and-forward messaging settings with live status |
| **Diagnostics** | Real-time tabbed view of status, interfaces, paths, announces, propagation |

## Supported Interfaces

| Type | Medium | Use Case |
|------|--------|----------|
| **AutoInterface** | Ethernet / WiFi | Zero-config local peer discovery via IPv6 multicast |
| **UDPInterface** | IP network | Point-to-point or broadcast UDP communication |
| **TCPServerInterface** | IP network | Accept inbound TCP connections from remote nodes |
| **TCPClientInterface** | IP network | Connect outbound to remote Reticulum TCP servers |
| **RNodeInterface** | LoRa radio | Long-range radio via [RNode](https://unsigned.io/rnode/) hardware |
| **KISSInterface** | Packet radio | KISS-compatible TNCs and radio modems |
| **AX25KISSInterface** | Amateur radio | AX.25-framed packet radio (requires ham license) |
| **SerialInterface** | Serial / USB | Raw serial to data radios and modems |
| **I2PInterface** | I2P overlay | Anonymous communication over the Invisible Internet |

## Requirements

- OPNsense 24.1 or later
- Python 3.11 (included with OPNsense)
- `py311-cryptography` and `py311-serial` (installed automatically as package dependencies)
- Reticulum and LXMF are installed from the bundled upstream source at post-install time — no separate package required (see [Upstream Source & Updating](#upstream-source--updating))
- For LoRa: An [RNode](https://unsigned.io/rnode/) transceiver connected via USB
- For packet radio: A KISS-compatible TNC connected via serial
- For I2P: A running I2P router (i2pd or Java I2P) accessible from OPNsense

## Installation

### From the OPNsense GUI

1. Navigate to **System > Firmware > Plugins**
2. Search for `os-reticulum`
3. Click **+** to install
4. Navigate to **Services > Reticulum** to configure

### From the Command Line

```bash
pkg install os-reticulum
service configd restart
```

### From Source (Development)

> **Note:** git is not installed on OPNsense by default. Install it first:
> ```bash
> pkg install git
> ```

The repo uses git submodules for the upstream Reticulum and LXMF sources. Clone with `--recurse-submodules` to populate them:

```bash
git clone --recurse-submodules https://github.com/drcoble/opnsense-reticulum.git
cd opnsense-reticulum/net/reticulum
make install
service configd restart
```

If you already cloned without `--recurse-submodules`, initialise them afterwards:

```bash
git submodule update --init --recursive
```

## Quick Start

1. **Enable the service**: Services > Reticulum > General — check "Enable Reticulum", click Save, then Apply
2. **Add an interface**: Services > Reticulum > Interfaces — click **+**, set Name to "Local Network", Type to "AutoInterface", click Save, then Apply
3. **Verify**: Services > Reticulum > Diagnostics — the Status tab should show the daemon running

To enable transport routing, check "Enable Transport Node" on the General page. To enable message propagation, configure settings on the Propagation page.

## Project Structure

```
net/reticulum/
├── Makefile                              # Plugin build metadata + bundled version pins
├── pkg-descr                             # Package description
├── scripts/
│   └── update_upstream.sh               # Developer helper: update submodule pins
├── doc/
│   └── userguide.md                      # Comprehensive user guide
└── src/
    ├── +POST_INSTALL                     # Post-install: creates user/dirs, pip-installs RNS+LXMF
    ├── +POST_DEINSTALL                   # Post-deinstall: pip-uninstalls RNS+LXMF
    ├── usr/local/lib/
    │   ├── rns-src/                      # git submodule → markqvist/Reticulum (pinned tag)
    │   └── lxmf-src/                     # git submodule → markqvist/LXMF (pinned tag)
    ├── etc/inc/plugins.inc.d/
    │   └── reticulum.inc                 # OPNsense service hooks
    └── opnsense/
        ├── mvc/app/
        │   ├── controllers/OPNsense/Reticulum/
        │   │   ├── IndexController.php          # GUI page controller
        │   │   └── Api/
        │   │       ├── SettingsController.php    # Settings + interface CRUD API
        │   │       ├── ServiceController.php     # Service lifecycle API
        │   │       └── DiagnosticsController.php # Diagnostics API
        │   ├── models/OPNsense/Reticulum/
        │   │   ├── Reticulum.xml                # Data model (80+ fields)
        │   │   ├── Reticulum.php                # Model class
        │   │   ├── ACL/ACL.xml                  # Access control
        │   │   └── Menu/Menu.xml                # Sidebar navigation
        │   └── views/OPNsense/Reticulum/
        │       ├── general.volt                 # General settings view
        │       ├── interfaces.volt              # Interface CRUD grid view
        │       ├── transport.volt               # Transport settings view
        │       ├── propagation.volt             # Propagation settings view
        │       └── diagnostics.volt             # Diagnostics view
        ├── service/
        │   ├── templates/OPNsense/Reticulum/
        │   │   ├── reticulum.conf               # Jinja2 → Reticulum config
        │   │   ├── lxmd.conf                    # Jinja2 → LXMF config
        │   │   └── +TARGETS                     # Template output paths
        │   └── conf/actions.d/
        │       └── actions_reticulum.conf       # configd action definitions
        └── scripts/OPNsense/Reticulum/
            ├── setup.sh                         # Service start/stop/restart
            ├── status.py                        # JSON service status
            └── diagnostics.py                   # Diagnostics backend
```

## Upstream Source & Updating

Reticulum (RNS) and LXMF are not installed from the FreeBSD ports tree. Instead, their full source is bundled with this plugin as git submodules pinned to a specific upstream release tag:

| Submodule | Upstream repo | Installed at |
|-----------|--------------|--------------|
| `src/usr/local/lib/rns-src` | [markqvist/Reticulum](https://github.com/markqvist/Reticulum) | `/usr/local/lib/rns-src` |
| `src/usr/local/lib/lxmf-src` | [markqvist/LXMF](https://github.com/markqvist/LXMF) | `/usr/local/lib/lxmf-src` |

At plugin install time, `+POST_INSTALL` runs `pip install --no-deps` from those directories, which creates the `rnsd`, `lxmd`, `rnstatus`, `rnpath`, and other CLI tools in `/usr/local/bin/`. The only FreeBSD package dependencies are `py311-cryptography` and `py311-serial` — the compiled libraries that pip cannot build in this environment.

### Why this approach?

The FreeBSD `py311-rns` and `py311-lxmf` ports often lag several releases behind the upstream Python packages. Bundling the source directly ensures the plugin always ships a tested, known-good version of Reticulum without waiting for a port update.

### Updating to a new Reticulum release

Use the included helper script:

```bash
# See current pinned versions and available upstream tags
./scripts/update_upstream.sh

# Pin to the latest tag of each upstream repo
./scripts/update_upstream.sh --latest

# Or pin to specific versions
./scripts/update_upstream.sh 1.1.4 0.9.5
```

The script will:
1. Fetch the latest tags from both upstream repos
2. Check out the requested tag in each submodule
3. Update the `RNS_VERSION` and `LXMF_VERSION` lines in `Makefile`
4. Bump `PLUGIN_REVISION`
5. Stage all changes ready for review and commit

After running the script, review the diff, test on a live OPNsense instance, then commit and push:

```bash
git diff --cached
git commit -m "Update Reticulum to 1.1.4, LXMF to 0.9.5"
git push
```

## REST API

All endpoints require OPNsense API key authentication.

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reticulum/settings/get` | Get general settings |
| `POST` | `/api/reticulum/settings/set` | Update general settings |
| `GET` | `/api/reticulum/settings/getPropagation` | Get propagation settings |
| `POST` | `/api/reticulum/settings/setPropagation` | Update propagation settings |
| `GET` | `/api/reticulum/settings/searchInterface` | List all interfaces |
| `GET` | `/api/reticulum/settings/getInterface/{uuid}` | Get interface by UUID |
| `POST` | `/api/reticulum/settings/addInterface` | Add interface |
| `POST` | `/api/reticulum/settings/setInterface/{uuid}` | Update interface |
| `POST` | `/api/reticulum/settings/delInterface/{uuid}` | Delete interface |
| `POST` | `/api/reticulum/settings/toggleInterface/{uuid}` | Toggle interface |

### Service Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reticulum/service/start` | Start services |
| `POST` | `/api/reticulum/service/stop` | Stop services |
| `POST` | `/api/reticulum/service/restart` | Restart services |
| `POST` | `/api/reticulum/service/reconfigure` | Regenerate configs + restart |
| `GET` | `/api/reticulum/service/status` | Service status |

### Diagnostics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reticulum/diagnostics/rnstatus` | Reticulum daemon status |
| `GET` | `/api/reticulum/diagnostics/paths` | Path table |
| `GET` | `/api/reticulum/diagnostics/announces` | Recent announcements |
| `GET` | `/api/reticulum/diagnostics/propagation` | Propagation node status |
| `GET` | `/api/reticulum/diagnostics/interfaces` | Interface statistics |

### Example

```bash
# Check service status
curl -u "API_KEY:API_SECRET" https://opnsense.local/api/reticulum/service/status

# Add a TCP server interface
curl -u "API_KEY:API_SECRET" -X POST \
  -d '{"interface":{"enabled":"1","name":"WAN TCP","interfaceType":"TCPServerInterface","tcp_server_listen_port":"4242"}}' \
  https://opnsense.local/api/reticulum/settings/addInterface

# Apply configuration
curl -u "API_KEY:API_SECRET" -X POST \
  https://opnsense.local/api/reticulum/service/reconfigure
```

## Documentation

See the full **[User Guide](net/reticulum/doc/userguide.md)** for:

- Verbose explanations of every setting and what it does
- Per-interface-type configuration details with recommended values
- LoRa radio parameter tables (frequency bands, spreading factors, bandwidth vs. range)
- Transport node best practices
- Propagation node tuning
- 5 complete example configurations (local node, internet transport, LoRa gateway, full transport+propagation, anonymous I2P)
- Command-line administration reference
- Troubleshooting guide

## Architecture

The plugin follows OPNsense's standard MVC conventions:

- **Model** (`Reticulum.xml`): Defines 80+ fields with validation, defaults, and types. Uses a single `ArrayField` for all interface types with prefixed fields and JavaScript conditional visibility.
- **Controllers**: `ApiMutableModelControllerBase` for settings CRUD, `ApiMutableServiceControllerBase` for service lifecycle, custom `ApiControllerBase` for diagnostics.
- **Views** (Volt templates): Standard OPNsense form rendering with `base_form` partials, bootgrid CRUD for the interface list, and tabbed AJAX diagnostics.
- **Templates** (Jinja2): Generate valid Reticulum ConfigObj-format and LXMF config files with proper 2-space indentation.
- **Backend**: Shell script orchestrating both `rnsd` and `lxmd` daemons under a dedicated `_reticulum` service user. Python scripts for JSON status and diagnostics output via `configd`.
- **Hooks** (`reticulum.inc`): Service registration, dynamic firewall rule generation, syslog facility, and HA sync support.

## Security

- Both daemons run as a dedicated `_reticulum` user (not root) via privilege separation
- Configuration directories are owned by `_reticulum` with mode 750
- Serial device access is granted via the `dialer` group
- All Reticulum communication uses X25519/Ed25519 cryptography by default
- No source addresses are included in Reticulum packets (initiator anonymity)

## Related Projects

- [Reticulum](https://github.com/markqvist/Reticulum) — The Reticulum Network Stack
- [LXMF](https://github.com/markqvist/LXMF) — Lightweight Extensible Message Format
- [Sideband](https://github.com/markqvist/Sideband) — LXMF messaging client
- [NomadNet](https://github.com/markqvist/NomadNet) — Resilient terminal-based communication
- [RNode](https://unsigned.io/rnode/) — Open-platform LoRa transceiver hardware
- [OPNsense](https://opnsense.org/) — Open-source firewall and routing platform

## License

BSD 2-Clause License. See individual source files for details.

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

When contributing code, follow the [OPNsense plugin development conventions](https://docs.opnsense.org/development/examples/helloworld.html) and test on a live OPNsense instance before submitting.
