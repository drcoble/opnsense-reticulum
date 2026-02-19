# OPNsense Reticulum Plugin User Guide

## Table of Contents

1. [Introduction](#1-introduction)
2. [Prerequisites](#2-prerequisites)
3. [Installation](#3-installation)
   - [Updating Reticulum](#updating-reticulum)
4. [Quick Start](#4-quick-start)
5. [General Settings](#5-general-settings)
6. [Interfaces](#6-interfaces)
   - [Common Interface Settings](#61-common-interface-settings)
   - [AutoInterface](#62-autointerface)
   - [UDPInterface](#63-udpinterface)
   - [TCPServerInterface](#64-tcpserverinterface)
   - [TCPClientInterface](#65-tcpclientinterface)
   - [RNodeInterface (LoRa)](#66-rnodeinterface-lora)
   - [KISSInterface](#67-kissinterface)
   - [AX25KISSInterface](#68-ax25kissinterface)
   - [SerialInterface](#69-serialinterface)
   - [I2PInterface](#610-i2pinterface)
7. [Transport Node](#7-transport-node)
8. [Propagation Node (LXMF)](#8-propagation-node-lxmf)
9. [Diagnostics](#9-diagnostics)
10. [Firewall Integration](#10-firewall-integration)
11. [REST API Reference](#11-rest-api-reference)
12. [Command-Line Administration](#12-command-line-administration)
13. [Troubleshooting](#13-troubleshooting)
14. [Example Configurations](#14-example-configurations)

---

## 1. Introduction

The OPNsense Reticulum plugin (`os-reticulum`) provides a full graphical interface for operating a Reticulum transport node and LXMF propagation node on your OPNsense firewall or router.

**Reticulum** is a cryptography-based networking stack for building resilient local and wide-area networks. It uses X25519/Ed25519 elliptic curve cryptography for all communication and can operate over diverse physical mediums including Ethernet, WiFi, LoRa radio, packet radio, serial links, and the I2P anonymous network. Reticulum is designed for self-organizing, coordination-free networking and can function at bandwidths as low as 150 bits per second.

**What this plugin does:**

- Runs the Reticulum network daemon (`rnsd`) as a managed OPNsense service
- Optionally runs the LXMF propagation daemon (`lxmd`) for store-and-forward messaging
- Provides GUI configuration for all 9 supported Reticulum interface types
- Automatically generates valid Reticulum and LXMF configuration files
- Automatically creates firewall rules for configured listener ports
- Provides real-time diagnostics for network status, paths, and announcements
- Exposes a full REST API for automation and scripting

**Two key roles this plugin enables:**

- **Transport Node**: Your OPNsense device forwards Reticulum packets across network hops, maintains routing path tables, and propagates announcements. Think of it as a router for the Reticulum network.
- **Propagation Node**: Your OPNsense device stores LXMF messages for offline recipients and synchronizes with other propagation nodes. Think of it as a mail server for the Reticulum network.

---

## 2. Prerequisites

### Hardware Requirements

- An OPNsense firewall/router (bare-metal or virtual machine)
- For LoRa radio: An RNode device (see https://unsigned.io/rnode/) connected via USB
- For packet radio: A KISS-compatible TNC connected via serial
- For serial modems: A compatible data radio or modem connected via serial/USB

### Software Requirements

- OPNsense 24.1 or later
- Python 3.11 (included with OPNsense)
- The following packages are installed automatically as pkg dependencies:
  - `py311-cryptography` (compiled cryptography library required by Reticulum)
  - `py311-serial` (PySerial, required for RNode, KISS, AX.25, and Serial interfaces)
- Reticulum (RNS) and LXMF are **not** installed from the FreeBSD ports tree. They are bundled directly as upstream source and installed via pip at plugin install time. See [Updating Reticulum](#updating-reticulum) for details.

### Network Requirements

- For TCP interfaces: A routable IP address and appropriate port forwarding if behind NAT
- For UDP interfaces: Network connectivity to the target peer(s)
- For AutoInterface: At least one Ethernet or WiFi interface on the local network
- For I2P interfaces: A running I2P router (i2pd or Java I2P) on the OPNsense host or local network

---

## 3. Installation

### Method 1: OPNsense Web GUI (Recommended)

1. Log into your OPNsense web interface
2. Navigate to **System > Firmware > Plugins**
3. Search for `os-reticulum`
4. Click the **+** button to install
5. Wait for installation to complete
6. The page may prompt you to reload — click **Reload** if asked
7. Navigate to **Services > Reticulum** to begin configuration

### Method 2: Command Line

SSH into your OPNsense device and run:

```bash
pkg install os-reticulum
```

After installation, restart the configuration daemon to register the new service:

```bash
service configd restart
```

### Method 3: Manual Build from Source

If you are developing or testing from the plugin source code, clone with `--recurse-submodules` to populate the bundled Reticulum and LXMF source trees:

```bash
git clone --recurse-submodules https://github.com/drcoble/opnsense-reticulum.git
cd opnsense-reticulum/net/reticulum
make install
service configd restart
```

If you already have a clone without the submodules, initialise them first:

```bash
git submodule update --init --recursive
```

### Post-Installation

The installer automatically:

- Installs Reticulum (RNS) from the bundled source at `/usr/local/lib/rns-src/` via `pip install --no-deps`
- Installs LXMF from the bundled source at `/usr/local/lib/lxmf-src/` via `pip install --no-deps`
- Creates the `rnsd`, `lxmd`, `rnstatus`, `rnpath`, and other CLI tools in `/usr/local/bin/`
- Creates a dedicated `_reticulum` service user and group (UID/GID 920)
- Creates configuration directories at `/usr/local/etc/reticulum/` and `/usr/local/etc/lxmd/`
- Creates the message store directory at `/var/db/lxmd/messagestore/`
- Creates a log directory at `/var/log/reticulum/`
- Adds the service user to the `dialer` group for serial device access
- Sets restrictive ownership and permissions on all directories

To verify the installed versions after installation:

```bash
python3.11 -m pip show rns lxmf
```

### Uninstallation

Via the GUI: **System > Firmware > Plugins**, find `os-reticulum`, and click the **-** button.

Via the command line:

```bash
pkg remove os-reticulum
```

The post-deinstall script automatically removes the pip-installed `rns` and `lxmf` packages. However, it does not remove the `_reticulum` user, configuration directories, or stored messages. To fully clean up:

```bash
pw userdel _reticulum
pw groupdel _reticulum
rm -rf /usr/local/etc/reticulum /usr/local/etc/lxmd /var/db/lxmd /var/log/reticulum
```

### Updating Reticulum

Because Reticulum and LXMF are installed from source bundled with the plugin (rather than from the FreeBSD ports tree), updates are delivered as plugin package updates rather than `pkg upgrade`.

**As a user**: install the latest `os-reticulum` plugin update from **System > Firmware > Plugins** whenever it is available. Each plugin update pins to a tested Reticulum and LXMF release.

**As a developer/contributor**: use the included helper script to update the bundled source to a new upstream release:

```bash
# Show current pinned versions and available upstream tags
./scripts/update_upstream.sh

# Pin to the latest tag of each upstream repo
./scripts/update_upstream.sh --latest

# Or pin to specific versions
./scripts/update_upstream.sh 1.1.4 0.9.5
```

The script updates the git submodules (`src/usr/local/lib/rns-src` and `src/usr/local/lib/lxmf-src`), bumps the version strings in `Makefile`, and stages everything ready for review. After testing on a live OPNsense instance, commit and push to release a new plugin version.

The bundled upstream source versions are always visible in the plugin `Makefile`:

```makefile
RNS_VERSION=    1.1.3
LXMF_VERSION=   0.9.4
```

---

## 4. Quick Start

This section walks you through getting a basic Reticulum node running in under 5 minutes.

### Step 1: Enable the Service

1. Navigate to **Services > Reticulum > General**
2. Check **Enable Reticulum**
3. Leave all other settings at their defaults
4. Click **Save**, then click **Apply**

### Step 2: Add an Interface

1. Navigate to **Services > Reticulum > Interfaces**
2. Click the **+** button to add a new interface
3. Set the following:
   - **Name**: `Local Network`
   - **Interface Type**: `AutoInterface`
   - Leave all other fields at their defaults
4. Click **Save**
5. Click **Apply**

Your OPNsense device will now automatically discover and communicate with other Reticulum peers on your local network using IPv6 link-local multicast.

### Step 3 (Optional): Enable Transport Mode

If you want your OPNsense device to route traffic for other Reticulum peers:

1. Navigate to **Services > Reticulum > General**
2. Check **Enable Transport Node**
3. Click **Save**, then click **Apply**

### Step 4: Verify

1. Navigate to **Services > Reticulum > Diagnostics**
2. The **Status** tab should show Reticulum as running
3. The **Interfaces** tab should show your configured interface(s) as active

---

## 5. General Settings

Navigate to: **Services > Reticulum > General**

These settings control the core behavior of the Reticulum daemon.

### Enable Reticulum

| | |
|---|---|
| **Field** | Enable Reticulum |
| **Default** | Unchecked (disabled) |
| **Config key** | `general.enabled` |

Master switch for the Reticulum network daemon (`rnsd`). When enabled and applied, the daemon starts automatically and runs as a background service under the `_reticulum` user. When disabled and applied, the daemon is stopped.

The Reticulum daemon must be enabled before any interfaces will function and before the propagation node can start.

### Enable Transport Node

| | |
|---|---|
| **Field** | Enable Transport Node |
| **Default** | Unchecked (disabled) |
| **Config key** | `enable_transport` |

When enabled, your OPNsense device becomes a Reticulum transport node. This means it will:

- **Forward packets** for other peers across multiple network hops
- **Maintain a path table** of known destinations and their routes
- **Propagate announcements** from other nodes across all connected interfaces
- **Serve path requests** so other nodes can discover routes to destinations
- **Cache public keys** from announcements, acting as a distributed cryptographic keystore

**When to enable this:**

- Your OPNsense device sits at a strategic point connecting two or more network segments (for example, bridging a LoRa radio network to a TCP-connected backbone)
- Your device is stationary, always-on, and has stable connectivity
- The network needs a routing node at this location for reliable packet delivery

**When NOT to enable this:**

- You only want to send and receive your own traffic (leave disabled for a standard Reticulum node)
- Your device is mobile or frequently disconnects
- There are already sufficient transport nodes covering your area of the network

**Important**: Not every Reticulum node should be a transport node. Having too many transport nodes on a network degrades performance due to increased resource consumption, bandwidth overhead, and route convergence delays. Only enable transport mode on devices that genuinely provide connectivity between network segments.

### Share Instance

| | |
|---|---|
| **Field** | Share Instance |
| **Default** | Checked (enabled) |
| **Config key** | `share_instance` |
| **Visibility** | Advanced |

When enabled, multiple programs on the same OPNsense device can share a single Reticulum instance through a local TCP socket. This avoids each program needing its own network interfaces and allows applications like Sideband, NomadNet, or custom scripts to use the daemon's interfaces.

If you are running the Reticulum daemon solely as a transport/propagation node with no other local Reticulum applications, you can safely leave this enabled (it has no negative impact). Disabling it would only be necessary if you need complete isolation between Reticulum instances on the same machine.

### Shared Instance Port

| | |
|---|---|
| **Field** | Shared Instance Port |
| **Default** | `37428` |
| **Config key** | `shared_instance_port` |
| **Visibility** | Advanced |

The TCP port used for local inter-process communication between the Reticulum daemon and other programs sharing the instance. This port only listens on localhost (127.0.0.1) and is not exposed to the network.

You only need to change this if you are running multiple isolated Reticulum instances on the same machine and need to avoid port conflicts. In virtually all deployments, the default value is correct.

### Instance Control Port

| | |
|---|---|
| **Field** | Instance Control Port |
| **Default** | `37429` |
| **Config key** | `instance_control_port` |
| **Visibility** | Advanced |

The TCP port used for control operations such as querying status and managing the running instance. Like the shared instance port, this only listens on localhost.

Change this only if running multiple isolated Reticulum instances. The default value is correct for virtually all deployments.

### Panic on Interface Error

| | |
|---|---|
| **Field** | Panic on Interface Error |
| **Default** | Unchecked (disabled) |
| **Config key** | `panic_on_interface_error` |
| **Visibility** | Advanced |

When enabled, the Reticulum daemon will immediately terminate if any configured interface fails to initialize during startup. This is useful in environments where every interface is critical and you want the daemon to fail loudly rather than running in a degraded state.

When disabled (the default), the daemon will log errors for failed interfaces but continue running with whatever interfaces did initialize successfully. This is the recommended behavior for most deployments, as it provides resilience — a temporarily disconnected serial device or unavailable TCP peer will not prevent the rest of the network from functioning.

**Recommended setting**: Leave disabled unless you are running a critical infrastructure node where partial operation is worse than no operation.

### Log Level

| | |
|---|---|
| **Field** | Log Level |
| **Default** | `4 - Notice` |
| **Config key** | `loglevel` |

Controls the verbosity of the Reticulum daemon's logging output. Logs are written to syslog under the `reticulum` facility and can be viewed at **System > Log Files** or via the Diagnostics page.

| Level | Name | Description |
|-------|------|-------------|
| 0 | None | No logging output at all |
| 1 | Critical | Only fatal errors that prevent operation |
| 2 | Error | Errors that indicate something went wrong but the daemon continues |
| 3 | Warning | Potential issues that may warrant attention |
| 4 | Notice | Normal operational events (interface up/down, connections established). **Recommended for normal use.** |
| 5 | Info | Detailed informational messages about daemon operations |
| 6 | Verbose | Very detailed output including packet-level information |
| 7 | Debug | Maximum verbosity — all internal operations logged. **Use only for troubleshooting.** Generates significant log volume. |

**Recommended setting**: `4 - Notice` for normal operation. Temporarily increase to `6 - Verbose` or `7 - Debug` when troubleshooting connectivity issues, then reduce back to avoid filling log storage.

---

## 6. Interfaces

Navigate to: **Services > Reticulum > Interfaces**

This page provides a grid for adding, editing, deleting, and toggling Reticulum network interfaces. Each interface represents a communication channel that Reticulum uses to send and receive data.

You can configure multiple interfaces simultaneously. For example, a transport node might have:
- An AutoInterface for local Ethernet/WiFi peer discovery
- A TCPServerInterface to accept connections from remote nodes over the internet
- An RNodeInterface for LoRa radio communication

When you add or edit an interface, a dialog appears with fields specific to the selected interface type. Only relevant fields are shown — selecting "RNodeInterface" shows LoRa radio parameters, selecting "TCPServerInterface" shows TCP listener parameters, and so on.

After making changes, click **Apply** to regenerate the Reticulum configuration file and restart the daemon.

### 6.1 Common Interface Settings

These settings appear for all interface types.

#### Enabled

| | |
|---|---|
| **Default** | Checked |

Enables or disables this individual interface. Disabled interfaces are not included in the generated Reticulum configuration file. Use the toggle button in the grid to quickly enable/disable interfaces without opening the edit dialog.

#### Name

| | |
|---|---|
| **Default** | (none — required) |
| **Validation** | Letters, numbers, spaces, hyphens, underscores |

A descriptive name for this interface. This name is used as the section header in the Reticulum configuration file and appears in diagnostics output. Choose something meaningful like "LoRa 868 MHz", "WAN TCP Server", or "LAN Auto Discovery".

Each interface name must be unique within your configuration.

#### Interface Type

| | |
|---|---|
| **Default** | (none — required) |

Selects the kind of interface to configure. The available types are:

| Type | Use Case |
|------|----------|
| **AutoInterface** | Automatic peer discovery on local Ethernet/WiFi networks via IPv6 multicast |
| **UDPInterface** | Point-to-point or broadcast communication over UDP |
| **TCPServerInterface** | Accept incoming TCP connections from remote Reticulum nodes |
| **TCPClientInterface** | Connect outbound to a remote Reticulum TCP server |
| **RNodeInterface** | LoRa radio communication via an RNode hardware transceiver |
| **KISSInterface** | Packet radio via a KISS-compatible Terminal Node Controller (TNC) |
| **AX25KISSInterface** | AX.25-encapsulated packet radio via a KISS TNC (amateur radio) |
| **SerialInterface** | Raw serial communication to data radios and modems |
| **I2PInterface** | Anonymous communication over the Invisible Internet Protocol (I2P) overlay network |

Selecting a type dynamically shows only the fields relevant to that interface type.

#### Interface Mode

| | |
|---|---|
| **Default** | Default (full) |
| **Visibility** | Advanced |

Controls how Reticulum handles traffic on this particular interface. The mode affects announcement propagation and routing behavior.

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Full** | Default mode with full routing capabilities. Announcements are propagated normally. | Most interfaces. Use this unless you have a specific reason to choose another mode. |
| **Gateway** | The interface connects to a network segment containing only non-transport (client) nodes. The transport node will serve as the gateway for those clients to reach the wider network. | When this interface faces a leaf network of endpoint devices that don't participate in routing. |
| **Boundary** | The interface connects two significantly different network segments (e.g., a slow LoRa link connecting to a fast Ethernet backbone). Reticulum adjusts announcement handling to account for the asymmetry. | When bridging between networks with very different bandwidth, latency, or reliability characteristics. |
| **Access Point** | The interface serves as a wide-area radio access point. Reticulum optimizes for serving transient, mobile users who come and go. | For LoRa or radio interfaces covering a large area where users connect temporarily (like a hilltop relay). |
| **Roaming** | The interface itself is mobile and may frequently change its network location. Reticulum adapts routing accordingly. | For interfaces on mobile devices or vehicles that move between different network segments. |

#### Outgoing

| | |
|---|---|
| **Default** | Checked (enabled) |
| **Visibility** | Advanced |

When enabled, Reticulum can send outbound traffic through this interface. When disabled, the interface is receive-only. This is useful for creating listen-only monitoring interfaces or for asymmetric setups where traffic should only flow in one direction.

#### Bitrate Override

| | |
|---|---|
| **Default** | (empty — auto-detect) |
| **Visibility** | Advanced |

Manually specifies the bitrate (in bits per second) of this interface. Reticulum normally auto-detects the bitrate for each interface type, but in some cases (custom serial modems, non-standard configurations) you may need to override it.

The bitrate information is used by Reticulum to make intelligent decisions about announcement timing and bandwidth allocation. Setting an incorrect bitrate can cause suboptimal performance.

Leave this empty unless you know the actual bitrate differs from what Reticulum auto-detects.

#### Announce Rate Target

| | |
|---|---|
| **Default** | (empty — use Reticulum default) |
| **Visibility** | Advanced |

The target time in seconds between announcements on this interface. Reticulum uses a bandwidth allocation system where a configurable percentage of each interface's bandwidth (default 2%) is reserved for announcements. This setting overrides the default calculation.

Setting a higher value reduces announcement traffic on bandwidth-constrained interfaces (like LoRa). Setting a lower value allows more frequent announcements on high-bandwidth interfaces.

**Example**: On a LoRa interface with limited bandwidth, you might set this to `600` (10 minutes) to limit announcement frequency. On a fast Ethernet interface, you might leave it empty to let Reticulum calculate the optimal rate.

#### Announce Rate Grace

| | |
|---|---|
| **Default** | (empty — use Reticulum default) |
| **Visibility** | Advanced |

The number of announcements a destination is allowed to make before rate limiting activates. This provides a grace period for new destinations or destinations that need to announce frequently during initial setup.

After this many announcements within the rate target window, subsequent announcements from the same destination are subject to the announce rate penalty.

#### Announce Rate Penalty

| | |
|---|---|
| **Default** | (empty — use Reticulum default) |
| **Visibility** | Advanced |

A multiplier applied to the announce rate target when a destination exceeds its allowed announcement rate. This progressively slows down destinations that announce too frequently, preventing any single destination from consuming excessive bandwidth.

For example, with a target of 300 seconds, a grace of 5, and a penalty of 2: a destination can announce 5 times within 300 seconds. After the 5th announce, the next allowed announce interval doubles to 600 seconds, then 1200 seconds, and so on until the destination reduces its announce rate.

---

### 6.2 AutoInterface

The AutoInterface provides zero-configuration peer discovery on local Ethernet and WiFi networks using IPv6 link-local multicast. This is the easiest way to connect Reticulum nodes on the same LAN segment — all nodes with AutoInterface enabled and the same group ID will automatically discover each other.

No IP infrastructure (DHCP, DNS, routers) is required. AutoInterface operates at the link-local level.

#### Group ID

| | |
|---|---|
| **Default** | `reticulum` |

A string identifier that groups Reticulum peers for discovery. Only nodes with the same group ID will discover and communicate with each other. This allows multiple independent Reticulum networks to coexist on the same physical LAN without interfering.

**Example**: If you have a production Reticulum network and a test network, you could use group IDs `production` and `testing` to keep them separate.

Leave at the default `reticulum` to be compatible with other standard Reticulum installations.

#### Discovery Scope

| | |
|---|---|
| **Default** | `Link` |

Controls the IPv6 multicast scope used for peer discovery. This determines how far discovery packets travel:

| Scope | Range | Description |
|-------|-------|-------------|
| **Link** | Same LAN segment | Packets never cross a router. Suitable for single-subnet deployments. This is the safest and most common choice. |
| **Admin** | Administrative domain | Slightly wider scope, but still typically confined to a managed network segment. |
| **Site** | Single site/campus | Packets can traverse routers within a single physical site. Requires multicast routing support. |
| **Organization** | Entire organization | Packets can traverse the organization's entire internal network. Requires multicast routing support. |
| **Global** | Unrestricted | No scope restriction. Generally not recommended for discovery traffic. |

**Recommended setting**: `Link` for most deployments. Only increase the scope if you specifically need cross-subnet discovery and have multicast routing configured.

#### Discovery Port

| | |
|---|---|
| **Default** | `29716` |

The UDP port used for sending and receiving peer discovery multicast packets. All nodes in the same group must use the same discovery port.

Change this only if the default port conflicts with another service or if you need to run multiple AutoInterface instances with different group IDs on different ports.

A firewall rule is automatically created for this port.

#### Data Port

| | |
|---|---|
| **Default** | `42671` |

The UDP port used for actual data transfer between discovered peers. After two nodes discover each other via the discovery port, they communicate data on this port.

Change this only if the default port conflicts with another service.

A firewall rule is automatically created for this port.

#### Allowed Interfaces

| | |
|---|---|
| **Default** | (empty — all interfaces) |

A comma-separated list of operating system network interface names that AutoInterface should use for discovery. When empty, Reticulum will use all available Ethernet and WiFi interfaces.

**Example**: `igb0,igb1` to restrict discovery to only the `igb0` and `igb1` interfaces.

Use this to limit discovery to specific network segments. On an OPNsense device with multiple interfaces (LAN, WAN, OPT1, etc.), you typically want discovery only on your internal/LAN interfaces, not on the WAN.

To find your interface names, check **Interfaces > Assignments** in OPNsense or run `ifconfig` on the command line.

#### Ignored Interfaces

| | |
|---|---|
| **Default** | (empty — ignore none) |

A comma-separated list of operating system network interface names to exclude from AutoInterface discovery. This is the inverse of "Allowed Interfaces" — rather than specifying which interfaces to use, you specify which ones to skip.

**Example**: `em0,lo0` to prevent discovery on the `em0` and `lo0` interfaces.

If both Allowed Interfaces and Ignored Interfaces are specified, Allowed Interfaces takes precedence.

---

### 6.3 UDPInterface

The UDPInterface sends and receives Reticulum traffic over UDP packets. It can operate in point-to-point mode (communicating with a specific remote peer) or broadcast mode (communicating with all peers on a local network segment).

UDP is connectionless, which makes this interface type lightweight but also means there is no automatic reconnection if a peer goes offline.

#### Listen IP

| | |
|---|---|
| **Default** | `0.0.0.0` |

The IP address to listen on for incoming UDP packets. Use `0.0.0.0` to listen on all available interfaces, or specify a specific IP address to restrict listening to a single interface.

#### Listen Port

| | |
|---|---|
| **Default** | `4242` |

The UDP port to listen on for incoming Reticulum packets. A firewall rule is automatically created for this port.

#### Forward IP

| | |
|---|---|
| **Default** | (empty) |

The IP address of a remote Reticulum peer to send outbound packets to. When set, the interface operates in point-to-point mode, forwarding all outbound traffic to this specific peer.

Leave empty for listen-only or broadcast mode.

#### Forward Port

| | |
|---|---|
| **Default** | (empty) |

The UDP port of the remote peer specified in Forward IP.

#### Broadcast Mode

| | |
|---|---|
| **Default** | Unchecked (disabled) |

When enabled, the interface sends outbound traffic as UDP broadcasts on the local network segment instead of to a specific peer. This allows multiple nodes on the same LAN to communicate without needing to configure specific peer addresses.

Note: UDP broadcast on WiFi networks can cause performance issues due to the way WiFi handles broadcast frames (they are sent at the lowest data rate). On WiFi networks, AutoInterface is generally a better choice.

---

### 6.4 TCPServerInterface

The TCPServerInterface creates a TCP listener that accepts incoming connections from remote Reticulum nodes. This is the primary way to provide connectivity to nodes across the internet or between different network locations.

TCP provides reliable, ordered delivery and automatic reconnection, making it suitable for long-distance links over the internet.

#### Listen IP

| | |
|---|---|
| **Default** | `0.0.0.0` |

The IP address to bind the TCP listener on. Use `0.0.0.0` to listen on all available interfaces, or specify a specific IP to restrict the listener to a single interface.

For a public-facing transport node, use `0.0.0.0` and ensure your WAN firewall rules allow inbound TCP on the listen port (the plugin creates this rule automatically).

#### Listen Port

| | |
|---|---|
| **Default** | `4242` |

The TCP port to listen on for incoming Reticulum connections. A firewall rule is automatically created for this port.

Choose a port that is not blocked by your ISP or upstream firewall. Common choices include `4242` (the Reticulum convention), `443`, or `8443`.

#### I2P Tunneled

| | |
|---|---|
| **Default** | Unchecked (disabled) |

Enable this if the TCP listener is accessible via an I2P tunnel. This informs Reticulum that the listener's real network address is an I2P hidden service, which affects how the interface handles connections and addresses.

Only enable this if you have specifically configured an I2P tunnel pointing to this TCP listener.

---

### 6.5 TCPClientInterface

The TCPClientInterface makes an outbound TCP connection to a remote Reticulum node that is running a TCPServerInterface. Reticulum automatically handles reconnection if the connection drops.

This is how most nodes connect to remote transport nodes over the internet.

#### Target Host

| | |
|---|---|
| **Default** | (empty — required) |

The hostname, FQDN, or IP address of the remote Reticulum TCP server to connect to.

**Examples**: `reticulum.example.com`, `192.168.1.100`, `rns.mynode.org`

#### Target Port

| | |
|---|---|
| **Default** | `4242` |

The TCP port of the remote server. Must match the Listen Port configured on the remote server's TCPServerInterface.

#### KISS Framing Bytes

| | |
|---|---|
| **Default** | (empty) |

Used when connecting to a KISS TNC that is accessible over TCP (rather than a direct serial connection). Specifies the number of KISS framing bytes expected by the remote TNC.

Leave empty for standard Reticulum TCP connections. Only set this if you are connecting to a TCP-to-serial bridge that terminates on a KISS TNC.

#### I2P Tunneled

| | |
|---|---|
| **Default** | Unchecked (disabled) |

Enable this if the TCP connection goes through an I2P tunnel. This tells Reticulum that the target host is an I2P hidden service address, which affects connection handling.

---

### 6.6 RNodeInterface (LoRa)

The RNodeInterface communicates over LoRa radio using an RNode hardware transceiver. RNodes are open-platform LoRa devices that can be built from inexpensive hardware or purchased pre-made (see https://unsigned.io/rnode/).

LoRa provides long-range, low-bandwidth communication ideal for off-grid, emergency, and rural networking. A single RNode can communicate over distances of several kilometers (line-of-sight) to tens of kilometers (with high-gain antennas).

#### Serial Port

| | |
|---|---|
| **Default** | `/dev/ttyUSB0` |

The serial device path for the RNode hardware. On FreeBSD/OPNsense, USB serial devices typically appear as `/dev/cuaU0`, `/dev/cuaU1`, etc. Linux-style paths like `/dev/ttyUSB0` may also work depending on your USB serial driver.

To find the correct device path, connect the RNode and check dmesg output or list `/dev/cua*` devices.

#### Frequency (Hz)

| | |
|---|---|
| **Default** | `868000000` (868 MHz) |
| **Valid range** | 100,000,000 - 1,000,000,000 (100 MHz - 1 GHz) |

The radio frequency in Hertz. Common frequency bands used with Reticulum:

| Region | Band | Frequency | Notes |
|--------|------|-----------|-------|
| Europe | 868 MHz ISM | `868000000` | Default. Up to 25 mW ERP in most EU countries. |
| Americas | 915 MHz ISM | `915000000` | Up to 1 W in the US (FCC Part 15). |
| Americas | 902 MHz ISM | `902000000` | Alternative US frequency. |
| Global | 433 MHz ISM | `433000000` | Lower frequency = longer range but lower bandwidth. |

**Important**: You are responsible for compliance with your local radio frequency regulations. Transmitting on unauthorized frequencies or at excessive power levels may violate local laws.

#### Bandwidth

| | |
|---|---|
| **Default** | `125 kHz` |

The LoRa channel bandwidth. This directly affects both data rate and range:

| Bandwidth | Data Rate | Range | Use Case |
|-----------|-----------|-------|----------|
| 7.8 kHz | Lowest | Maximum | Extreme long range, very low data rate |
| 10.4 kHz | Very low | Very long | Long range links |
| 15.6 kHz | Very low | Very long | Long range links |
| 20.8 kHz | Low | Long | Medium-distance links |
| 31.25 kHz | Low | Long | Medium-distance links |
| 41.7 kHz | Moderate | Moderate | Balanced links |
| 62.5 kHz | Moderate | Moderate | Balanced links |
| **125 kHz** | **Good** | **Good** | **General purpose — recommended starting point** |
| 250 kHz | High | Short | Short-range, higher throughput |
| 500 kHz | Highest | Shortest | Maximum throughput, shortest range |

#### TX Power (dBm)

| | |
|---|---|
| **Default** | `7` |
| **Valid range** | 0 - 22 |

Transmit power in decibels relative to one milliwatt (dBm). Higher values increase range but consume more power and may exceed legal limits.

| dBm | Milliwatts | Notes |
|-----|-----------|-------|
| 0 | 1 mW | Minimum power |
| 7 | 5 mW | Default — conservative, suitable for short/medium range |
| 10 | 10 mW | Moderate power |
| 14 | 25 mW | EU 868 MHz ISM limit (typical) |
| 17 | 50 mW | Higher power |
| 20 | 100 mW | High power |
| 22 | 158 mW | Maximum supported by most modules |

**Important**: Ensure your TX power setting complies with local regulations for the frequency band you are using. The legal maximum varies by country and frequency.

#### Spreading Factor

| | |
|---|---|
| **Default** | `SF7` |

The LoRa spreading factor controls the trade-off between range/robustness and data rate:

| Spreading Factor | Data Rate | Range | Noise Immunity |
|-----------------|-----------|-------|----------------|
| **SF7** | Highest | Shortest | Lowest — **best for short/medium range** |
| SF8 | High | Short-medium | Low |
| SF9 | Moderate | Medium | Moderate |
| SF10 | Low | Long | Good |
| SF11 | Very low | Very long | Very good |
| SF12 | Lowest | Maximum | Maximum — **best for extreme range** |

Each step up in spreading factor approximately doubles the time-on-air (and halves the data rate) while increasing the receiver sensitivity by about 2.5 dB.

**Recommendation**: Start with SF7. Increase only if you need more range or are experiencing packet loss. All nodes communicating on the same link must use the same spreading factor.

#### Coding Rate

| | |
|---|---|
| **Default** | `4/5` |

The LoRa forward error correction (FEC) coding rate. Higher coding rates add more redundancy to each packet, improving reliability in noisy environments at the cost of lower effective data rate:

| Coding Rate | Overhead | Robustness | Data Rate Impact |
|-------------|----------|------------|-----------------|
| **4/5** | 25% | Lowest | Highest throughput — **recommended for most use** |
| 4/6 | 50% | Moderate | Moderate throughput |
| 4/7 | 75% | Good | Lower throughput |
| 4/8 | 100% | Maximum | Lowest throughput — use in very noisy environments |

#### RNode ID

| | |
|---|---|
| **Default** | (empty) |
| **Visibility** | Advanced |

A numeric identifier used when multiple RNode devices are connected to the same Reticulum instance. Reticulum uses this ID to distinguish between the devices.

Leave empty if you have only one RNode connected. If you have multiple RNodes, assign each a unique ID (starting from 0).

#### Flow Control

| | |
|---|---|
| **Default** | Unchecked (disabled) |
| **Visibility** | Advanced |

Enables hardware RTS/CTS flow control on the serial connection to the RNode. This is typically not needed for standard RNode setups but may be required if you experience serial buffer overruns at high data rates.

---

### 6.7 KISSInterface

The KISSInterface communicates with packet radio modems and Terminal Node Controllers (TNCs) that implement the KISS (Keep It Simple, Stupid) protocol. KISS is a standard protocol used in amateur radio for connecting computers to radio modems.

#### Serial Port

| | |
|---|---|
| **Default** | `/dev/ttyUSB1` |

The serial device path for the KISS TNC.

#### Baud Rate

| | |
|---|---|
| **Default** | `115200` |
| **Minimum** | 300 |

The serial port baud rate. Must match the baud rate configured on the TNC. Common values: `1200` (VHF packet radio), `9600` (UHF packet radio), `19200`, `38400`, `57600`, `115200` (modern TNCs).

#### Data Bits

| | |
|---|---|
| **Default** | `8` |

Number of data bits per serial frame. Almost always `8` for KISS TNCs.

#### Parity

| | |
|---|---|
| **Default** | `None` |
| **Options** | None, Even, Odd |

Serial parity checking mode. Almost always `None` for KISS TNCs.

#### Stop Bits

| | |
|---|---|
| **Default** | `1` |
| **Options** | 1, 2 |

Number of stop bits per serial frame. Almost always `1` for KISS TNCs.

#### Flow Control

| | |
|---|---|
| **Default** | Unchecked (disabled) |

Enables hardware RTS/CTS flow control. Enable if your TNC supports and requires it.

#### Preamble (ms)

| | |
|---|---|
| **Default** | (empty — TNC default) |
| **Visibility** | Advanced |

The KISS preamble time in milliseconds. This is the time the TNC keys the transmitter before sending data, allowing the remote receiver to synchronize. Leave empty to use the TNC's built-in default.

#### TX Tail (ms)

| | |
|---|---|
| **Default** | (empty — TNC default) |
| **Visibility** | Advanced |

The KISS transmit tail time in milliseconds. This is the time the transmitter remains keyed after the last data byte, ensuring the complete packet is transmitted. Leave empty to use the TNC's default.

#### Persistence

| | |
|---|---|
| **Default** | (empty — TNC default) |
| **Visibility** | Advanced |
| **Valid range** | 0 - 255 |

The KISS persistence parameter for CSMA (Carrier Sense Multiple Access) channel access. This value (0-255) represents the probability (value/256) that the TNC will transmit when the channel is sensed as clear. Higher values mean more aggressive transmission.

- `0`: Never transmit (useless)
- `63`: ~25% probability — conservative, good for busy channels
- `127`: ~50% probability — balanced
- `191`: ~75% probability — aggressive
- `255`: 100% probability — always transmit immediately (equivalent to no CSMA)

#### Slot Time (ms)

| | |
|---|---|
| **Default** | (empty — TNC default) |
| **Visibility** | Advanced |

The KISS slot time in milliseconds. The TNC waits this long between CSMA channel checks. Works in conjunction with the persistence parameter to control channel access timing.

#### Beacon Interval (s)

| | |
|---|---|
| **Default** | (empty — disabled) |
| **Visibility** | Advanced |

If set, the TNC transmits a beacon at this interval (in seconds). Beacons help other nodes discover this interface. Leave empty to disable beacons.

#### Beacon Data

| | |
|---|---|
| **Default** | (empty) |
| **Visibility** | Advanced |

Text payload included in beacon transmissions. Only used if Beacon Interval is set.

---

### 6.8 AX25KISSInterface

The AX25KISSInterface is similar to the KISSInterface but adds AX.25 protocol framing, which is standard in amateur radio networking. The AX.25 encapsulation adds overhead compared to raw KISS but provides compatibility with existing amateur radio infrastructure.

This interface type requires an amateur radio license to operate.

#### Serial Port, Baud Rate, Data Bits, Parity, Stop Bits, Flow Control

These fields are identical to the [KISSInterface](#67-kissinterface) equivalents. See those descriptions above.

#### Callsign

| | |
|---|---|
| **Default** | (empty) |
| **Validation** | 3-7 uppercase alphanumeric characters |

Your amateur radio callsign as assigned by your national licensing authority. This is included in AX.25 frame headers as required by amateur radio regulations.

**Examples**: `N0CALL`, `W1AW`, `VK2ABC`

#### SSID

| | |
|---|---|
| **Default** | (empty) |
| **Valid range** | 0 - 15 |

The AX.25 Secondary Station Identifier. SSIDs allow a single callsign to identify multiple stations or services. By convention:

| SSID | Common Use |
|------|-----------|
| 0 | Primary station |
| 1-4 | Additional stations |
| 5 | Digipeater |
| 7 | Handheld/portable |
| 9 | Mobile |
| 10 | Internet gateway |
| 15 | Reserved |

---

### 6.9 SerialInterface

The SerialInterface provides raw serial communication to data radios and modems. Unlike the KISS interfaces, this does not use any framing protocol — Reticulum's own HDLC-like framing is applied directly to the serial byte stream.

Use this for simple serial modems, data radios with transparent serial pass-through, or any device that accepts raw serial data.

#### Serial Port

| | |
|---|---|
| **Default** | `/dev/ttyUSB3` |

The serial device path for the modem or data radio.

#### Baud Rate

| | |
|---|---|
| **Default** | `9600` |
| **Minimum** | 300 |

Must match the modem's configured baud rate.

#### Data Bits, Parity, Stop Bits, Flow Control

Standard serial port parameters. See the [KISSInterface](#67-kissinterface) equivalents for descriptions. The defaults (8N1, no flow control) are correct for most modems.

---

### 6.10 I2PInterface

The I2PInterface enables communication over the Invisible Internet Protocol (I2P), an anonymous peer-to-peer overlay network. Using I2P, Reticulum nodes can communicate without revealing their real IP addresses, providing strong anonymity.

This requires a running I2P router (i2pd or Java I2P) accessible from the OPNsense device.

#### I2P Peers

| | |
|---|---|
| **Default** | (empty) |

A comma-separated list of I2P base32 destination addresses to connect to. These are the `.b32.i2p` addresses of remote Reticulum nodes reachable over the I2P network.

**Example**: `abc123def456.b32.i2p,xyz789ghi012.b32.i2p`

No firewall rules are created for I2P interfaces since all traffic is tunneled through the I2P router.

---

## 7. Transport Node

Navigate to: **Services > Reticulum > Transport**

This page provides the transport mode toggle (same setting as on the General page) along with detailed best-practice guidance and a summary of your configured interfaces.

### What is a Transport Node?

A standard Reticulum node only handles its own traffic — it sends and receives packets for its own destinations. A transport node additionally:

1. **Forwards packets** for other nodes across the network, enabling multi-hop communication
2. **Maintains a path table** recording how to reach known destinations
3. **Propagates announcements** so other nodes can discover destinations across the network
4. **Responds to path requests** so nodes can find routes to destinations they haven't directly heard from
5. **Caches public keys** from announcements, serving as a distributed cryptographic keystore

### Best Practices

- **Stationary**: Transport nodes must remain in fixed locations. If a transport node moves, its path table becomes invalid and the network must reconverge.
- **Always-on**: Transport nodes should run continuously. If a transport node goes offline, paths through it break and the network must rediscover routes.
- **Well-connected**: Place transport nodes where they bridge multiple network segments. A transport node with only one interface provides no routing benefit.
- **Strategic, not ubiquitous**: Enable transport only on nodes that genuinely provide connectivity between segments. A network should contain the minimum number of transport nodes needed for full coverage. Excessive transport nodes waste bandwidth and slow route convergence.
- **Announce rates**: On bandwidth-limited interfaces (especially LoRa), configure appropriate announce rate targets and penalties in the Interfaces tab to prevent announcement flooding.

### Interfaces Summary Table

The transport page shows a summary of all configured interfaces. Click "Manage interfaces and announce rate settings" to go to the Interfaces tab for detailed editing.

---

## 8. Propagation Node (LXMF)

Navigate to: **Services > Reticulum > Propagation**

The propagation node provides store-and-forward messaging using the LXMF (Lightweight Extensible Message Format) protocol. When enabled, the plugin runs the `lxmd` daemon alongside the Reticulum daemon.

### What is a Propagation Node?

A propagation node is a messaging relay for the Reticulum network. It:

1. **Stores messages** for recipients who are currently offline
2. **Delivers messages** to recipients when they come online and connect
3. **Peers with other propagation nodes** to synchronize message stores
4. **Provides redundancy** — messages stored on multiple propagation nodes survive individual node failures

LXMF clients (such as Sideband and NomadNet) automatically use the nearest available propagation node for message delivery and retrieval.

### Propagation Node Status Panel

The top of the propagation page shows a live status panel indicating whether lxmd is running, how many messages are stored, and how many peer nodes are connected.

### Settings

#### Enable Propagation Node

| | |
|---|---|
| **Default** | Unchecked (disabled) |

Enables the LXMF propagation daemon (`lxmd`). The Reticulum daemon must be enabled and running before lxmd can start — lxmd depends on a running Reticulum instance for network connectivity.

When enabled and applied, lxmd starts automatically after rnsd. When disabled and applied, lxmd is stopped.

#### Enable Node Functionality

| | |
|---|---|
| **Default** | Checked (enabled) |

Enables the actual propagation node functionality within lxmd. When disabled, lxmd runs but does not accept or propagate messages. This can be useful for running lxmd in a limited mode for testing.

#### Announce at Start

| | |
|---|---|
| **Default** | Checked (enabled) |

When enabled, the propagation node broadcasts an announcement on the Reticulum network when lxmd starts. This announcement makes the node discoverable by LXMF clients, allowing them to automatically find and use it for message delivery and retrieval.

Disable this only if you want a "hidden" propagation node that is only used by clients that are manually configured with its address.

#### Auto-Peer

| | |
|---|---|
| **Default** | Checked (enabled) |

When enabled, the propagation node automatically discovers and peers with other propagation nodes on the Reticulum network. Peered nodes synchronize their message stores, providing redundancy and wider message availability.

Disable this if you want a standalone propagation node that does not share messages with other nodes.

#### Auto-Peer Max Depth

| | |
|---|---|
| **Default** | `4` |
| **Valid range** | 1 - 128 |

The maximum number of network hops for auto-peering with other propagation nodes. The propagation node will only peer with other propagation nodes that are within this many hops.

Lower values limit peering to nearby nodes (reducing sync traffic but also reducing redundancy). Higher values allow peering with more distant nodes (increasing redundancy but also increasing sync traffic).

**Recommended setting**: `4` is a good balance for most networks. Increase if your network is large and you want wider message distribution. Decrease if bandwidth is constrained.

#### Message Storage Limit

| | |
|---|---|
| **Default** | `2000` |
| **Valid range** | 0 (unlimited) or any positive integer |

The maximum number of messages the propagation node will store. When the limit is reached, the oldest messages are deleted to make room for new ones.

Set to `0` for unlimited storage (messages are only removed when they expire or are explicitly deleted). Be mindful of disk space when using unlimited storage on devices with limited storage capacity.

Monitor the "Stored Messages" count in the propagation status panel and in the diagnostics tab to track usage.

#### Message Storage Path

| | |
|---|---|
| **Default** | `/var/db/lxmd/messagestore` |
| **Visibility** | Advanced |

The filesystem path where LXMF messages are stored. The default location is created during plugin installation with appropriate ownership and permissions.

Change this only if you need to store messages on a different filesystem (e.g., a mounted USB drive for additional storage capacity). Ensure the path exists and is owned by the `_reticulum` user.

#### Max Message Size (KB)

| | |
|---|---|
| **Default** | `1000` (1 MB) |
| **Minimum** | 1 |

The maximum accepted size for a single LXMF message in kilobytes. Messages larger than this limit are rejected by the propagation node.

This prevents individual large messages from consuming excessive storage and bandwidth. For text-only messaging, 1000 KB (1 MB) is generous. If you expect to handle messages with large attachments (images, files), increase this value.

#### Sync Interval (seconds)

| | |
|---|---|
| **Default** | `360` (6 minutes) |
| **Minimum** | 10 |

The interval in seconds between message synchronization cycles with peered propagation nodes. During each sync cycle, the node checks peered nodes for new messages and shares any messages they don't have.

Lower values provide faster message propagation across nodes but consume more bandwidth. Higher values reduce bandwidth usage but increase the delay before messages reach all propagation nodes.

**Recommended setting**: `360` (6 minutes) for most networks. Reduce to `60` (1 minute) if you need near-real-time message propagation and have sufficient bandwidth. Increase to `3600` (1 hour) or more if bandwidth is severely constrained.

#### Prioritise Local Delivery

| | |
|---|---|
| **Default** | Checked (enabled) |

When enabled, the propagation node prioritizes delivering messages directly to locally-reachable recipients before propagating them to peer nodes. This reduces latency for nearby users.

When disabled, messages are propagated to peer nodes and delivered to local recipients with equal priority.

Leave enabled for most deployments.

---

## 9. Diagnostics

Navigate to: **Services > Reticulum > Diagnostics**

The diagnostics page provides real-time visibility into the state of your Reticulum node. It contains five tabbed panels and supports auto-refresh at 5-second intervals.

### Controls

- **Auto-refresh (5s)**: Check this box to automatically reload the active tab every 5 seconds. Useful for monitoring a running node.
- **Refresh**: Click to manually reload the current tab.

### Status Tab

Shows the overall Reticulum daemon status, including:

- Whether the daemon is running
- Whether transport mode is enabled
- Uptime information
- Instance configuration details

### Interfaces Tab

Shows a table of all active Reticulum interfaces with real-time statistics:

| Column | Description |
|--------|-------------|
| **Name** | The configured interface name |
| **Type** | The interface type (AutoInterface, TCPServerInterface, etc.) |
| **Status** | Up or Down |
| **TX** | Total bytes transmitted |
| **RX** | Total bytes received |
| **RSSI** | Received Signal Strength Indicator in dBm (radio interfaces only) |
| **SNR** | Signal-to-Noise Ratio in dB (radio interfaces only) |

### Paths Tab

Shows the Reticulum path table — a list of known destinations and how to reach them:

| Column | Description |
|--------|-------------|
| **Destination** | The destination hash (hex-encoded cryptographic identifier) |
| **Hops** | Number of network hops to reach this destination |
| **Next Hop** | The address of the next transport node on the path |
| **Interface** | The interface used to reach this destination |
| **Expires** | When this path entry will expire and be removed |

### Announces Tab

Shows recent Reticulum announcements received by the node:

| Column | Description |
|--------|-------------|
| **Timestamp** | When the announcement was received |
| **Destination Hash** | The cryptographic identifier of the announcing destination |
| **Hops** | Number of hops the announcement has traveled |
| **Interface** | The interface the announcement was received on |

### Propagation Tab

Shows LXMF propagation node status (only relevant when the propagation node is enabled):

- Whether lxmd is running
- Number of stored messages
- Number of peered propagation nodes
- Synchronization status

---

## 10. Firewall Integration

The plugin automatically creates OPNsense firewall rules for Reticulum interfaces that listen on network ports. Rules are created and removed dynamically based on your interface configuration — you do not need to manually create firewall rules.

### Automatic Rules

| Interface Type | Protocol | Port | Rule Created |
|---------------|----------|------|-------------|
| TCPServerInterface | TCP | Listen Port | Yes |
| UDPInterface | UDP | Listen Port | Yes |
| AutoInterface | UDP | Discovery Port | Yes |
| AutoInterface | UDP | Data Port | Yes |
| TCPClientInterface | (outbound) | (none) | No — outbound connections use existing allow rules |
| RNodeInterface | (serial) | (none) | No — not an IP interface |
| KISSInterface | (serial) | (none) | No — not an IP interface |
| AX25KISSInterface | (serial) | (none) | No — not an IP interface |
| SerialInterface | (serial) | (none) | No — not an IP interface |
| I2PInterface | (tunneled) | (none) | No — traffic goes through the I2P router |

Rules are labeled descriptively (e.g., "Reticulum TCP: WAN Server") and link back to the plugin's interface configuration page.

### Manual Rules

If you need additional firewall rules (e.g., to restrict Reticulum access to specific source IP ranges), create them manually at **Firewall > Rules** on the appropriate interface tab.

---

## 11. REST API Reference

The plugin provides a full REST API for automation, scripting, and integration with external systems. All API endpoints require authentication with an OPNsense API key and secret.

### Settings API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reticulum/settings/get` | Retrieve general settings |
| POST | `/api/reticulum/settings/set` | Update general settings |
| GET | `/api/reticulum/settings/getPropagation` | Retrieve propagation settings |
| POST | `/api/reticulum/settings/setPropagation` | Update propagation settings |
| GET | `/api/reticulum/settings/searchInterface` | List all interfaces (grid data) |
| GET | `/api/reticulum/settings/getInterface/{uuid}` | Get a single interface by UUID |
| POST | `/api/reticulum/settings/addInterface` | Add a new interface |
| POST | `/api/reticulum/settings/setInterface/{uuid}` | Update an existing interface |
| POST | `/api/reticulum/settings/delInterface/{uuid}` | Delete an interface |
| POST | `/api/reticulum/settings/toggleInterface/{uuid}` | Toggle interface enabled/disabled |

### Service API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reticulum/service/start` | Start Reticulum services |
| POST | `/api/reticulum/service/stop` | Stop Reticulum services |
| POST | `/api/reticulum/service/restart` | Restart Reticulum services |
| POST | `/api/reticulum/service/reconfigure` | Regenerate configs and restart |
| GET | `/api/reticulum/service/status` | Get service running status |

### Diagnostics API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reticulum/diagnostics/rnstatus` | Reticulum daemon status |
| GET | `/api/reticulum/diagnostics/paths` | Path table |
| GET | `/api/reticulum/diagnostics/announces` | Recent announcements |
| GET | `/api/reticulum/diagnostics/propagation` | Propagation node status |
| GET | `/api/reticulum/diagnostics/interfaces` | Interface statistics |

### Example API Usage

```bash
# Get service status
curl -u "API_KEY:API_SECRET" \
  https://opnsense.local/api/reticulum/service/status

# Add a TCPServerInterface
curl -u "API_KEY:API_SECRET" -X POST \
  -d '{"interface":{"enabled":"1","name":"WAN TCP","interfaceType":"TCPServerInterface","tcp_server_listen_ip":"0.0.0.0","tcp_server_listen_port":"4242"}}' \
  https://opnsense.local/api/reticulum/settings/addInterface

# Apply configuration
curl -u "API_KEY:API_SECRET" -X POST \
  https://opnsense.local/api/reticulum/service/reconfigure
```

---

## 12. Command-Line Administration

For advanced troubleshooting or scripting, you can manage the Reticulum services from the OPNsense command line via SSH.

### Service Control

```bash
# Start Reticulum services
configctl reticulum start

# Stop Reticulum services
configctl reticulum stop

# Restart Reticulum services
configctl reticulum restart

# Check service status (JSON output)
configctl reticulum status
```

### Configuration Templates

```bash
# Regenerate configuration files from current settings
configctl template reload OPNsense/Reticulum

# View the generated Reticulum config
cat /usr/local/etc/reticulum/config

# View the generated LXMF config
cat /usr/local/etc/lxmd/config
```

### Diagnostics

```bash
# View Reticulum status (directly)
rnstatus --config /usr/local/etc/reticulum

# View path table
rnpath --config /usr/local/etc/reticulum

# Via configd (JSON output)
configctl reticulum diagnostics rnstatus
configctl reticulum diagnostics paths
configctl reticulum diagnostics interfaces
configctl reticulum diagnostics propagation
```

### Log Files

```bash
# View Reticulum logs (via syslog)
clog /var/log/system.log | grep reticulum

# View with live follow
tail -f /var/log/system.log | grep reticulum
```

---

## 13. Troubleshooting

### Service won't start

1. Check the log: **System > Log Files > General** or `clog /var/log/system.log | grep reticulum`
2. Verify the generated config is valid: `cat /usr/local/etc/reticulum/config`
3. Ensure at least one interface is configured and enabled
4. If using serial interfaces (RNode, KISS, Serial), verify the device path exists: `ls -la /dev/cuaU*`
5. If using TCP interfaces, ensure the port is not already in use: `sockstat -l | grep 4242`

### Interface shows as "Down" in diagnostics

- **TCP Client**: Verify the target host is reachable and the target port is correct. Check if the remote server is running.
- **TCP Server**: Verify the listen port is not blocked by another firewall rule or in use by another service.
- **RNode/KISS/Serial**: Verify the serial device exists, the baud rate matches the device, and the `_reticulum` user has permission to access the device (`ls -la /dev/cuaU0`).
- **AutoInterface**: Verify the OS network interface is up and has an IPv6 link-local address.
- **I2P**: Verify the I2P router is running and accessible.

### No peers discovered on AutoInterface

1. Ensure other Reticulum nodes on the same LAN segment also have AutoInterface configured with the same Group ID
2. Ensure the discovery scope is not too restrictive (try `Link` first)
3. Verify IPv6 is enabled on the network interfaces
4. Check that the discovery and data ports are not blocked by switch ACLs or other network infrastructure

### Propagation node won't start

1. Verify the Reticulum daemon is running first — lxmd depends on rnsd
2. Check logs for lxmd errors: `clog /var/log/system.log | grep lxmd`
3. Verify the message storage path exists and is writable by `_reticulum`: `ls -la /var/db/lxmd/messagestore`
4. Verify LXMF is installed: `python3.11 -m pip show lxmf`

### Serial device not found

On FreeBSD/OPNsense, USB serial devices use `/dev/cuaU*` naming (not `/dev/ttyUSB*` as on Linux). After connecting a USB serial device:

1. Check `dmesg | tail` for the device name
2. List available devices: `ls /dev/cuaU*`
3. Verify permissions: the `_reticulum` user must be in the `dialer` group (set up automatically during installation)

### Changes not taking effect

Always click **Apply** after making changes. The **Save** button stores your settings in the OPNsense configuration database but does not regenerate the Reticulum config files or restart services. **Apply** performs both save and reconfigure.

---

## 14. Example Configurations

### Example 1: Simple Local Network Node

A basic node that discovers peers on the local LAN.

**General Settings**:
- Enable Reticulum: Checked
- Enable Transport Node: Unchecked
- Log Level: 4 - Notice

**Interfaces**:
| Name | Type | Key Settings |
|------|------|-------------|
| LAN Discovery | AutoInterface | Group ID: `reticulum`, Discovery Scope: Link |

### Example 2: Internet-Connected Transport Node

A transport node that bridges local and remote Reticulum networks.

**General Settings**:
- Enable Reticulum: Checked
- Enable Transport Node: Checked
- Log Level: 4 - Notice

**Interfaces**:
| Name | Type | Key Settings |
|------|------|-------------|
| LAN Discovery | AutoInterface | Group ID: `reticulum`, Discovery Scope: Link, Allowed Interfaces: `igb1` (LAN only) |
| WAN TCP Server | TCPServerInterface | Listen IP: `0.0.0.0`, Listen Port: `4242` |
| Upstream Peer | TCPClientInterface | Target Host: `rns.example.com`, Target Port: `4242` |

### Example 3: LoRa Radio Gateway

A transport node that bridges LoRa radio to an IP network.

**General Settings**:
- Enable Reticulum: Checked
- Enable Transport Node: Checked

**Interfaces**:
| Name | Type | Key Settings |
|------|------|-------------|
| LoRa 868 MHz | RNodeInterface | Port: `/dev/cuaU0`, Frequency: `868000000`, Bandwidth: 125 kHz, TX Power: 14, SF: 7, CR: 4/5, Mode: Access Point |
| LAN | AutoInterface | Group ID: `reticulum`, Discovery Scope: Link |
| Internet Uplink | TCPClientInterface | Target Host: `backbone.example.com`, Target Port: `4242` |

The LoRa interface uses Access Point mode because it serves mobile/temporary radio users. The announce rate target on the LoRa interface should be set to something like `600` seconds to conserve radio bandwidth.

### Example 4: Full Transport + Propagation Node

A comprehensive node providing both routing and messaging services.

**General Settings**:
- Enable Reticulum: Checked
- Enable Transport Node: Checked
- Log Level: 4 - Notice

**Interfaces**:
| Name | Type | Key Settings |
|------|------|-------------|
| LAN | AutoInterface | Defaults |
| Public TCP | TCPServerInterface | Listen Port: `4242` |

**Propagation Settings**:
- Enable Propagation Node: Checked
- Enable Node Functionality: Checked
- Announce at Start: Checked
- Auto-Peer: Checked
- Auto-Peer Max Depth: 4
- Message Storage Limit: 5000
- Max Message Size: 1000 KB
- Sync Interval: 360 seconds
- Prioritise Local Delivery: Checked

### Example 5: Anonymous I2P Transport Node

A transport node accessible only over the I2P anonymous network.

**General Settings**:
- Enable Reticulum: Checked
- Enable Transport Node: Checked

**Interfaces**:
| Name | Type | Key Settings |
|------|------|-------------|
| I2P Network | I2PInterface | Peers: `abc123.b32.i2p,def456.b32.i2p` |
| Hidden TCP | TCPServerInterface | Listen IP: `127.0.0.1`, Listen Port: `4242`, I2P Tunneled: Checked |

The TCP server listens only on localhost, with an I2P server tunnel pointing to it. Remote nodes connect via the I2P address.
