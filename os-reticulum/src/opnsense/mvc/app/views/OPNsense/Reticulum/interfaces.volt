{#
    OPNsense Reticulum Plugin — Interface List & Editor
    Copyright (C) 2024 OPNsense Community
    SPDX-License-Identifier: BSD-2-Clause
#}

{% extends 'layouts/default.volt' %}

{% block content %}

<div id="service_status_container"></div>

{# ======================== Toolbar ======================== #}
<div class="row" style="margin-bottom:8px; margin-top:8px;">
    <div class="col-sm-12">
        <button class="btn btn-primary" id="addInterfaceBtn" type="button">
            <i class="fa fa-plus"></i> {{ lang._('Add Interface') }}
        </button>
        <button class="btn btn-default" id="applyInterfacesBtn" type="button" style="float:right;">
            <i class="fa fa-check"></i> {{ lang._('Apply Changes') }}
        </button>
    </div>
</div>

<div id="apply-success-msg" class="alert alert-info" style="display:none; margin-top:8px;">
    {{ lang._('Configuration applied. The service is reloading — the status indicator above will update shortly.') }}
</div>

{# ======================== Interface Grid ======================== #}
<table id="grid-interfaces" class="table table-condensed table-hover bootgrid-table"
       data-editDialog="DialogInterface"
       data-empty="{{ lang._('No interfaces configured. Click \\'Add Interface\\' to create your first Reticulum interface.') }}">
    <thead>
        <tr>
            <th data-column-id="name" data-type="string">{{ lang._('Name') }}</th>
            <th data-column-id="type" data-type="string" data-formatter="typeDisplay">{{ lang._('Type') }}</th>
            <th data-column-id="enabled" data-type="string" data-formatter="rowtoggle" data-width="6em">{{ lang._('Enabled') }}</th>
            <th data-column-id="mode" data-type="string" data-formatter="modeDisplay" data-width="9em">{{ lang._('Mode') }}</th>
            <th data-column-id="commands" data-formatter="commands" data-sortable="false" data-width="7em"></th>
        </tr>
    </thead>
    <tbody>
    </tbody>
</table>

{# ======================== Edit Interface Modal ======================== #}
<div id="DialogInterface" class="modal fade" role="dialog">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
                <h4 class="modal-title">{{ lang._('Edit Interface') }}</h4>
            </div>
            <div class="modal-body">
                <form id="interface" class="form-horizontal">
                <ul class="nav nav-tabs" id="interface-tabs">
                    <li class="active"><a data-toggle="tab" href="#tab-interface-basic">{{ lang._('Basic Settings') }}</a></li>
                    <li><a data-toggle="tab" href="#tab-interface-network">{{ lang._('Network') }}</a></li>
                    <li><a data-toggle="tab" href="#tab-interface-radio">{{ lang._('Radio / Serial') }}</a></li>
                    <li><a data-toggle="tab" href="#tab-interface-advanced">{{ lang._('Advanced') }}</a></li>
                </ul>
                <div class="tab-content" style="padding-top:12px;">

                    {# ===== Basic Settings Tab ===== #}
                    <div id="tab-interface-basic" class="tab-pane fade in active" role="tabpanel">

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.enabled" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Enabled') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.enabled" />
        <div class="hidden" data-for="help_for_interface.enabled">
            <small>{{ lang._('Enable or disable this interface. Disabled interfaces are stored in configuration but not loaded by rnsd.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.name" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Name') }} <span class="text-danger">*</span>
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.name"
               placeholder="{{ lang._('e.g. Home LoRa, Office TCP Uplink') }}" />
        <span class="text-danger small" id="interface-name-conflict" style="display:none;">{{ lang._('Interface name must be unique. This name is already used by another interface.') }}</span>
        <div class="hidden" data-for="help_for_interface.name">
            <small>{{ lang._('A unique human-readable name for this interface. Used in log output and status displays. Allowed characters: letters, numbers, spaces, hyphens, underscores. Max 64 characters. Each interface must have a distinct name.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.type" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Type') }} <span class="text-danger">*</span>
    </label>
    <div class="col-sm-8">
        <select class="form-control" id="interface.type">
            <option value="">{{ lang._('-- Select Type --') }}</option>
            <option value="TCPServerInterface">{{ lang._('TCP Server (accepts connections)') }}</option>
            <option value="TCPClientInterface">{{ lang._('TCP Client (connects outbound)') }}</option>
            <option value="BackboneInterface">{{ lang._('TCP Backbone') }}</option>
            <option value="UDPInterface">{{ lang._('UDP') }}</option>
            <option value="AutoInterface">{{ lang._('Local Network (Auto-Discovery)') }}</option>
            <option value="RNodeInterface">{{ lang._('RNode LoRa Radio') }}</option>
            <option value="RNodeMultiInterface">{{ lang._('RNode LoRa Radio (Multi-Channel)') }}</option>
            <option value="SerialInterface">{{ lang._('Serial Port') }}</option>
            <option value="KISSInterface">{{ lang._('KISS TNC') }}</option>
            <option value="AX25KISSInterface">{{ lang._('AX.25 / KISS TNC') }}</option>
            <option value="PipeInterface">{{ lang._('Pipe / Command') }}</option>
            <option value="I2PInterface">{{ lang._('I2P Network') }}</option>
        </select>
        <div class="hidden" data-for="help_for_interface.type">
            <small>{{ lang._('The interface type determines the physical or logical transport medium used. The form will show only the fields relevant to the selected type.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.mode" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Mode') }}
    </label>
    <div class="col-sm-8">
        <select class="form-control" id="interface.mode">
            <option value="full">{{ lang._('Full Router') }}</option>
            <option value="gateway">{{ lang._('Gateway') }}</option>
            <option value="access_point">{{ lang._('Access Point') }}</option>
            <option value="roaming">{{ lang._('Roaming Client') }}</option>
            <option value="boundary">{{ lang._('Boundary Node') }}</option>
        </select>
        <div class="hidden" data-for="help_for_interface.mode">
            <small>{{ lang._('Controls how this interface participates in the Reticulum network. Full Router is standard bidirectional relay (default). Gateway accepts/forwards routes from external networks. Access Point accepts connections from client/roaming nodes. Roaming Client is a portable endpoint that minimises announcements. Boundary Node is an edge node that limits routing scope.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.outgoing" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Allow Outbound Packets') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.outgoing" />
        <div class="hidden" data-for="help_for_interface.outgoing">
            <small>{{ lang._('Allow the Reticulum service to send packets out through this interface. Uncheck to make this interface receive-only.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.bootstrap_only" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Bootstrap Only') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.bootstrap_only" />
        <div class="hidden" data-for="help_for_interface.bootstrap_only">
            <small>{{ lang._('When enabled, this interface is only used during initial route discovery (bootstrapping) and is not used for ongoing packet forwarding. Use when you have a dedicated bootstrap/seed node connection that should not carry data traffic.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <div class="col-sm-12"><h5>{{ lang._('Network Isolation (IFAC)') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.network_name" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Network Segment Name') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.network_name" />
        <div class="hidden" data-for="help_for_interface.network_name">
            <small>{{ lang._('Network isolation group name (IFAC). Interfaces across different nodes that share the same Network Segment Name and passphrase form a single isolated logical network. Leave blank for the global Reticulum network.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.passphrase" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Network Segment Passphrase') }}
    </label>
    <div class="col-sm-8">
        <input type="password" class="form-control" id="interface.passphrase"
               placeholder="{{ lang._('Enter new value to change (current value not shown)') }}" />
        <div class="hidden" data-for="help_for_interface.passphrase">
            <small>{{ lang._('Passphrase used together with the Network Segment Name to derive cryptographic keying material for network isolation. Write-only — never returned by the API. Leave blank to keep the existing passphrase.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.ifac_size" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Authentication Tag Size (bytes)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.ifac_size" />
        <div class="hidden" data-for="help_for_interface.ifac_size">
            <small>{{ lang._('Size in bytes of the authentication tag appended to each packet for network isolation. Larger values (up to 512) provide stronger authentication but add overhead; minimum 8. Leave blank for automatic sizing.') }}</small>
        </div>
    </div>
</div>

                    </div>{# /tab-interface-basic #}

                    {# ===== Network Tab ===== #}
                    <div id="tab-interface-network" class="tab-pane fade" role="tabpanel">

<div class="form-group type-tcp-server type-udp">
    <div class="col-sm-12"><h5>{{ lang._('TCP / UDP Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-tcp-server type-udp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.listen_ip" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Listen IP') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.listen_ip" placeholder="0.0.0.0" />
        <div class="hidden" data-for="help_for_interface.listen_ip">
            <small>{{ lang._('Local IP address to bind the listening socket to. Use 0.0.0.0 to accept connections on all network interfaces. Enter a specific IP to restrict to one interface (e.g. 192.168.1.1). Applies to: TCPServerInterface, BackboneInterface, UDPInterface.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp-server type-udp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.listen_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Listen Port') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.listen_port" />
        <div class="hidden" data-for="help_for_interface.listen_port">
            <small>{{ lang._('TCP/UDP port number to listen on. Default: 4242. Ensure this port is reachable through your firewall if you want remote nodes to connect.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.target_host" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Target Host') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.target_host"
               placeholder="{{ lang._('hostname or IP address') }}" />
        <div class="hidden" data-for="help_for_interface.target_host">
            <small>{{ lang._('Hostname or IP address of the remote Reticulum node to connect to. Accepts DNS names or IP addresses. rnsd will automatically reconnect if the connection is lost. Applies to: TCPClientInterface.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.target_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Target Port') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.target_port"
               placeholder="4242" />
        <div class="hidden" data-for="help_for_interface.target_port">
            <small>{{ lang._('TCP port of the remote node to connect to. Must match the Listen Port configured on the remote TCPServerInterface or BackboneInterface. Default: 4242. Applies to: TCPClientInterface.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.prefer_ipv6" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Prefer IPv6') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.prefer_ipv6" />
        <div class="hidden" data-for="help_for_interface.prefer_ipv6">
            <small>{{ lang._('When the target hostname resolves to both IPv4 and IPv6 addresses, prefer the IPv6 address. Useful on dual-stack networks.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.device" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Restrict to Network Adapter') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.device" />
        <div class="hidden" data-for="help_for_interface.device">
            <small>{{ lang._('Name of the local network adapter to bind to (e.g. em0, vtnet0, re0). Leave blank to let the OS choose. Only needed if you have multiple network interfaces and want to pin this Reticulum interface to a specific adapter.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.i2p_tunneled" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('I2P Tunneled') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.i2p_tunneled" />
        <div class="hidden" data-for="help_for_interface.i2p_tunneled">
            <small>{{ lang._('Route this TCP interface through an I2P tunnel rather than directly over the internet. Requires a running I2P router on this host. Provides anonymity at the cost of higher latency.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.kiss_framing" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('KISS Framing') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.kiss_framing" />
        <div class="hidden" data-for="help_for_interface.kiss_framing">
            <small>{{ lang._('Use KISS protocol framing instead of raw TCP. Enable only when connecting to a legacy TNC or radio device that requires KISS framing over a TCP connection.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-tcp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.fixed_mtu" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Fixed MTU') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.fixed_mtu" />
        <div class="hidden" data-for="help_for_interface.fixed_mtu">
            <small>{{ lang._('Override the Maximum Transmission Unit for this interface (bytes). Leave blank for automatic MTU discovery. Only set this if you experience fragmentation issues or are connecting to a device with a known fixed MTU.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-udp">
    <div class="col-sm-12"><h5>{{ lang._('UDP Forward Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-udp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.forward_ip" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Forward IP') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.forward_ip" />
        <div class="hidden" data-for="help_for_interface.forward_ip">
            <small>{{ lang._('For UDPInterface: the destination IP address to forward UDP packets to. Leave blank if the same as Listen IP.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-udp">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.forward_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Forward Port') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.forward_port" />
        <div class="hidden" data-for="help_for_interface.forward_port">
            <small>{{ lang._('For UDPInterface: the destination UDP port to forward packets to. Leave blank if the same as Listen Port.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <div class="col-sm-12"><h5>{{ lang._('Local Network Auto-Discovery Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.group_id" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Network Group Name') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.group_id" />
        <div class="hidden" data-for="help_for_interface.group_id">
            <small>{{ lang._('Auto-discovery group identifier. Interfaces sharing the same Group ID form a single logical Reticulum network via IPv6 multicast. Leave blank to use the default group. Use a custom string to create a private subnet.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.discovery_scope" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Discovery Scope') }}
    </label>
    <div class="col-sm-8">
        <select class="form-control" id="interface.discovery_scope">
            <option value="link">{{ lang._('Local Link (default)') }}</option>
            <option value="admin">{{ lang._('Admin') }}</option>
            <option value="site">{{ lang._('Site') }}</option>
            <option value="organisation">{{ lang._('Organization') }}</option>
            <option value="global">{{ lang._('Global') }}</option>
        </select>
        <div class="hidden" data-for="help_for_interface.discovery_scope">
            <small>{{ lang._('IPv6 multicast scope for neighbour discovery. link (default) limits discovery to the local network segment. Wider scopes require proper IPv6 routing.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.discovery_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Discovery Port') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.discovery_port" />
        <div class="hidden" data-for="help_for_interface.discovery_port">
            <small>{{ lang._('UDP port used for multicast discovery announcements. Default: 29716. All nodes on the same AutoInterface group must use the same discovery port.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.data_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Data Port') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.data_port" />
        <div class="hidden" data-for="help_for_interface.data_port">
            <small>{{ lang._('UDP port used for actual Reticulum data packets. Default: 42671. All nodes on the same AutoInterface group must use the same data port.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.devices" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Devices') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.devices"
               data-allownew="true"
               data-nbdropdownelements="0"
               data-placeholder="{{ lang._('Enter network interface name and press Enter') }}" />
        <div class="hidden" data-for="help_for_interface.devices">
            <small>{{ lang._('Comma-separated list of OS network interface names to use for multicast discovery (e.g. em0, wlan0). Leave blank to automatically use all eligible interfaces.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.ignored_devices" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Ignored Devices') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.ignored_devices"
               data-allownew="true"
               data-nbdropdownelements="0"
               data-placeholder="{{ lang._('Enter interface name to ignore and press Enter') }}" />
        <div class="hidden" data-for="help_for_interface.ignored_devices">
            <small>{{ lang._('Comma-separated list of OS network interface names to exclude from AutoInterface discovery (e.g. docker0, lo0, tap0). Useful to prevent Reticulum from using virtual, loopback, or container interfaces.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-auto">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.multicast_address_type" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Multicast Address Type') }}
    </label>
    <div class="col-sm-8">
        <select class="form-control" id="interface.multicast_address_type">
            <option value="temporary">{{ lang._('Temporary (recommended)') }}</option>
            <option value="permanent">{{ lang._('Fixed') }}</option>
        </select>
        <div class="hidden" data-for="help_for_interface.multicast_address_type">
            <small>{{ lang._('IPv6 multicast address type used for discovery. Temporary (default) uses a dynamically generated IPv6 address compatible with most networks. Use temporary unless you have a specific reason to use a fixed address.') }}</small>
        </div>
    </div>
</div>

                    </div>{# /tab-interface-network #}

                    {# ===== Radio / Serial Tab ===== #}
                    <div id="tab-interface-radio" class="tab-pane fade" role="tabpanel">

<div class="form-group type-rnode">
    <div class="col-sm-12"><h5>{{ lang._('RNode LoRa Radio Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-rnode type-serial type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Serial Port') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.port"
               placeholder="/dev/cuaU0" />
        <div class="hidden" data-for="help_for_interface.port">
            <small>{{ lang._('The serial device path for the connected radio or TNC hardware. On FreeBSD/OPNsense: /dev/cuaU0, /dev/cuaU1, etc. for USB serial devices. The reticulum service user must be in the dialer group to access serial ports.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.frequency" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Frequency (Hz)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.frequency" />
        <div class="hidden" data-for="help_for_interface.frequency">
            <small>{{ lang._('Radio frequency in Hz for the RNode LoRa transceiver. Example: 915000000 for 915 MHz (Americas), 868000000 for 868 MHz (Europe), 433000000 for 433 MHz. Ensure you are licensed for the frequency in your jurisdiction.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.bandwidth" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Bandwidth (Hz)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.bandwidth" />
        <div class="hidden" data-for="help_for_interface.bandwidth">
            <small>{{ lang._('LoRa signal bandwidth in Hz. Common values: 125000 (125 kHz, standard), 250000 (250 kHz), 500000 (500 kHz), 62500 (62.5 kHz). Narrower bandwidth = longer range but slower data rate.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.txpower" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('TX Power (dBm)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.txpower" />
        <div class="hidden" data-for="help_for_interface.txpower">
            <small>{{ lang._('Transmit power in dBm. Range: 0–22 dBm. Use the minimum power necessary to maintain reliable links. Ensure compliance with local radio regulations.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.spreadingfactor" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Spreading Factor') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.spreadingfactor" />
        <div class="hidden" data-for="help_for_interface.spreadingfactor">
            <small>{{ lang._('LoRa spreading factor (SF7–SF12). Higher SF = longer range and better sensitivity, but much slower data rate. SF7 = fastest; SF12 = slowest. SF9 or SF10 is a common balance point. All nodes on a channel must use the same SF.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.codingrate" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Coding Rate') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.codingrate" />
        <div class="hidden" data-for="help_for_interface.codingrate">
            <small>{{ lang._('LoRa error correction coding rate (5–8, representing 4/5 to 4/8). Higher values add more redundancy and improve reliability in noisy environments at the cost of throughput. CR5 is most common. All nodes must match.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.airtime_limit_long" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Daily Airtime Limit (%)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.airtime_limit_long" />
        <div class="hidden" data-for="help_for_interface.airtime_limit_long">
            <small>{{ lang._('Maximum percentage of time this interface may transmit over a 24-hour rolling window (0–100). Required by radio regulations in some regions (e.g. EU 868 MHz: 1%). Leave blank for no limit.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.airtime_limit_short" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('10-Minute Airtime Limit (%)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.airtime_limit_short" />
        <div class="hidden" data-for="help_for_interface.airtime_limit_short">
            <small>{{ lang._('Maximum percentage of time this interface may transmit over any 10-minute rolling window (0–100). Use in conjunction with the daily limit for regulatory compliance. Leave blank for no limit.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode type-serial type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.flow_control" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Flow Control') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.flow_control" />
        <div class="hidden" data-for="help_for_interface.flow_control">
            <small>{{ lang._('Enable RTS/CTS hardware flow control. Required for some serial devices to prevent buffer overruns. Most USB-serial adapters work without hardware flow control.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.id_callsign" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('ID Callsign') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.id_callsign" />
        <div class="hidden" data-for="help_for_interface.id_callsign">
            <small>{{ lang._('Amateur radio callsign to transmit for station identification (e.g. W5XYZ). Required by law in many jurisdictions when operating amateur radio equipment. Format: ITU callsign, optionally with SSID suffix (e.g. W5XYZ-1).') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-rnode type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.id_interval" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('ID Interval (seconds)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.id_interval" />
        <div class="hidden" data-for="help_for_interface.id_interval">
            <small>{{ lang._('How often (in seconds) to transmit the station identification callsign. Default: 600 (every 10 minutes). Must satisfy local regulatory requirements. Applies when ID Callsign is set.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-serial">
    <div class="col-sm-12"><h5>{{ lang._('Serial Port Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-serial type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.speed" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Baud Rate') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.speed" />
        <div class="hidden" data-for="help_for_interface.speed">
            <small>{{ lang._('Serial port baud rate. Must match the baud rate configured on the connected device. Common values: 9600, 19200, 38400, 57600, 115200, 230400.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-serial">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.databits" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Data Bits') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.databits" />
        <div class="hidden" data-for="help_for_interface.databits">
            <small>{{ lang._('Number of data bits per character. Typically 8. Rarely needs changing unless the device specifies otherwise. Range: 5–8.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-serial type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.parity" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Parity') }}
    </label>
    <div class="col-sm-8">
        <select id="interface.parity" class="form-control">
            <option value="none">{{ lang._('None') }}</option>
            <option value="even">{{ lang._('Even') }}</option>
            <option value="odd">{{ lang._('Odd') }}</option>
        </select>
        <div class="hidden" data-for="help_for_interface.parity">
            <small>{{ lang._('Serial parity check setting. Options: none (most common), even, odd. Must match the device. Virtually all modern devices use none.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-serial type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.stopbits" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Stop Bits') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.stopbits" />
        <div class="hidden" data-for="help_for_interface.stopbits">
            <small>{{ lang._('Number of stop bits per character. Typically 1. Use 2 only if the device specification requires it.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-kiss">
    <div class="col-sm-12"><h5>{{ lang._('KISS TNC Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.preamble" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Preamble (ms)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.preamble" />
        <div class="hidden" data-for="help_for_interface.preamble">
            <small>{{ lang._('KISS TNC preamble duration in milliseconds — the time the TNC keys up the transmitter before sending data. Adjust based on your TNC/radio combination; leave blank for driver default.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.txtail" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('TX Tail (ms)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.txtail" />
        <div class="hidden" data-for="help_for_interface.txtail">
            <small>{{ lang._('KISS TNC TX tail duration in milliseconds — how long the TNC keeps transmitting after the last byte, allowing the signal to fully clear. Increase if the last few bytes of packets are being lost. Leave blank for driver default.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.persistence" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Persistence') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.persistence" />
        <div class="hidden" data-for="help_for_interface.persistence">
            <small>{{ lang._('KISS CSMA persistence value (0–255). Controls how aggressively the TNC attempts to transmit when the channel is clear. Higher = more aggressive. Leave blank for driver default.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-kiss">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.slottime" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Slot Time (ms)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.slottime" />
        <div class="hidden" data-for="help_for_interface.slottime">
            <small>{{ lang._('KISS CSMA slot time in milliseconds — the interval used in the random backoff algorithm before retrying transmission. Leave blank for driver default.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-ax25">
    <div class="col-sm-12"><h5>{{ lang._('AX.25 Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-ax25">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.callsign" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Callsign') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.callsign" />
        <div class="hidden" data-for="help_for_interface.callsign">
            <small>{{ lang._('Your amateur radio callsign for this AX.25 interface (e.g. W5XYZ). Mandatory for AX25KISSInterface — AX.25 protocol requires a valid callsign as the source address for all frames. Include SSID if needed (e.g. W5XYZ-9).') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-ax25">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.ssid" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('SSID') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.ssid" />
        <div class="hidden" data-for="help_for_interface.ssid">
            <small>{{ lang._('Secondary Station ID (0–15) for this AX.25 station. Used to distinguish multiple stations operating under the same callsign. SSID 0 is the default/primary station.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-pipe">
    <div class="col-sm-12"><h5>{{ lang._('Pipe / Command Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-pipe">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.command" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Command') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.command"
               placeholder="/usr/bin/nc 10.0.0.1 4242" />
        <div class="hidden" data-for="help_for_interface.command">
            <small>{{ lang._('The shell command to execute for this pipe interface. rnsd will communicate with the command\'s stdin/stdout as a Reticulum data channel. Example: /usr/bin/nc 10.0.0.1 4242. The command must be a full absolute path.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-pipe">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.respawn_delay" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Respawn Delay (seconds)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.respawn_delay" />
        <div class="hidden" data-for="help_for_interface.respawn_delay">
            <small>{{ lang._('How many seconds to wait before restarting the command if it exits unexpectedly. Minimum: 1. Default: 5. Increase this if the command is prone to rapid restart loops.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-i2p">
    <div class="col-sm-12"><h5>{{ lang._('I2P Network Settings') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-i2p">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.connectable" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Accept Inbound Connections') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.connectable" />
        <div class="hidden" data-for="help_for_interface.connectable">
            <small>{{ lang._('When enabled, this node creates an inbound I2P tunnel so other nodes can reach it directly through the I2P network. When disabled, this node only makes outbound connections (client-only mode). Requires a running I2P router on this host.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-i2p">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.i2p_peers" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('I2P Peers') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.i2p_peers"
               data-allownew="true"
               data-nbdropdownelements="0"
               data-placeholder="{{ lang._('Enter I2P peer address (b32.i2p format) and press Enter') }}" />
        <div class="hidden" data-for="help_for_interface.i2p_peers">
            <small>{{ lang._('Comma-separated list of I2P peer addresses (b32.i2p format) to connect to. These are the I2P addresses of other Reticulum nodes running I2PInterface. Leave blank if this node only listens for incoming I2P connections.') }}</small>
        </div>
    </div>
</div>

                    </div>{# /tab-interface-radio #}

                    {# ===== Advanced Tab ===== #}
                    <div id="tab-interface-advanced" class="tab-pane fade" role="tabpanel">

<div class="form-group">
    <div class="col-sm-12"><h5>{{ lang._('Rate Limits') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.announce_cap" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Max Announcements per Minute') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.announce_cap" />
        <div class="hidden" data-for="help_for_interface.announce_cap">
            <small>{{ lang._('Maximum number of route announcements per minute that the Reticulum service will emit on this interface. Range: 1-100. Useful on slow or congested links (e.g. LoRa radio).') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.bitrate" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Bitrate (bps)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.bitrate" />
        <div class="hidden" data-for="help_for_interface.bitrate">
            <small>{{ lang._('The physical or effective bitrate of this interface in bits per second. Used by rnsd to calculate routing costs and tune announce rates. Leave blank for automatic detection. Required for serial/radio interfaces.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <div class="col-sm-12"><h5>{{ lang._('Node Discovery / Advertisement') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.discoverable" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Advertise This Node') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.discoverable" />
        <div class="hidden" data-for="help_for_interface.discoverable">
            <small>{{ lang._('Broadcast this node\'s connection information (address, port) so other Reticulum nodes can automatically discover and connect to it. Applies to: TCP Server, TCP Backbone.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.discovery_name" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Node Display Name') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.discovery_name" />
        <div class="hidden" data-for="help_for_interface.discovery_name">
            <small>{{ lang._('A human-friendly name for this node shown to others during discovery (e.g. Region 5 Gateway, Office Backbone). Not required to be unique, but should be descriptive enough to identify the node.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.announce_interval" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Announce Interval (minutes)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.announce_interval" />
        <div class="hidden" data-for="help_for_interface.announce_interval">
            <small>{{ lang._('How often (in minutes) to broadcast the discovery announcement. Minimum: 5 minutes. Shorter intervals help nodes reconnect faster after a restart but increase network traffic.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.reachable_on" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Reachable On') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.reachable_on" />
        <div class="hidden" data-for="help_for_interface.reachable_on">
            <small>{{ lang._('Network address or hostname where this interface can be reached by connecting nodes. If left blank, rnsd attempts to auto-detect the address. Useful when behind NAT — specify the public/routable address here (e.g. 203.0.113.10 or mynode.dyndns.org).') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.latitude" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Latitude') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.latitude" />
        <div class="hidden" data-for="help_for_interface.latitude">
            <small>{{ lang._('Geographic latitude of this node in decimal degrees (e.g. 37.7749 for San Francisco). Optional — used for geographic display in compatible Reticulum applications. Leave blank if location should not be disclosed.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.longitude" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Longitude') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.longitude" />
        <div class="hidden" data-for="help_for_interface.longitude">
            <small>{{ lang._('Geographic longitude of this node in decimal degrees (e.g. -122.4194 for San Francisco). Optional — used for geographic display. Leave blank if location should not be disclosed.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.height" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Height (m)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.height" />
        <div class="hidden" data-for="help_for_interface.height">
            <small>{{ lang._('Altitude of this node above sea level in metres. Optional metadata for geographic systems. Leave blank if not needed.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.discovery_stamp_value" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Discovery Stamp Cost') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.discovery_stamp_value" />
        <div class="hidden" data-for="help_for_interface.discovery_stamp_value">
            <small>{{ lang._('Proof-of-work cost value attached to discovery announcements from this interface. Leave blank to use the default. Higher values make it more expensive for nodes to announce on this interface, discouraging announcement spam.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.discovery_encrypt" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Encrypt Discovery Announcements') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.discovery_encrypt" />
        <div class="hidden" data-for="help_for_interface.discovery_encrypt">
            <small>{{ lang._('Encrypt discovery announcements broadcast by this interface. When enabled, only nodes that know the network passphrase can process discovery announcements. Requires IFAC (network_name/passphrase) to be configured on this interface.') }}</small>
        </div>
    </div>
</div>

<div class="form-group type-discover">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.publish_ifac" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Publish IFAC Information') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.publish_ifac" />
        <div class="hidden" data-for="help_for_interface.publish_ifac">
            <small>{{ lang._('Publish interface access configuration (IFAC) in discovery announcements. Allows connecting nodes to automatically configure IFAC settings. Only enable on trusted networks.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <div class="col-sm-12"><h5>{{ lang._('Announce Rate Control') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.announce_rate_target" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Forwarded Announces Limit (per minute)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.announce_rate_target" />
        <div class="hidden" data-for="help_for_interface.announce_rate_target">
            <small>{{ lang._('Maximum announces per minute forwarded through this interface. Leave blank for no rate limiting. Setting this helps protect slow or congested interfaces (e.g. LoRa) from being overwhelmed by announcement traffic from higher-speed interfaces.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.announce_rate_grace" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Rate Limit Warm-Up Period (seconds)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.announce_rate_grace" />
        <div class="hidden" data-for="help_for_interface.announce_rate_grace">
            <small>{{ lang._('Number of seconds during which the announce rate limit is not enforced after startup or after a quiet period. Allows an initial burst of announces before the rate cap kicks in. Leave blank for no warm-up period.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.announce_rate_penalty" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Excess Rate Slowdown (seconds)') }}
    </label>
    <div class="col-sm-8">
        <input type="text" class="form-control" id="interface.announce_rate_penalty" />
        <div class="hidden" data-for="help_for_interface.announce_rate_penalty">
            <small>{{ lang._('Additional delay (in seconds) applied per announce when the rate limit is exceeded, progressively slowing down announcement bursts. Leave blank for no additional slowdown beyond the basic rate limit.') }}</small>
        </div>
    </div>
</div>

<div class="form-group">
    <div class="col-sm-12"><h5>{{ lang._('Announcement Flood Protection') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.ingress_control" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Enable Announcement Flood Protection') }}
    </label>
    <div class="col-sm-8">
        <input type="checkbox" id="interface.ingress_control" />
        <div class="hidden" data-for="help_for_interface.ingress_control">
            <small>{{ lang._('Enable the ingress control system for this interface. This limits the rate of incoming route announcements to protect against announcement floods (a form of denial-of-service). All fields below are only active when this is enabled.') }}</small>
        </div>
    </div>
</div>

<div id="ingress-control-fields" style="display:none;">

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_new_time" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('New Source Classification Window (seconds)') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_new_time" />
            <div class="hidden" data-for="help_for_interface.ic_new_time">
                <small>{{ lang._('Time window in seconds used to classify a source as new (not recently seen). Announcements from new sources are subject to tighter rate limits.') }}</small>
            </div>
        </div>
    </div>

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_burst_freq_new" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('Max Burst Rate — New Sources (per window)') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_burst_freq_new" />
            <div class="hidden" data-for="help_for_interface.ic_burst_freq_new">
                <small>{{ lang._('Maximum number of announces per time window accepted from new (previously unseen) sources. New sources are treated more strictly to prevent address-space flooding attacks.') }}</small>
            </div>
        </div>
    </div>

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_burst_freq" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('Max Burst Rate — Known Sources (per window)') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_burst_freq" />
            <div class="hidden" data-for="help_for_interface.ic_burst_freq">
                <small>{{ lang._('Maximum number of announces per time window accepted from known (previously seen) sources. Known sources are trusted slightly more than new ones.') }}</small>
            </div>
        </div>
    </div>

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_max_held_announces" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('Queue Size During Suppression') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_max_held_announces" />
            <div class="hidden" data-for="help_for_interface.ic_max_held_announces">
                <small>{{ lang._('Maximum number of announces to queue while suppressing a burst. Announces beyond this limit are dropped.') }}</small>
            </div>
        </div>
    </div>

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_burst_hold" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('Burst Hold Time (seconds)') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_burst_hold" />
            <div class="hidden" data-for="help_for_interface.ic_burst_hold">
                <small>{{ lang._('How long (in seconds) to suppress announces after a burst limit is exceeded. During this period, further announces from the offending source are queued up to the queue size limit.') }}</small>
            </div>
        </div>
    </div>

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_burst_penalty" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('Repeat Violation Backoff Multiplier') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_burst_penalty" />
            <div class="hidden" data-for="help_for_interface.ic_burst_penalty">
                <small>{{ lang._('Multiplier applied to the hold time for repeated burst violations. Higher values impose increasingly long suppression periods on persistent offenders.') }}</small>
            </div>
        </div>
    </div>

    <div class="form-group ingress-dep">
        <label class="col-sm-4 control-label">
            <a id="help_for_interface.ic_held_release_interval" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
            {{ lang._('Queue Drain Interval (seconds)') }}
        </label>
        <div class="col-sm-8">
            <input type="text" class="form-control" id="interface.ic_held_release_interval" />
            <div class="hidden" data-for="help_for_interface.ic_held_release_interval">
                <small>{{ lang._('Interval in seconds at which queued announces are gradually released after the suppression period ends. Prevents a large backlog from being released all at once.') }}</small>
            </div>
        </div>
    </div>

</div>{# /ingress-control-fields #}

<div class="form-group type-multi">
    <div class="col-sm-12"><h5>{{ lang._('Multi-Channel Sub-Interface Configuration') }}</h5><hr style="margin-top:4px;"/></div>
</div>

<div class="form-group type-multi">
    <div class="col-sm-12">
        <div class="alert alert-warning">
            <i class="fa fa-exclamation-triangle"></i>
            {{ lang._('Security note: This field is emitted verbatim into the rnsd configuration file. Do not paste untrusted content. Only administrators with full Reticulum access can save this field.') }}
        </div>
    </div>
</div>

<div class="form-group type-multi">
    <label class="col-sm-4 control-label">
        <a id="help_for_interface.sub_interfaces_raw" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
        {{ lang._('Channel Definitions') }}
    </label>
    <div class="col-sm-8">
        <textarea class="form-control" id="interface.sub_interfaces_raw" rows="10" spellcheck="false" style="font-family:monospace;"></textarea>
        <div class="hidden" data-for="help_for_interface.sub_interfaces_raw">
            <small>{{ lang._('Plain text configuration block for RNode LoRa Radio (Multi-Channel) sub-interfaces. Each sub-interface is defined with triple-bracket [[[name]]] syntax and its own frequency, bandwidth, txpower, spreadingfactor, and codingrate values. This field is required for RNodeMultiInterface.') }}</small>
            <pre style="margin-top:6px; font-size:12px;">[[[Channel A]]]
  frequency = 915000000
  bandwidth = 125000
  txpower = 17
  spreadingfactor = 9
  codingrate = 5

[[[Channel B]]]
  frequency = 868000000
  bandwidth = 250000
  txpower = 14
  spreadingfactor = 7
  codingrate = 5</pre>
        </div>
    </div>
</div>

                    </div>{# /tab-interface-advanced #}

                </div>{# /tab-content #}
                </form>
            </div>{# /modal-body #}
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">{{ lang._('Cancel') }}</button>
                <button type="button" class="btn btn-primary" id="btn-save-interface">{{ lang._('Save') }}</button>
            </div>
        </div>
    </div>
</div>

{# ======================== Delete Confirmation Modal ======================== #}
<div id="DialogDeleteInterface" class="modal fade" role="dialog">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
                <h4 class="modal-title">{{ lang._('Delete Interface?') }}</h4>
            </div>
            <div class="modal-body">
                <p id="delete-confirm-msg"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">{{ lang._('Cancel') }}</button>
                <button type="button" class="btn btn-danger" id="btn-confirm-delete">{{ lang._('Delete Interface') }}</button>
            </div>
        </div>
    </div>
</div>

{# ======================== JavaScript ======================== #}
<script>
$(document).ready(function() {

    // State: track add vs edit mode and cached data
    var editingUuid = null;
    var existingNames = {};
    var deleteUuid = null;

    /**
     * Map internal Reticulum interface type names to human-readable labels.
     */
    var typeDisplayNames = {
        'TCPServerInterface':   '{{ lang._("TCP Server (accepts connections)") }}',
        'TCPClientInterface':   '{{ lang._("TCP Client (connects outbound)") }}',
        'BackboneInterface':    '{{ lang._("TCP Backbone") }}',
        'UDPInterface':         '{{ lang._("UDP") }}',
        'AutoInterface':        '{{ lang._("Local Network (Auto-Discovery)") }}',
        'RNodeInterface':       '{{ lang._("RNode LoRa Radio") }}',
        'RNodeMultiInterface':  '{{ lang._("RNode LoRa Radio (Multi-Channel)") }}',
        'SerialInterface':      '{{ lang._("Serial Port") }}',
        'KISSInterface':        '{{ lang._("KISS TNC") }}',
        'AX25KISSInterface':    '{{ lang._("AX.25 / KISS TNC") }}',
        'PipeInterface':        '{{ lang._("Pipe / Command") }}',
        'I2PInterface':         '{{ lang._("I2P Network") }}'
    };

    var modeDisplayNames = {
        'full':         '{{ lang._("Full Router") }}',
        'gateway':      '{{ lang._("Gateway") }}',
        'access_point': '{{ lang._("Access Point") }}',
        'roaming':      '{{ lang._("Roaming Client") }}',
        'boundary':     '{{ lang._("Boundary Node") }}'
    };

    // Service status indicator (read-only rnsd dot — no Start/Stop on this page)
    updateServiceControlUI('reticulum', 'rnsd');
    setInterval(function() {
        updateServiceControlUI('reticulum', 'rnsd');
    }, 10000);

    // Initialize the interface grid
    $('#grid-interfaces').UIBootgrid({
        search:  '/api/reticulum/rnsd/searchInterfaces',
        get:     '/api/reticulum/rnsd/getInterface/',
        set:     '/api/reticulum/rnsd/setInterface/',
        add:     '/api/reticulum/rnsd/addInterface/',
        del:     '/api/reticulum/rnsd/delInterface/',
        toggle:  '/api/reticulum/rnsd/toggleInterface/',
        options: {
            selection: false,
            multiSelect: false,
            rowCount: [10, 25, 50],
            formatters: {
                typeDisplay: function(column, row) {
                    return typeDisplayNames[row.type] || row.type;
                },
                modeDisplay: function(column, row) {
                    return modeDisplayNames[row.mode] || row.mode;
                },
                commands: function(column, row) {
                    var safeName = $('<div/>').text(row.name).html();
                    return '<button type="button" class="btn btn-xs btn-default command-edit" ' +
                           'data-row-id="' + row.uuid + '" ' +
                           'aria-label="{{ lang._("Edit interface") }}" ' +
                           'title="{{ lang._("Edit") }}">' +
                           '<span class="fa fa-pencil"></span></button> ' +
                           '<button type="button" class="btn btn-xs btn-default command-delete" ' +
                           'data-row-id="' + row.uuid + '" ' +
                           'data-row-name="' + safeName + '" ' +
                           'aria-label="{{ lang._("Delete interface") }}" ' +
                           'title="{{ lang._("Delete") }}: ' + safeName + '">' +
                           '<span class="fa fa-trash-o text-danger"></span></button>';
                }
            }
        }
    });

    /**
     * Show/hide form field groups based on the selected interface type.
     */
    function updateTypeVisibility(type) {
        $('.type-tcp, .type-tcp-server, .type-udp, .type-auto, .type-rnode, .type-serial, ' +
          '.type-kiss, .type-ax25, .type-pipe, .type-i2p, .type-multi, .type-discover').hide();

        switch (type) {
            case 'TCPServerInterface':
            case 'BackboneInterface':
                // Server types: show listening fields, client-connection fields, and discovery
                $('.type-tcp, .type-tcp-server, .type-discover').show();
                break;
            case 'TCPClientInterface':
                // Client type: show only outbound-connection fields — not listen_ip/listen_port
                $('.type-tcp').show();
                break;
            case 'UDPInterface':
                $('.type-udp').show();
                break;
            case 'AutoInterface':
                $('.type-auto').show();
                break;
            case 'RNodeInterface':
                $('.type-rnode').show();
                break;
            case 'RNodeMultiInterface':
                $('.type-rnode, .type-multi').show();
                break;
            case 'SerialInterface':
                $('.type-serial').show();
                break;
            case 'KISSInterface':
                $('.type-kiss').show();
                break;
            case 'AX25KISSInterface':
                $('.type-ax25, .type-kiss').show();
                break;
            case 'PipeInterface':
                $('.type-pipe').show();
                break;
            case 'I2PInterface':
                $('.type-i2p').show();
                break;
        }
    }

    /**
     * Show/hide ingress control sub-fields based on the checkbox state.
     */
    function updateIngressVisibility() {
        if ($('#interface\\.ingress_control').is(':checked')) {
            $('#ingress-control-fields').show();
        } else {
            $('#ingress-control-fields').hide();
        }
    }

    // Update field visibility when the type dropdown changes
    $(document).on('change', '#interface\\.type', function() {
        updateTypeVisibility($(this).val());
    });

    // Toggle ingress sub-fields on checkbox change
    $(document).on('change', '#interface\\.ingress_control', function() {
        updateIngressVisibility();
    });

    /**
     * Capture the UUID when UIBootgrid's built-in edit handler fires.
     * UIBootgrid handles fetching data, populating form, opening modal.
     * We just need to record the UUID and update the title.
     */
    $(document).on('click', '.command-edit', function() {
        editingUuid = $(this).data('row-id');
        $('#DialogInterface .modal-title').text('{{ lang._("Edit Interface") }}');
    });

    // Delete confirmation flow
    $(document).on('click', '.command-delete', function(e) {
        e.preventDefault();
        e.stopImmediatePropagation();
        deleteUuid = $(this).data('row-id');
        var name = $(this).data('row-name');
        $('#delete-confirm-msg').text(
            '{{ lang._("Are you sure you want to delete the interface") }} "' + name + '"? ' +
            '{{ lang._("This cannot be undone.") }}'
        );
        $('#DialogDeleteInterface').modal('show');
    });

    $('#btn-confirm-delete').click(function() {
        if (deleteUuid) {
            ajaxCall('/api/reticulum/rnsd/delInterface/' + deleteUuid, {}, function() {
                $('#DialogDeleteInterface').modal('hide');
                $('#grid-interfaces').bootgrid('reload');
                deleteUuid = null;
            });
        }
    });

    $('#DialogDeleteInterface').on('hidden.bs.modal', function() {
        deleteUuid = null;
    });

    /**
     * Add Interface — clear the form and open the modal in add mode.
     */
    $('#addInterfaceBtn').click(function() {
        editingUuid = null;
        $('#interface')[0].reset();
        // Clear all select elements to defaults
        $('#interface\\.type').val('');
        $('#interface\\.mode').val('full');
        $('#interface\\.discovery_scope').val('link');
        $('#interface\\.multicast_address_type').val('temporary');
        $('#interface\\.parity').val('none');
        // Clear tokenizer fields (must re-init after clearing)
        $('#interface\\.devices, #interface\\.ignored_devices, #interface\\.i2p_peers').val('');
        // Clear textarea
        $('#interface\\.sub_interfaces_raw').val('');
        // Update modal title
        $('#DialogInterface .modal-title').text('{{ lang._("Add Interface") }}');
        // Reset name conflict state
        $('#interface-name-conflict').hide();
        // Initialize tokenizers and show modal
        formatTokenizersUI('#DialogInterface');
        updateTypeVisibility('');
        updateIngressVisibility();
        $('#DialogInterface').modal('show');
    });

    /**
     * Save button handler — calls addInterface or setInterface depending on mode.
     */
    $('#btn-save-interface').click(function() {
        var endpoint;
        if (editingUuid) {
            endpoint = '/api/reticulum/rnsd/setInterface/' + editingUuid;
        } else {
            endpoint = '/api/reticulum/rnsd/addInterface';
        }
        saveFormToEndpoint(endpoint, 'interface', function(data) {
            if (data && (data.result === 'saved' || data.uuid)) {
                $('#DialogInterface').modal('hide');
                $('#grid-interfaces').bootgrid('reload');
            }
        }, true);
    });

    // Apply Changes — triggers configd reconfigure
    $('#applyInterfacesBtn').click(function() {
        ajaxCall('/api/reticulum/service/reconfigure', {}, function(data) {
            updateServiceControlUI('reticulum', 'rnsd');
            $('#apply-success-msg').fadeIn().delay(3000).fadeOut();
        });
    });

    /**
     * When UIBootgrid opens the modal for edit (via .command-edit click),
     * it calls get URL and populates the form. We hook shown.bs.modal to
     * capture the UUID and set up visibility/tokenizers.
     */
    $('#DialogInterface').on('shown.bs.modal', function() {
        updateTypeVisibility($('#interface\\.type').val());
        updateIngressVisibility();

        // Fetch existing names for uniqueness check
        existingNames = {};
        ajaxCall('/api/reticulum/rnsd/searchInterfaces', {rowCount: -1}, function(data) {
            if (data && data.rows) {
                $.each(data.rows, function(idx, row) {
                    existingNames[row.uuid] = row.name;
                });
            }
            checkNameConflict();
        });
    });

    function checkNameConflict() {
        var currentName = $('#interface\\.name').val().trim();
        var conflict = false;
        if (currentName.length > 0) {
            $.each(existingNames, function(uuid, name) {
                if (uuid !== editingUuid && name === currentName) {
                    conflict = true;
                    return false;
                }
            });
        }
        if (conflict) {
            $('#interface-name-conflict').show();
        } else {
            $('#interface-name-conflict').hide();
        }
    }

    $(document).on('input', '#interface\\.name', function() {
        checkNameConflict();
    });

});
</script>

{% endblock %}
