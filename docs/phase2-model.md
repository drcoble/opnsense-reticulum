# Phase 2 — XML Model & BaseModel Class

## Overview
Define the complete OPNsense data model for all rnsd and lxmd settings. This is the single source of truth for configuration — all GUI forms, API endpoints, and template rendering derive from this model.

---

## Files

1. `src/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.xml` — Field definitions
2. `src/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.php` — BaseModel class

---

## 1. Reticulum.xml — Complete Model Definition

**Mount path:** `//OPNsense/Reticulum` in config.xml

### Structure Overview

```xml
<model>
    <mount>//OPNsense/Reticulum</mount>
    <version>1.0.0</version>
    <description>Reticulum Network Stack and LXMF Propagation Node</description>
    <items>
        <general>          <!-- rnsd global settings -->
        <interfaces>
            <interface type="ArrayField">  <!-- per-interface config -->
        <lxmf>             <!-- lxmd settings -->
    </items>
</model>
```

### 1.1 `<general>` Container — rnsd Global Settings

These map to the `[reticulum]` section of the Reticulum config file.

```xml
<general>
    <!-- Service enable -->
    <enabled type="BooleanField">
        <Required>Y</Required>
        <Default>0</Default>
        <ValidationMessage>Service enabled state is required</ValidationMessage>
    </enabled>

    <!-- Transport -->
    <enable_transport type="BooleanField">
        <Default>0</Default>
    </enable_transport>

    <!-- Instance sharing -->
    <share_instance type="BooleanField">
        <Default>1</Default>
    </share_instance>

    <shared_instance_port type="PortField">
        <Default>37428</Default>
        <ValidationMessage>Must be a valid port (1-65535)</ValidationMessage>
    </shared_instance_port>

    <instance_control_port type="PortField">
        <Default>37429</Default>
        <ValidationMessage>Must be a valid port (1-65535)</ValidationMessage>
    </instance_control_port>

    <!-- Error handling -->
    <panic_on_interface_error type="BooleanField">
        <Default>0</Default>
    </panic_on_interface_error>

    <respond_to_probes type="BooleanField">
        <Default>0</Default>
    </respond_to_probes>

    <!-- Remote management -->
    <enable_remote_management type="BooleanField">
        <Default>0</Default>
    </enable_remote_management>

    <remote_management_allowed type="CSVListField">
        <Mask>/^[0-9a-f]{32,64}$/</Mask>
        <MaskPerItem>Y</MaskPerItem>
        <ValidationMessage>Each entry must be a valid hex identity hash (32-64 chars)</ValidationMessage>
    </remote_management_allowed>

    <!-- rpc_key: write-only (UpdateOnlyTextField never returned in GET).
         Empty = unset. When set, minimum 32 hex chars (128-bit security). -->
    <rpc_key type="UpdateOnlyTextField">
        <Mask>/^([0-9a-f]{32,128})?$/</Mask>
        <ValidationMessage>RPC key must be empty (unset) or 32-128 lowercase hex characters</ValidationMessage>
    </rpc_key>

    <!-- Logging -->
    <loglevel type="IntegerField">
        <Default>4</Default>
        <MinimumValue>0</MinimumValue>
        <MaximumValue>7</MaximumValue>
        <ValidationMessage>Log level must be 0-7</ValidationMessage>
    </loglevel>

    <!-- logfile: restrict to /var/log/reticulum/ to prevent path traversal -->
    <logfile type="TextField">
        <Default>/var/log/reticulum/rnsd.log</Default>
        <Mask>/^\/var\/log\/reticulum\/[a-zA-Z0-9._-]{1,64}$/</Mask>
        <ValidationMessage>Log file must be a filename under /var/log/reticulum/</ValidationMessage>
    </logfile>
</general>
```

### 1.2 `<interfaces>` Container — Interface ArrayField

Each interface record contains ALL possible fields across all types. Type-specific fields are conditionally used by templates (Phase 3) and conditionally shown in the GUI (Phase 5).

```xml
<interfaces>
    <interface type="ArrayField">
        <!-- UniqueIdField REQUIRED: provides the UUID key for all API CRUD operations
             (addItem/getItem/setItem/delItem). Must be first child of every ArrayField. -->
        <uuid type="UniqueIdField">
            <Required>N</Required>
        </uuid>

        <!-- ===== COMMON FIELDS (all types) ===== -->

        <enabled type="BooleanField">
            <Default>1</Default>
            <Required>Y</Required>
        </enabled>

        <name type="TextField">
            <Required>Y</Required>
            <Mask>/^[a-zA-Z0-9 _-]{1,64}$/</Mask>
            <ValidationMessage>Name required: 1-64 chars, alphanumeric/spaces/underscore/dash</ValidationMessage>
        </name>

        <type type="OptionField">
            <Required>Y</Required>
            <OptionValues>
                <AutoInterface>AutoInterface</AutoInterface>
                <TCPServerInterface>TCPServerInterface</TCPServerInterface>
                <TCPClientInterface>TCPClientInterface</TCPClientInterface>
                <UDPInterface>UDPInterface</UDPInterface>
                <I2PInterface>I2PInterface</I2PInterface>
                <RNodeInterface>RNodeInterface</RNodeInterface>
                <RNodeMultiInterface>RNodeMultiInterface</RNodeMultiInterface>
                <SerialInterface>SerialInterface</SerialInterface>
                <KISSInterface>KISSInterface</KISSInterface>
                <AX25KISSInterface>AX25KISSInterface</AX25KISSInterface>
                <PipeInterface>PipeInterface</PipeInterface>
                <BackboneInterface>BackboneInterface</BackboneInterface>
            </OptionValues>
        </type>

        <mode type="OptionField">
            <Default>full</Default>
            <OptionValues>
                <full>Full</full>
                <gateway>Gateway</gateway>
                <access_point>Access Point</access_point>
                <roaming>Roaming</roaming>
                <boundary>Boundary</boundary>
            </OptionValues>
        </mode>

        <outgoing type="BooleanField">
            <Default>1</Default>
        </outgoing>

        <!-- IFAC settings -->
        <!-- network_name: reject newlines and INI structural characters to prevent config injection -->
        <network_name type="TextField">
            <Mask>/^[^\n\r\[\]=]{0,128}$/</Mask>
            <ValidationMessage>Network name must not contain newlines, brackets, or equals signs</ValidationMessage>
        </network_name>

        <!-- passphrase: write-only, never returned in GET responses -->
        <passphrase type="UpdateOnlyTextField" />

        <ifac_size type="IntegerField">
            <MinimumValue>8</MinimumValue>
            <MaximumValue>512</MaximumValue>
            <ValidationMessage>IFAC size must be 8-512 bits</ValidationMessage>
        </ifac_size>

        <!-- General limits -->
        <announce_cap type="IntegerField">
            <MinimumValue>1</MinimumValue>
            <MaximumValue>100</MaximumValue>
            <ValidationMessage>Announce cap must be 1-100 percent</ValidationMessage>
        </announce_cap>

        <bitrate type="IntegerField">
            <MinimumValue>1</MinimumValue>
            <MaximumValue>10000000000</MaximumValue>
            <ValidationMessage>Bitrate must be at least 1 bps</ValidationMessage>
        </bitrate>

        <bootstrap_only type="BooleanField">
            <Default>0</Default>
        </bootstrap_only>

        <!-- ===== TCP/IP FIELDS ===== -->

        <!-- listen_ip: restrict to valid IPv4/IPv6 address characters -->
        <listen_ip type="TextField">
            <Default>0.0.0.0</Default>
            <Mask>/^[0-9a-fA-F:.]{1,45}$/</Mask>
            <ValidationMessage>Must be a valid IPv4 or IPv6 address</ValidationMessage>
        </listen_ip>

        <listen_port type="PortField">
            <Default>4242</Default>
        </listen_port>

        <!-- target_host: use HostnameField for built-in hostname/IP validation -->
        <target_host type="HostnameField" />

        <target_port type="PortField">
            <Default>4242</Default>
        </target_port>

        <!-- device: OS network interface name to bind to (e.g., em0, igb1) -->
        <device type="TextField">
            <Mask>/^[a-zA-Z][a-zA-Z0-9_]{0,15}$/</Mask>
            <ValidationMessage>Must be a valid OS network interface name (e.g., em0)</ValidationMessage>
        </device>

        <prefer_ipv6 type="BooleanField">
            <Default>0</Default>
        </prefer_ipv6>

        <i2p_tunneled type="BooleanField">
            <Default>0</Default>
        </i2p_tunneled>

        <kiss_framing type="BooleanField">
            <Default>0</Default>
        </kiss_framing>

        <fixed_mtu type="IntegerField" />

        <!-- UDP specific -->
        <!-- forward_ip: restrict to valid IPv4/IPv6 address characters -->
        <forward_ip type="TextField">
            <Mask>/^[0-9a-fA-F:.]{0,45}$/</Mask>
            <ValidationMessage>Must be a valid IPv4 or IPv6 address</ValidationMessage>
        </forward_ip>

        <forward_port type="PortField">
            <Default>4242</Default>
        </forward_port>

        <!-- ===== SERIAL/RADIO FIELDS ===== -->

        <!-- port: serial device path — restrict to /dev/ to prevent path traversal -->
        <port type="TextField">
            <Mask>/^\/dev\/[a-zA-Z0-9._-]{1,64}$/</Mask>
            <ValidationMessage>Must be a valid device path (e.g., /dev/cuaU0)</ValidationMessage>
        </port>

        <speed type="IntegerField">
            <Default>9600</Default>
        </speed>

        <databits type="IntegerField">
            <Default>8</Default>
            <MinimumValue>5</MinimumValue>
            <MaximumValue>8</MaximumValue>
        </databits>

        <parity type="OptionField">
            <Default>none</Default>
            <OptionValues>
                <none>None</none>
                <even>Even</even>
                <odd>Odd</odd>
            </OptionValues>
        </parity>

        <stopbits type="IntegerField">
            <Default>1</Default>
            <MinimumValue>1</MinimumValue>
            <MaximumValue>2</MaximumValue>
        </stopbits>

        <flow_control type="BooleanField">
            <Default>0</Default>
        </flow_control>

        <!-- RNode radio parameters -->
        <!-- frequency: Hz — covers all LoRa/RNode ISM bands (100 MHz – 2.5 GHz) -->
        <frequency type="IntegerField">
            <MinimumValue>100000000</MinimumValue>
            <MaximumValue>2500000000</MaximumValue>
            <ValidationMessage>Frequency must be 100000000–2500000000 Hz (100 MHz–2.5 GHz)</ValidationMessage>
        </frequency>

        <!-- bandwidth: Hz — LoRa supported values: 7800–500000 -->
        <bandwidth type="IntegerField">
            <MinimumValue>7800</MinimumValue>
            <MaximumValue>500000</MaximumValue>
            <ValidationMessage>Bandwidth must be 7800–500000 Hz</ValidationMessage>
        </bandwidth>

        <txpower type="IntegerField">
            <MinimumValue>0</MinimumValue>
            <MaximumValue>22</MaximumValue>
            <ValidationMessage>TX power must be 0-22 dBm</ValidationMessage>
        </txpower>

        <spreadingfactor type="IntegerField">
            <MinimumValue>7</MinimumValue>
            <MaximumValue>12</MaximumValue>
            <ValidationMessage>Spreading factor must be 7-12</ValidationMessage>
        </spreadingfactor>

        <codingrate type="IntegerField">
            <MinimumValue>5</MinimumValue>
            <MaximumValue>8</MaximumValue>
            <ValidationMessage>Coding rate must be 5-8</ValidationMessage>
        </codingrate>

        <airtime_limit_long type="NumericField">
            <MinimumValue>0</MinimumValue>
            <MaximumValue>100</MaximumValue>
            <ValidationMessage>Airtime limit must be 0-100 percent</ValidationMessage>
        </airtime_limit_long>

        <airtime_limit_short type="NumericField">
            <MinimumValue>0</MinimumValue>
            <MaximumValue>100</MaximumValue>
            <ValidationMessage>Airtime limit must be 0-100 percent</ValidationMessage>
        </airtime_limit_short>

        <!-- AX.25 / identification -->
        <!-- callsign: uppercase amateur radio callsign, optionally with SSID suffix -->
        <callsign type="TextField">
            <Mask>/^[A-Z0-9]{0,7}(-[0-9]{1,2})?$/</Mask>
            <ValidationMessage>Must be a valid uppercase callsign (e.g., N0CALL or N0CALL-5)</ValidationMessage>
        </callsign>

        <ssid type="IntegerField">
            <Default>0</Default>
            <MinimumValue>0</MinimumValue>
            <MaximumValue>15</MaximumValue>
            <ValidationMessage>SSID must be 0-15</ValidationMessage>
        </ssid>

        <!-- id_callsign: identification callsign for KISS/RNode interfaces -->
        <id_callsign type="TextField">
            <Mask>/^[A-Z0-9]{0,7}(-[0-9]{1,2})?$/</Mask>
            <ValidationMessage>Must be a valid uppercase callsign (e.g., N0CALL)</ValidationMessage>
        </id_callsign>

        <id_interval type="IntegerField">
            <MinimumValue>1</MinimumValue>
        </id_interval>

        <!-- KISS TNC parameters -->
        <preamble type="IntegerField" />
        <txtail type="IntegerField" />
        <persistence type="IntegerField" />
        <slottime type="IntegerField" />

        <!-- ===== AUTO INTERFACE FIELDS ===== -->

        <!-- group_id: reject newlines and INI structural characters -->
        <group_id type="TextField">
            <Mask>/^[^\n\r\[\]=]{0,128}$/</Mask>
            <ValidationMessage>Group ID must not contain newlines, brackets, or equals signs</ValidationMessage>
        </group_id>

        <multicast_address_type type="OptionField">
            <Default>temporary</Default>
            <OptionValues>
                <temporary>Temporary</temporary>
                <permanent>Permanent</permanent>
            </OptionValues>
        </multicast_address_type>

        <!-- devices / ignored_devices: OS network interface names (e.g., em0, igb1) -->
        <devices type="CSVListField">
            <Mask>/^[a-zA-Z][a-zA-Z0-9_]{0,15}$/</Mask>
            <MaskPerItem>Y</MaskPerItem>
            <ValidationMessage>Each entry must be a valid OS interface name (e.g., em0)</ValidationMessage>
        </devices>

        <ignored_devices type="CSVListField">
            <Mask>/^[a-zA-Z][a-zA-Z0-9_]{0,15}$/</Mask>
            <MaskPerItem>Y</MaskPerItem>
            <ValidationMessage>Each entry must be a valid OS interface name (e.g., em0)</ValidationMessage>
        </ignored_devices>

        <discovery_scope type="OptionField">
            <Default>link</Default>
            <OptionValues>
                <link>Link</link>
                <admin>Admin</admin>
                <site>Site</site>
                <organisation>Organisation</organisation>
                <global>Global</global>
            </OptionValues>
        </discovery_scope>

        <discovery_port type="PortField">
            <Default>29716</Default>
        </discovery_port>

        <data_port type="PortField">
            <Default>42671</Default>
        </data_port>

        <!-- ===== I2P FIELDS ===== -->

        <connectable type="BooleanField">
            <Default>0</Default>
        </connectable>

        <!-- i2p_peers: rendered into INI config as `peers = ...`
             Validate per-item to prevent INI injection via newlines/brackets.
             I2P base32 addresses are 52 lowercase base32 chars + .b32.i2p suffix. -->
        <i2p_peers type="CSVListField">
            <Mask>/^[a-z2-7]{52}\.b32\.i2p$/</Mask>
            <MaskPerItem>Y</MaskPerItem>
            <ValidationMessage>Each entry must be a valid I2P base32 address (52 chars + .b32.i2p)</ValidationMessage>
        </i2p_peers>

        <!-- ===== PIPE FIELDS ===== -->

        <!-- command: SECURITY NOTE — this value is rendered directly into the Reticulum
             INI config and executed by rnsd as a subprocess under the reticulum service
             user. The Mask below rejects newlines and INI structural characters to
             prevent config injection. The Phase 3 template must NOT emit this field
             without newline escaping. Restrict to absolute executable paths in the GUI.
             The reticulum user has access to identity keys, serial devices (dialer group),
             and all data in /var/db/reticulum/ and /var/db/lxmf/. -->
        <command type="TextField">
            <Mask>/^[^\n\r\[\]]{0,512}$/</Mask>
            <ValidationMessage>Command must not contain newlines or INI section characters</ValidationMessage>
        </command>

        <respawn_delay type="IntegerField">
            <Default>5</Default>
            <MinimumValue>1</MinimumValue>
        </respawn_delay>

        <!-- ===== RNODEMULTI RAW BLOCK ===== -->

        <!-- sub_interfaces_raw: SECURITY NOTE — this field is emitted verbatim into the
             Reticulum config file by the Phase 3 template (required because OPNsense
             ArrayField cannot nest sub-interfaces). Any authenticated admin with the
             reticulum ACL privilege can inject arbitrary INI content through this field.
             This is an accepted architectural trade-off. The GUI (Phase 5) must display
             a prominent warning. No Mask is applied because the field intentionally
             contains newlines and INI structure. -->
        <sub_interfaces_raw type="TextField" />

        <!-- ===== DISCOVERABLE SETTINGS (server/backbone) ===== -->

        <discoverable type="BooleanField">
            <Default>0</Default>
        </discoverable>

        <!-- discovery_name: reject newlines and INI structural characters -->
        <discovery_name type="TextField">
            <Mask>/^[^\n\r\[\]=]{0,128}$/</Mask>
            <ValidationMessage>Discovery name must not contain newlines, brackets, or equals signs</ValidationMessage>
        </discovery_name>

        <announce_interval type="IntegerField">
            <MinimumValue>5</MinimumValue>
            <ValidationMessage>Announce interval must be at least 5 minutes</ValidationMessage>
        </announce_interval>
        <!-- Minutes, minimum 5 -->

        <!-- reachable_on: reject newlines and INI structural characters -->
        <reachable_on type="TextField">
            <Mask>/^[^\n\r\[\]=]{0,255}$/</Mask>
            <ValidationMessage>Reachable-on value must not contain newlines, brackets, or equals signs</ValidationMessage>
        </reachable_on>

        <discovery_stamp_value type="IntegerField" />

        <discovery_encrypt type="BooleanField">
            <Default>0</Default>
        </discovery_encrypt>

        <publish_ifac type="BooleanField">
            <Default>0</Default>
        </publish_ifac>

        <!-- Geolocation: valid geographic coordinate ranges -->
        <latitude type="NumericField">
            <MinimumValue>-90</MinimumValue>
            <MaximumValue>90</MaximumValue>
            <ValidationMessage>Latitude must be -90 to 90</ValidationMessage>
        </latitude>

        <longitude type="NumericField">
            <MinimumValue>-180</MinimumValue>
            <MaximumValue>180</MaximumValue>
            <ValidationMessage>Longitude must be -180 to 180</ValidationMessage>
        </longitude>

        <height type="NumericField" />

        <!-- ===== ANNOUNCE RATE CONTROL ===== -->

        <announce_rate_target type="IntegerField">
            <MinimumValue>1</MinimumValue>
        </announce_rate_target>

        <announce_rate_grace type="IntegerField">
            <MinimumValue>0</MinimumValue>
        </announce_rate_grace>

        <announce_rate_penalty type="IntegerField">
            <MinimumValue>0</MinimumValue>
        </announce_rate_penalty>

        <!-- ===== INGRESS CONTROL ===== -->

        <ingress_control type="BooleanField">
            <Default>0</Default>
        </ingress_control>

        <ic_new_time type="IntegerField" />
        <ic_burst_freq_new type="NumericField" />
        <ic_burst_freq type="NumericField" />
        <ic_max_held_announces type="IntegerField" />
        <ic_burst_hold type="IntegerField" />
        <ic_burst_penalty type="IntegerField" />
        <ic_held_release_interval type="IntegerField" />
    </interface>
</interfaces>
```

### 1.3 `<lxmf>` Container — lxmd Settings

**INI key name mapping:** Several model field names differ from the actual lxmd config file key names.
The Phase 3 Jinja2 template MUST emit the correct INI keys — not the model field names:

| Model field | lxmd INI key |
|---|---|
| `delivery_transfer_max_size` | `delivery_transfer_max_accepted_size` |
| `propagation_message_max_size` | `propagation_message_max_accepted_size` |
| `propagation_sync_max_size` | `propagation_sync_max_accepted_size` |
| `stamp_cost_target` | `propagation_stamp_cost_target` |
| `stamp_cost_flexibility` | `propagation_stamp_cost_flexibility` |

**Template storage note:** `allowed_identities` and `ignored_destinations` are stored by lxmd as
separate flat files (one hash per line), not as INI keys. The Phase 3 template must write
these fields to `/usr/local/etc/lxmf/allowed` and `/usr/local/etc/lxmf/ignored` respectively,
not into the INI config file.

**Size field units:**
- `delivery_transfer_max_size`, `propagation_message_max_size`, `propagation_sync_max_size` — **KB**
- `message_storage_limit` — **MB**

```xml
<lxmf>
    <!-- Service -->
    <enabled type="BooleanField">
        <Required>Y</Required>
        <Default>0</Default>
    </enabled>

    <!-- display_name: explicit newline rejection (. does not match \n in PCRE by default,
         but /^[^\n\r]{0,128}$/ makes the intent unambiguous) -->
    <display_name type="TextField">
        <Default>Anonymous Peer</Default>
        <Mask>/^[^\n\r]{0,128}$/</Mask>
        <ValidationMessage>Display name must be 128 characters or fewer with no newlines</ValidationMessage>
    </display_name>

    <!-- LXMF announce -->
    <lxmf_announce_at_start type="BooleanField">
        <Default>0</Default>
    </lxmf_announce_at_start>

    <lxmf_announce_interval type="IntegerField">
        <MinimumValue>1</MinimumValue>
        <MaximumValue>44640</MaximumValue>
        <ValidationMessage>Announce interval must be 1-44640 minutes (max 31 days)</ValidationMessage>
    </lxmf_announce_interval>

    <!-- Delivery -->
    <!-- INI key: delivery_transfer_max_accepted_size — unit: KB -->
    <delivery_transfer_max_size type="NumericField">
        <Default>1000</Default>
        <MinimumValue>0.38</MinimumValue>
        <ValidationMessage>Delivery transfer max size must be at least 0.38 KB</ValidationMessage>
    </delivery_transfer_max_size>

    <!-- on_inbound: path to a script executed by lxmd on every inbound LXMF message.
         SECURITY: if the script is writable by the reticulum user, this is a backdoor
         triggered by network traffic. Restrict to absolute paths only. -->
    <on_inbound type="TextField">
        <Mask>/^(\/[^\x00\n\r\[\]]{1,255})?$/</Mask>
        <ValidationMessage>Must be an absolute path (starting with /) or empty</ValidationMessage>
    </on_inbound>

    <!-- Propagation node -->
    <enable_node type="BooleanField">
        <Default>0</Default>
    </enable_node>

    <!-- node_name: explicit newline rejection -->
    <node_name type="TextField">
        <Mask>/^[^\n\r]{0,128}$/</Mask>
        <ValidationMessage>Node name must be 128 characters or fewer with no newlines</ValidationMessage>
    </node_name>

    <announce_interval type="IntegerField">
        <Default>360</Default>
        <MinimumValue>1</MinimumValue>
        <MaximumValue>44640</MaximumValue>
        <ValidationMessage>Announce interval must be 1-44640 minutes (max 31 days)</ValidationMessage>
    </announce_interval>

    <announce_at_start type="BooleanField">
        <Default>1</Default>
    </announce_at_start>

    <!-- message_storage_limit: unit MB -->
    <message_storage_limit type="NumericField">
        <Default>500</Default>
        <MinimumValue>0.005</MinimumValue>
        <ValidationMessage>Message storage limit must be at least 0.005 MB</ValidationMessage>
    </message_storage_limit>

    <!-- INI key: propagation_message_max_accepted_size — unit: KB -->
    <propagation_message_max_size type="NumericField">
        <Default>256</Default>
        <MinimumValue>0.38</MinimumValue>
        <ValidationMessage>Propagation message max size must be at least 0.38 KB</ValidationMessage>
    </propagation_message_max_size>

    <!-- INI key: propagation_sync_max_accepted_size — unit: KB -->
    <propagation_sync_max_size type="NumericField">
        <Default>10240</Default>
        <MinimumValue>0.38</MinimumValue>
        <ValidationMessage>Propagation sync max size must be at least 0.38 KB</ValidationMessage>
    </propagation_sync_max_size>

    <!-- Stamp / peering costs -->
    <!-- INI key: propagation_stamp_cost_target -->
    <stamp_cost_target type="IntegerField">
        <Default>16</Default>
        <MinimumValue>13</MinimumValue>
        <MaximumValue>64</MaximumValue>
        <ValidationMessage>Stamp cost target must be 13-64</ValidationMessage>
    </stamp_cost_target>

    <!-- INI key: propagation_stamp_cost_flexibility -->
    <!-- Cross-field constraint: stamp_cost_target - stamp_cost_flexibility >= 13
         (enforced in performValidation — effective minimum cost must not drop below 13) -->
    <stamp_cost_flexibility type="IntegerField">
        <Default>3</Default>
        <MinimumValue>0</MinimumValue>
        <MaximumValue>16</MaximumValue>
        <ValidationMessage>Stamp cost flexibility must be 0-16</ValidationMessage>
    </stamp_cost_flexibility>

    <peering_cost type="IntegerField">
        <Default>18</Default>
        <MinimumValue>13</MinimumValue>
        <MaximumValue>64</MaximumValue>
        <ValidationMessage>Peering cost must be 13-64</ValidationMessage>
    </peering_cost>

    <remote_peering_cost_max type="IntegerField">
        <Default>26</Default>
        <MinimumValue>1</MinimumValue>
        <MaximumValue>64</MaximumValue>
        <ValidationMessage>Remote peering cost max must be 1-64</ValidationMessage>
    </remote_peering_cost_max>

    <!-- Peering -->
    <max_peers type="IntegerField">
        <Default>20</Default>
        <MinimumValue>1</MinimumValue>
        <MaximumValue>1000</MaximumValue>
        <ValidationMessage>Max peers must be 1-1000</ValidationMessage>
    </max_peers>

    <autopeer type="BooleanField">
        <Default>1</Default>
    </autopeer>

    <autopeer_maxdepth type="IntegerField">
        <Default>6</Default>
        <MinimumValue>1</MinimumValue>
        <MaximumValue>128</MaximumValue>
        <ValidationMessage>Autopeer max depth must be 1-128</ValidationMessage>
    </autopeer_maxdepth>

    <from_static_only type="BooleanField">
        <Default>0</Default>
    </from_static_only>

    <static_peers type="CSVListField">
        <Mask>/^[0-9a-f]{32}$/</Mask>
        <MaskPerItem>Y</MaskPerItem>
        <ValidationMessage>Each peer must be a 32-character lowercase hex hash</ValidationMessage>
    </static_peers>

    <!-- Access control -->
    <auth_required type="BooleanField">
        <Default>0</Default>
    </auth_required>

    <control_allowed type="CSVListField">
        <Mask>/^[0-9a-f]{32}$/</Mask>
        <MaskPerItem>Y</MaskPerItem>
        <ValidationMessage>Each entry must be a 32-character lowercase hex hash</ValidationMessage>
    </control_allowed>

    <prioritise_destinations type="CSVListField">
        <Mask>/^[0-9a-f]{32}$/</Mask>
        <MaskPerItem>Y</MaskPerItem>
        <ValidationMessage>Each entry must be a 32-character lowercase hex hash</ValidationMessage>
    </prioritise_destinations>

    <!-- allowed_identities: TEMPLATE NOTE — lxmd stores this as a flat file
         (/usr/local/etc/lxmf/allowed, one hash per line), not an INI key.
         Phase 3 template must write this field to that file, not into the INI config. -->
    <allowed_identities type="CSVListField">
        <Mask>/^[0-9a-f]{32}$/</Mask>
        <MaskPerItem>Y</MaskPerItem>
        <ValidationMessage>Each entry must be a 32-character lowercase hex hash</ValidationMessage>
    </allowed_identities>

    <!-- ignored_destinations: TEMPLATE NOTE — lxmd stores this as a flat file
         (/usr/local/etc/lxmf/ignored, one hash per line), not an INI key.
         Phase 3 template must write this field to that file, not into the INI config. -->
    <ignored_destinations type="CSVListField">
        <Mask>/^[0-9a-f]{32}$/</Mask>
        <MaskPerItem>Y</MaskPerItem>
        <ValidationMessage>Each entry must be a 32-character lowercase hex hash</ValidationMessage>
    </ignored_destinations>

    <!-- Logging -->
    <loglevel type="IntegerField">
        <Default>4</Default>
        <MinimumValue>0</MinimumValue>
        <MaximumValue>7</MaximumValue>
        <ValidationMessage>Log level must be 0-7</ValidationMessage>
    </loglevel>

    <!-- logfile: restrict to /var/log/reticulum/ to prevent path traversal -->
    <logfile type="TextField">
        <Default>/var/log/reticulum/lxmd.log</Default>
        <Mask>/^\/var\/log\/reticulum\/[a-zA-Z0-9._-]{1,64}$/</Mask>
        <ValidationMessage>Log file must be a filename under /var/log/reticulum/</ValidationMessage>
    </logfile>
</lxmf>
```

---

## 2. Reticulum.php — BaseModel Class

**Path:** `src/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.php`

```php
<?php

namespace OPNsense\Reticulum;

use OPNsense\Base\BaseModel;
use OPNsense\Base\Messages\Message;

class Reticulum extends BaseModel
{
    /**
     * Custom validation: cross-field constraints
     * Called automatically by the framework during save
     */
    public function performValidation($validateFullModel = false)
    {
        $messages = parent::performValidation($validateFullModel);

        // shared_instance_port != instance_control_port
        $sip = (string)$this->general->shared_instance_port;
        $icp = (string)$this->general->instance_control_port;
        if (!empty($sip) && !empty($icp) && $sip === $icp) {
            $messages->appendMessage(new Message(
                "Shared instance port and instance control port must be different",
                "general.instance_control_port"
            ));
        }

        // Stamp cost floor: target - flexibility >= 13
        // lxmd subtracts flexibility from target to find the minimum accepted cost.
        // The absolute minimum cost is 13, so (target - flexibility) must be >= 13.
        $target = (int)(string)$this->lxmf->stamp_cost_target;
        $flex = (int)(string)$this->lxmf->stamp_cost_flexibility;
        if ($target - $flex < 13) {
            $messages->appendMessage(new Message(
                "Effective stamp cost (target minus flexibility) must be at least 13",
                "lxmf.stamp_cost_flexibility"
            ));
        }

        // ── Interface cross-record uniqueness checks ──
        // Duplicate names produce INI section collisions (last wins, silently dropping one).
        // Duplicate TCP listen endpoints cause bind failures at runtime.
        // Duplicate serial ports cause device contention failures.
        $namesSeen = [];
        $tcpListenSeen = [];
        $serialPortSeen = [];
        $tcpServerTypes = ['TCPServerInterface', 'BackboneInterface'];
        $serialTypes = ['RNodeInterface', 'RNodeMultiInterface', 'SerialInterface', 'KISSInterface', 'AX25KISSInterface'];

        foreach ($this->interfaces->interface->iterateItems() as $uuid => $iface) {
            $ifName = (string)$iface->name;
            $ifType = (string)$iface->type;
            $ifEnabled = (string)$iface->enabled;

            // 1. Interface name uniqueness (all interfaces, regardless of enabled state,
            //    because names become INI section headers in the config file)
            if (!empty($ifName)) {
                if (isset($namesSeen[$ifName])) {
                    $messages->appendMessage(new Message(
                        "Interface name '{$ifName}' is already used by another interface",
                        "interfaces.interface.{$uuid}.name"
                    ));
                }
                $namesSeen[$ifName] = true;
            }

            // Skip disabled interfaces for resource-contention checks
            if ($ifEnabled !== '1') {
                continue;
            }

            // 2. TCP listen IP+port uniqueness (enabled TCPServer/Backbone only)
            if (in_array($ifType, $tcpServerTypes, true)) {
                $listenIp = (string)$iface->listen_ip;
                $listenPort = (string)$iface->listen_port;
                if (!empty($listenPort)) {
                    $key = $listenIp . ':' . $listenPort;
                    if (isset($tcpListenSeen[$key])) {
                        $messages->appendMessage(new Message(
                            "Another enabled interface is already listening on {$key}",
                            "interfaces.interface.{$uuid}.listen_port"
                        ));
                    }
                    $tcpListenSeen[$key] = true;
                }
            }

            // 3. Serial port device uniqueness (enabled serial/radio types only)
            if (in_array($ifType, $serialTypes, true)) {
                $devPort = (string)$iface->port;
                if (!empty($devPort)) {
                    if (isset($serialPortSeen[$devPort])) {
                        $messages->appendMessage(new Message(
                            "Another enabled interface is already using device {$devPort}",
                            "interfaces.interface.{$uuid}.port"
                        ));
                    }
                    $serialPortSeen[$devPort] = true;
                }
            }
        }

        return $messages;
    }
}
```

---

## 3. Cross-Field Validation Rules

| Rule | Fields | Constraint | Error Location |
|------|--------|-----------|---------------|
| Port conflict | `general.shared_instance_port`, `general.instance_control_port` | Must differ | `general.instance_control_port` |
| Stamp floor | `lxmf.stamp_cost_target`, `lxmf.stamp_cost_flexibility` | target − flexibility ≥ 13 | `lxmf.stamp_cost_flexibility` |
| Interface name uniqueness | `interfaces.interface.*.name` | Unique across all records | Per-record `name` field |
| TCP listen endpoint uniqueness | `interfaces.interface.*.listen_ip`, `*.listen_port` | Unique among enabled TCPServer/Backbone | Per-record `listen_port` field |
| Serial port uniqueness | `interfaces.interface.*.port` | Unique among enabled serial/radio types | Per-record `port` field |

**Implementation:** All three cross-record checks are implemented in the model's
`performValidation()` via `iterateItems()`. This fires automatically on every
`addBase`/`setBase` call through the framework, so no controller-level code is needed.

- **Interface name uniqueness:** checked for all records (enabled or disabled), because
  names become INI section headers and a collision silently drops one interface.
- **TCP listen IP+port uniqueness:** checked for enabled TCPServerInterface and
  BackboneInterface records only — duplicate bind endpoints cause runtime failures.
- **Serial port device uniqueness:** checked for enabled RNodeInterface,
  RNodeMultiInterface, SerialInterface, KISSInterface, and AX25KISSInterface records
  only — duplicate device paths cause contention failures.

---

## 4. OPNsense Field Type Reference

| OPNsense Type | Maps To | Notes |
|---------------|---------|-------|
| `BooleanField` | 0/1 in config.xml | GUI renders as toggle/checkbox |
| `TextField` | String | Supports `<Mask>` regex validation |
| `IntegerField` | Integer | Supports Min/Max |
| `NumericField` | Float | Supports Min/Max, used for KB/MB values |
| `PortField` | Integer 1-65535 | Built-in port validation |
| `OptionField` | Enum string | Requires `<OptionValues>` |
| `CSVListField` | Comma-separated string | `<Mask>` validates the full CSV string by default; add `<MaskPerItem>Y</MaskPerItem>` to validate each item individually |
| `UpdateOnlyTextField` | String | Never returned in GET responses (masked by `getBase()`) |
| `HostnameField` | String | Validates hostname/IP format; use instead of TextField for host/IP fields |
| `ArrayField` | Repeating record | UUID-keyed, supports CRUD; **must include `<uuid type="UniqueIdField">` as first child** |
| `UniqueIdField` | UUID | Auto-generated record identifier; required first child of every ArrayField |

---

## 5. Implementation Checklist

- [ ] Create Reticulum.xml with all three containers (general, interfaces, lxmf)
- [ ] Verify all field types match OPNsense's available field types
- [ ] Create Reticulum.php with cross-field validation
- [ ] Test model loads without errors: `configctl firmware plugins list` should show os-reticulum
- [ ] Test field validation: create a test script or use API to save invalid values
- [ ] Verify UpdateOnlyTextField behavior for passphrase and rpc_key (GET must return empty/masked)
- [ ] Verify CSVListField MaskPerItem works: test saving a comma-separated list with mixed valid/invalid entries
- [ ] Verify UniqueIdField auto-generates UUIDs on addItem
- [ ] Verify stamp floor validation: target=13, flexibility=1 should PASS; target=13, flexibility=2 should FAIL
- [ ] Verify port conflict validation: shared_instance_port == instance_control_port should FAIL
- [ ] Add both files to pkg-plist
- [ ] Phase 3 template: use correct lxmd INI key names (see mapping table in section 1.3)
- [ ] Phase 3 template: write allowed_identities to /usr/local/etc/lxmf/allowed (one hash per line)
- [ ] Phase 3 template: write ignored_destinations to /usr/local/etc/lxmf/ignored (one hash per line)
- [ ] Phase 3 template: strip or escape newlines from all TextField values rendered into INI config
- [ ] Model: validate interface name uniqueness (implemented in performValidation)
- [ ] Model: validate TCPServerInterface/BackboneInterface listen_ip+port uniqueness (implemented in performValidation)
- [ ] Model: validate serial/radio port device uniqueness (implemented in performValidation)
- [ ] Phase 5 GUI: display prominent security warning on sub_interfaces_raw textarea
- [ ] Phase 5 GUI: label size fields with correct units (KB vs MB per section 1.3 notes)
