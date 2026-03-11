{#
    OPNsense Reticulum Plugin — LXMF Propagation Node Settings
    Copyright (C) 2024 OPNsense Community
    SPDX-License-Identifier: BSD-2-Clause
#}

{% extends 'layouts/default.volt' %}

{% block content %}

<p class="text-muted">
    {{ lang._('LXMF (Lightweight Extensible Message Format) is the messaging layer that runs over Reticulum. The Reticulum service (rnsd) must be running before LXMF can start.') }}
</p>

{# ======================== Dual Service Status Section ========================
     Neither service uses updateServiceControlUI() here because that function
     hardcodes #service_status_container as its target and can only control one
     service per page. Instead:
       - rnsd row: read-only status badge via direct ajaxCall to rnsdStatus
       - lxmd row: custom toolbar with Start/Stop/Restart buttons via direct
                   ajaxCall to lxmdStart / lxmdStop / lxmdRestart / lxmdStatus
     Both rows are polled on the same interval as the rnsd dependency banner.
#}
<div class="content-box" style="padding:10px 16px;">

    {# ---- Transport Node (rnsd) — read-only status ---- #}
    <div class="row" style="margin-bottom:8px; align-items:center; display:flex;">
        <div class="col-sm-2">
            <strong>{{ lang._('Transport Node') }}:</strong>
        </div>
        <div class="col-sm-10" id="rnsd-status-row">
            {# Populated by updateRnsdStatusBadge() #}
            <span id="rnsd-status-badge" class="label label-default" style="font-size:0.85em; padding:4px 8px;">
                {{ lang._('loading...') }}
            </span>
            <small class="text-muted" style="margin-left:8px;">
                {{ lang._('Managed on the') }}
                <a href="/ui/reticulum/general">{{ lang._('General') }}</a>
                {{ lang._('page.') }}
            </small>
        </div>
    </div>

    {# ---- Propagation Node (lxmd) — full service control ---- #}
    <div class="row" style="align-items:center; display:flex;">
        <div class="col-sm-2">
            <strong>{{ lang._('Propagation Node') }}:</strong>
        </div>
        <div class="col-sm-10">
            <div class="btn-group" role="group" style="margin-right:10px;">
                <button type="button" class="btn btn-xs btn-success" id="lxmd-btn-start"
                        title="{{ lang._('Start the LXMF propagation node (lxmd). Requires Transport Node to be running.') }}">
                    <i class="fa fa-play"></i> {{ lang._('Start') }}
                </button>
                <button type="button" class="btn btn-xs btn-danger" id="lxmd-btn-stop"
                        title="{{ lang._('Stop the LXMF propagation node (lxmd).') }}">
                    <i class="fa fa-stop"></i> {{ lang._('Stop') }}
                </button>
                <button type="button" class="btn btn-xs btn-default" id="lxmd-btn-restart"
                        title="{{ lang._('Restart the LXMF propagation node (lxmd). Requires Transport Node to be running.') }}">
                    <i class="fa fa-refresh"></i> {{ lang._('Restart') }}
                </button>
            </div>
            <span id="lxmd-status-badge" class="label label-default" style="font-size:0.85em; padding:4px 8px;">
                {{ lang._('loading...') }}
            </span>
            <span id="lxmd-action-msg" class="text-muted small" style="margin-left:8px; display:none;"></span>
        </div>
    </div>

</div>

{# ======================== rnsd Dependency Warning ======================== #}
<div id="rnsd-warning" class="alert alert-warning" style="display:none; margin-top:8px;">
    <i class="fa fa-exclamation-triangle"></i>
    {{ lang._('The Transport Node (rnsd) is not running. LXMF cannot start until rnsd is active.') }}
    <a href="/ui/reticulum/general">{{ lang._('Go to General settings to start the Transport Node.') }}</a>
</div>

{# ======================== Tab Navigation ======================== #}
<ul class="nav nav-tabs" data-tabs="tabs" id="maintabs" style="margin-top:12px;">
    <li class="active"><a data-toggle="tab" href="#tab-general">{{ lang._('General') }}</a></li>
    <li><a data-toggle="tab" href="#tab-propagation">{{ lang._('Propagation') }}</a></li>
    <li class="propagation-dep-tab"><a data-toggle="tab" href="#tab-costs">{{ lang._('Stamp Costs') }}</a></li>
    <li class="propagation-dep-tab"><a data-toggle="tab" href="#tab-peering">{{ lang._('Peering') }}</a></li>
    <li><a data-toggle="tab" href="#tab-acl">{{ lang._('Access Control') }}</a></li>
    <li><a data-toggle="tab" href="#tab-logging">{{ lang._('Logging') }}</a></li>
</ul>

<div class="tab-content content-box" style="padding:16px;">
    <form id="lxmf" class="form-horizontal">

        {# ======================== General Tab ======================== #}
        <div id="tab-general" class="tab-pane fade in active">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.enabled" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Enable LXMF Service') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.enabled" />
                    <div class="hidden" data-for="help_for_lxmf.enabled">
                        <small>{{ lang._('Enable the LXMF (Lightweight Extensible Message Format) service (lxmd). Requires the Reticulum service (rnsd) to be running — the LXMF service will fail to start if Reticulum is not active. Use this to turn this OPNsense device into a message relay and store-and-forward node.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.display_name" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Display Name') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.display_name" />
                    <div class="hidden" data-for="help_for_lxmf.display_name">
                        <small>{{ lang._('Human-readable name for this LXMF node as it appears to other peers and messaging clients (e.g. My Home Node, Region 5 Relay). Max 128 characters. Default: Anonymous Peer.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.lxmf_announce_at_start" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Announce LXMF Identity at Startup') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.lxmf_announce_at_start" />
                    <div class="hidden" data-for="help_for_lxmf.lxmf_announce_at_start">
                        <small>{{ lang._('Broadcast this node\'s LXMF identity to the network immediately when the LXMF service starts. Useful for quickly making this node visible to peers after a restart. If disabled, the node waits until the next scheduled announce interval.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.lxmf_announce_interval" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('LXMF Announce Interval (minutes)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.lxmf_announce_interval" />
                    <div class="hidden" data-for="help_for_lxmf.lxmf_announce_interval">
                        <small>{{ lang._('How often this node announces its LXMF identity to the network, in minutes. Leave blank to disable periodic announcements. Maximum: 44640 minutes (31 days).') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.delivery_transfer_max_size" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Max Delivery Size (KB)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.delivery_transfer_max_size" />
                    <div class="hidden" data-for="help_for_lxmf.delivery_transfer_max_size">
                        <small>{{ lang._('Maximum size in kilobytes of an incoming LXMF message that this node will accept for direct delivery. Messages larger than this limit are rejected. Default: 1000 KB.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Propagation Tab ======================== #}
        <div id="tab-propagation" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.enable_node" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Enable Propagation Node (Store & Forward Relay)') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.enable_node" />
                    <span class="help-block" style="margin-top:4px; margin-bottom:0;">
                        <small class="text-muted">{{ lang._('When enabled, the Stamp Costs and Peering tabs become available.') }}</small>
                    </span>
                    <div class="hidden" data-for="help_for_lxmf.enable_node">
                        <small>{{ lang._('Enable store-and-forward message propagation. When enabled, this node stores messages destined for offline recipients and forwards them when those recipients reconnect — making this a full LXMF propagation node. All fields in the Propagation, Costs, and Peering tabs are only active when this is enabled.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.node_name" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Node Name') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.node_name" />
                    <div class="hidden" data-for="help_for_lxmf.node_name">
                        <small>{{ lang._('Human-friendly name for this propagation node, shown to other propagation nodes during peering (e.g. Pacific Northwest Relay, Office Propagation Node). Max 128 characters. Leave blank to use the Display Name.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.announce_interval" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Propagation Announce Interval (minutes)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.announce_interval" />
                    <div class="hidden" data-for="help_for_lxmf.announce_interval">
                        <small>{{ lang._('How often (in minutes) this propagation node announces its availability to other nodes. Default: 360 (every 6 hours). Shorter intervals help new nodes discover this propagation node faster, but increase network traffic.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.announce_at_start" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Announce Propagation Node at Startup') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.announce_at_start" />
                    <div class="hidden" data-for="help_for_lxmf.announce_at_start">
                        <small>{{ lang._('Broadcast this propagation node\'s identity immediately when the LXMF service starts. Recommended — ensures the node is quickly visible to peers after restarts. Note: this is distinct from \'Announce LXMF Identity at Startup\' on the General tab.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.message_storage_limit" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Storage Limit (MB)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.message_storage_limit" />
                    <div class="hidden" data-for="help_for_lxmf.message_storage_limit">
                        <small>{{ lang._('Maximum disk space in megabytes allocated for storing messages awaiting delivery. Default: 500 MB. When this limit is reached, the oldest messages are deleted to make room.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.propagation_message_max_size" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Max Message Size (KB)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.propagation_message_max_size" />
                    <div class="hidden" data-for="help_for_lxmf.propagation_message_max_size">
                        <small>{{ lang._('Maximum size in kilobytes of a single message accepted into the propagation queue. Messages larger than this are rejected. Default: 256 KB. Note: the sync packet size (Max Sync Size) is constrained to 40x this value.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.propagation_sync_max_size" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Max Sync Size (KB)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.propagation_sync_max_size" />
                    <span class="text-warning small" id="sync-size-warn" style="display:none;">{{ lang._('Max Sync Size should be at least 40x the Max Message Size (currently: ') }}<span id="sync-size-min"></span>{{ lang._(' KB).') }}</span>
                    <div class="hidden" data-for="help_for_lxmf.propagation_sync_max_size">
                        <small>{{ lang._('Maximum size in kilobytes of a sync packet exchanged with peer propagation nodes. Default: 10240 KB (10 MB). Should be at least 40x the Max Message Size.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Costs Tab ======================== #}
        <div id="tab-costs" class="tab-pane fade">
            <div class="form-group propagation-dep">
                <div class="col-sm-12">
                    <p class="text-muted small">{{ lang._('Stamp costs are a lightweight proof-of-work mechanism that discourages message spam. Senders must perform a small calculation whose difficulty is set here. Higher values require more computational work from senders before their messages are accepted.') }}</p>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.stamp_cost_target" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Anti-Spam Work Requirement') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.stamp_cost_target" />
                    <div class="hidden" data-for="help_for_lxmf.stamp_cost_target">
                        <small>{{ lang._('Target computational difficulty required from message senders. Default: 16. Higher values require more work from senders. Range: 13-64. Constraint: target - tolerance must be at least 13.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.stamp_cost_flexibility" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Anti-Spam Tolerance Range') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.stamp_cost_flexibility" />
                    <span class="text-warning small" id="stamp-floor-warn" style="display:none;"></span>
                    <div class="hidden" data-for="help_for_lxmf.stamp_cost_flexibility">
                        <small>{{ lang._('Tolerance around the work requirement. Default: 3. Stamps with a cost between target-tolerance and target+tolerance are accepted. Range: 0-16. Constraint: target-tolerance must be at least 13.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.peering_cost" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Peer Acceptance Difficulty') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.peering_cost" />
                    <div class="hidden" data-for="help_for_lxmf.peering_cost">
                        <small>{{ lang._('Computational difficulty required for other nodes to establish peering with this node. Default: 18. Higher values reduce the risk of peer flooding. Range: 13-64.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.remote_peering_cost_max" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Maximum Acceptable Peer Difficulty') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.remote_peering_cost_max" />
                    <div class="hidden" data-for="help_for_lxmf.remote_peering_cost_max">
                        <small>{{ lang._('Maximum difficulty value this node will accept from remote peers. Default: 26. Peers advertising a difficulty higher than this are rejected. Set to 1 to accept all peers. Range: 1-64.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Peering Tab ======================== #}
        <div id="tab-peering" class="tab-pane fade">
            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.autopeer" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Auto-Peer') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.autopeer" />
                    <div class="hidden" data-for="help_for_lxmf.autopeer">
                        <small>{{ lang._('Automatically discover and establish peering with other LXMF propagation nodes found on the network, up to the configured maximum depth. When disabled, this node only peers with entries in the Static Peers list. Recommended: enabled for most deployments.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.autopeer_maxdepth" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Auto-Peer Max Depth (hops)') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.autopeer_maxdepth" />
                    <div class="hidden" data-for="help_for_lxmf.autopeer_maxdepth">
                        <small>{{ lang._('Maximum number of Reticulum hops away from this node to search for and accept automatic peers. Default: 6. Lower values restrict peering to nearby nodes; higher values build a larger peer mesh but increase sync traffic. Range: 1-128.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.max_peers" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Max Peers') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.max_peers" />
                    <div class="hidden" data-for="help_for_lxmf.max_peers">
                        <small>{{ lang._('Maximum number of active propagation peers this node maintains simultaneously. Default: 20. Range: 1-1000.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.from_static_only" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Peer With Static List Only') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.from_static_only" />
                    <div class="hidden" data-for="help_for_lxmf.from_static_only">
                        <small>{{ lang._('When enabled, this node only peers with nodes explicitly listed in the Static Peers field. Auto-peering is disabled regardless of the Auto-Peer setting.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group propagation-dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.static_peers" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Static Peers') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.static_peers"
                           data-allownew="true"
                           data-nbdropdownelements="0"
                           data-placeholder="{{ lang._('Paste a 32-character hex identity hash and press Enter') }}"
                           data-error-msg="{{ lang._('%s is not a valid identity hash. Must be exactly 32 hex characters.') }}" />
                    <span class="text-warning small" id="static-only-warn" style="display:none;">{{ lang._("'Peer With Static List Only' is checked but the Static Peers list is empty. Add at least one peer hash above, or this node will have no propagation peers.") }}</span>
                    <div class="hidden" data-for="help_for_lxmf.static_peers">
                        <small>{{ lang._('Comma-separated list of Reticulum identity hashes (32 hex characters each) for propagation nodes to statically peer with. These peers are always attempted regardless of the Auto-Peer setting.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== ACL Tab ======================== #}
        <div id="tab-acl" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.auth_required" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Require Authentication for Control') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="lxmf.auth_required" />
                    <div class="hidden" data-for="help_for_lxmf.auth_required">
                        <small>{{ lang._('Require cryptographic authentication for management and control operations on this propagation node. When enabled, only identities in the Authorized Controllers list can issue control commands. Recommended for publicly accessible propagation nodes.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.control_allowed" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Authorized Controllers') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.control_allowed"
                           data-allownew="true"
                           data-nbdropdownelements="0"
                           data-placeholder="{{ lang._('Paste a 32-character hex identity hash and press Enter') }}"
                           data-error-msg="{{ lang._('%s is not a valid identity hash. Must be exactly 32 hex characters.') }}" />
                    <div class="hidden" data-for="help_for_lxmf.control_allowed">
                        <small>{{ lang._('Identity hashes (32 hex characters each) of nodes permitted to issue control commands to this propagation node. Leave blank to allow no remote control.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.allowed_identities" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Permitted Message Sources') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.allowed_identities"
                           data-allownew="true"
                           data-nbdropdownelements="0"
                           data-placeholder="{{ lang._('Paste a 32-character hex identity hash and press Enter') }}"
                           data-error-msg="{{ lang._('%s is not a valid identity hash. Must be exactly 32 hex characters.') }}" />
                    <div class="hidden" data-for="help_for_lxmf.allowed_identities">
                        <small>{{ lang._('Identity hashes (32 hex characters each) of nodes permitted to submit messages to this propagation node. Leave blank to allow all sources (open propagation node — recommended for community nodes).') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.ignored_destinations" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Blocked Destinations') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.ignored_destinations"
                           data-allownew="true"
                           data-nbdropdownelements="0"
                           data-placeholder="{{ lang._('Paste a 32-character hex identity hash and press Enter') }}"
                           data-error-msg="{{ lang._('%s is not a valid identity hash. Must be exactly 32 hex characters.') }}" />
                    <div class="hidden" data-for="help_for_lxmf.ignored_destinations">
                        <small>{{ lang._('Destination hashes (32 hex characters each) whose messages this node will refuse to store or forward. Use this to block known spam sources. Messages addressed to blocked destinations are silently dropped.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.prioritise_destinations" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Priority Destinations') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.prioritise_destinations"
                           data-allownew="true"
                           data-nbdropdownelements="0"
                           data-placeholder="{{ lang._('Paste a 32-character hex identity hash and press Enter') }}"
                           data-error-msg="{{ lang._('%s is not a valid identity hash. Must be exactly 32 hex characters.') }}" />
                    <div class="hidden" data-for="help_for_lxmf.prioritise_destinations">
                        <small>{{ lang._('Destination hashes (32 hex characters each) that receive priority handling in the propagation queue. Messages for these destinations are delivered before lower-priority traffic.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Logging Tab ======================== #}
        <div id="tab-logging" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.loglevel" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Log Level') }}
                </label>
                <div class="col-sm-10">
                    <select id="lxmf.loglevel" class="form-control">
                        <option value="0">{{ lang._('Critical') }} (0)</option>
                        <option value="1">{{ lang._('Error') }} (1)</option>
                        <option value="2">{{ lang._('Warning') }} (2)</option>
                        <option value="3">{{ lang._('Notice') }} (3)</option>
                        <option value="4" selected="selected">{{ lang._('Info') }} (4)</option>
                        <option value="5">{{ lang._('Debug') }} (5)</option>
                        <option value="6">{{ lang._('Extreme') }} (6)</option>
                        <option value="7">{{ lang._('Trace') }} (7)</option>
                    </select>
                    <div class="hidden" data-for="help_for_lxmf.loglevel">
                        <small>{{ lang._('Controls how much detail the LXMF service writes to the log file. Select from: Critical, Error, Warning, Notice, Info (recommended), Debug, Extreme, Trace.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.logfile" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Log File') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.logfile" />
                    <div class="hidden" data-for="help_for_lxmf.logfile">
                        <small>{{ lang._('Log file name under /var/log/reticulum/. Default: /var/log/reticulum/lxmd.log. Only filenames within /var/log/reticulum/ are permitted.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_lxmf.on_inbound" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Run Script on Message Receipt') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="lxmf.on_inbound" />
                    <span class="text-warning small"><i class="fa fa-exclamation-triangle"></i> {{ lang._('Security: This script is executed on every inbound message received from the network. Ensure the script is owned by root and is not writable by the reticulum user.') }}</span>
                    <div class="hidden" data-for="help_for_lxmf.on_inbound">
                        <small>{{ lang._('Absolute path to a script or executable to run when the LXMF service receives an inbound message. The script receives message metadata as arguments. Leave blank to disable. Useful for custom notification or integration workflows.') }}</small>
                    </div>
                </div>
            </div>
        </div>

    </form>

    {# ======================== Form Footer ======================== #}
    <div class="row">
        <div class="col-md-12 text-right">
            <button class="btn btn-primary" id="saveBtn" type="button">
                <i class="fa fa-save"></i> {{ lang._('Save') }}
            </button>
            <button class="btn btn-default" id="applyBtn" type="button"
                    title="{{ lang._('Saves and signals lxmd to reload its configuration. A full service restart may occur.') }}">
                <i class="fa fa-check"></i> {{ lang._('Apply Changes') }}
            </button>
        </div>
    </div>

    <div id="apply-success-msg" class="alert alert-info" style="display:none; margin-top:12px;">
        {{ lang._('Configuration applied. The service is reloading — the status indicator above will update shortly.') }}
    </div>
</div>

<script>
$(document).ready(function() {

    // -----------------------------------------------------------------------
    // Status badge helpers
    // -----------------------------------------------------------------------

    /**
     * Apply a Bootstrap label class and text to a badge element.
     * @param {jQuery} $badge  The <span> element to update.
     * @param {string} status  'running' | 'stopped' | 'loading' | 'error'
     * @param {string} text    Display text (already translated at call site).
     */
    function applyBadge($badge, status, text) {
        $badge.removeClass('label-default label-success label-danger label-warning');
        switch (status) {
            case 'running':
                $badge.addClass('label-success');
                break;
            case 'stopped':
                $badge.addClass('label-danger');
                break;
            case 'error':
                $badge.addClass('label-warning');
                break;
            default:
                $badge.addClass('label-default');
        }
        $badge.text(text);
    }

    // -----------------------------------------------------------------------
    // rnsd — read-only status badge + dependency warning
    // -----------------------------------------------------------------------

    /**
     * Poll /api/reticulum/service/rnsdStatus and update:
     *   - the read-only badge in the rnsd status row
     *   - the #rnsd-warning dependency banner
     *   - the disabled state of the lxmd Start/Restart buttons
     *
     * This single function replaces the former separate checkRnsdDependency()
     * call, avoiding two redundant AJAX requests per polling cycle.
     */
    function updateRnsdStatus() {
        ajaxCall('/api/reticulum/service/rnsdStatus', {}, function(data) {
            var running = (data && data.status === 'running');
            var $badge = $('#rnsd-status-badge');

            if (running) {
                applyBadge($badge, 'running', '{{ lang._("Running") }}');
                $('#rnsd-warning').hide();
            } else {
                applyBadge($badge, 'stopped', '{{ lang._("Stopped") }}');
                $('#rnsd-warning').show();
            }

            // Disable lxmd Start and Restart when rnsd is not running — the
            // server enforces this too, but disabling the buttons avoids a
            // confusing error response reaching the user.
            $('#lxmd-btn-start, #lxmd-btn-restart').prop('disabled', !running);
        });
    }

    // -----------------------------------------------------------------------
    // lxmd — custom service control toolbar
    // -----------------------------------------------------------------------

    /**
     * Poll /api/reticulum/service/lxmdStatus and update the status badge.
     * Button enabled/disabled state is managed by updateRnsdStatus() (for
     * rnsd dependency) and the action handlers themselves (during in-flight
     * requests to prevent double-clicks).
     */
    function updateLxmdStatus() {
        ajaxCall('/api/reticulum/service/lxmdStatus', {}, function(data) {
            var running = (data && data.status === 'running');
            applyBadge(
                $('#lxmd-status-badge'),
                running ? 'running' : 'stopped',
                running ? '{{ lang._("Running") }}' : '{{ lang._("Stopped") }}'
            );
        });
    }

    /**
     * Show a transient action message below the lxmd toolbar, then fade it
     * out after a short delay. Avoids browser alert() per OPNsense UI convention.
     * @param {string} msg   Message text.
     * @param {string} cls   CSS class to apply (e.g. 'text-danger', 'text-muted').
     */
    function showLxmdMsg(msg, cls) {
        var $msg = $('#lxmd-action-msg');
        $msg.removeClass('text-muted text-danger text-warning')
            .addClass(cls)
            .text(msg)
            .show();
        setTimeout(function() { $msg.fadeOut(400); }, 4000);
    }

    /**
     * Lock all lxmd toolbar buttons during an in-flight action, then unlock
     * them and refresh both service statuses once the action completes.
     * @param {string}   endpoint  API path, e.g. '/api/reticulum/service/lxmdStart'
     * @param {string}   label     Human-readable action label for the message.
     */
    function lxmdAction(endpoint, label) {
        // Disable all buttons to prevent concurrent actions
        $('#lxmd-btn-start, #lxmd-btn-stop, #lxmd-btn-restart').prop('disabled', true);

        ajaxCall(endpoint, {}, function(data) {
            if (data && data.result === 'error') {
                // Server rejected the action (e.g. rnsd dependency check failed)
                var detail = data.message || '{{ lang._("Unknown error") }}';
                showLxmdMsg(label + ': ' + detail, 'text-danger');
            } else {
                showLxmdMsg(label + ' ' + '{{ lang._("command sent.") }}', 'text-muted');
            }
            // Refresh both rows after a brief settle delay to give the
            // service time to transition before we read status back.
            setTimeout(function() {
                updateRnsdStatus();
                updateLxmdStatus();
            }, 1200);
        });
    }

    // -----------------------------------------------------------------------
    // Propagation field visibility
    // -----------------------------------------------------------------------

    /**
     * Show or hide propagation-dependent fields based on the enable_node checkbox.
     */
    function updatePropagationVisibility() {
        if ($('#lxmf\\.enable_node').is(':checked')) {
            $('.propagation-dep').show();
            $('.propagation-dep-tab').show();
        } else {
            $('.propagation-dep').hide();
            $('.propagation-dep-tab').hide();
        }
    }

    // -----------------------------------------------------------------------
    // Cross-field validators
    // -----------------------------------------------------------------------

    /**
     * Validate that stamp_cost_target - stamp_cost_flexibility >= 13.
     */
    function checkStampFloor() {
        var target = parseInt($('#lxmf\\.stamp_cost_target').val(), 10);
        var flex = parseInt($('#lxmf\\.stamp_cost_flexibility').val(), 10);
        if (!isNaN(target) && !isNaN(flex)) {
            var floor = target - flex;
            if (floor < 13) {
                $('#stamp-floor-warn').text(
                    '{{ lang._("Anti-Spam Work Requirement minus Anti-Spam Tolerance Range must be at least 13. Current value: ") }}' +
                    floor + '.'
                ).show();
            } else {
                $('#stamp-floor-warn').hide();
            }
        }
    }

    /**
     * Validate that propagation_sync_max_size >= 40 * propagation_message_max_size.
     */
    function checkSyncSize() {
        var maxMsg = parseFloat($('#lxmf\\.propagation_message_max_size').val());
        var maxSync = parseFloat($('#lxmf\\.propagation_sync_max_size').val());
        if (!isNaN(maxMsg) && !isNaN(maxSync)) {
            var minSync = maxMsg * 40;
            if (maxSync < minSync) {
                $('#sync-size-min').text(minSync);
                $('#sync-size-warn').show();
            } else {
                $('#sync-size-warn').hide();
            }
        }
    }

    /**
     * Warn when from_static_only is checked but no static peers are configured.
     */
    function checkStaticOnlyWarn() {
        var staticOnly = $('#lxmf\\.from_static_only').is(':checked');
        var peers = $('#lxmf\\.static_peers').val();
        if (staticOnly && (!peers || peers.trim() === '')) {
            $('#static-only-warn').show();
        } else {
            $('#static-only-warn').hide();
        }
    }

    // -----------------------------------------------------------------------
    // Initialisation
    // -----------------------------------------------------------------------

    // Load settings from the API and populate the form
    ajaxCall('/api/reticulum/lxmd/get', {}, function(data, status) {
        mapDataToFormUI(data).done(function() {
            formatTokenizersUI();
            updatePropagationVisibility();
            checkStampFloor();
            checkSyncSize();
            checkStaticOnlyWarn();
            // Fetch both service statuses after the form is ready
            updateRnsdStatus();
            updateLxmdStatus();
        });
    });

    // Poll both service statuses every 10 seconds
    setInterval(function() {
        updateRnsdStatus();
        updateLxmdStatus();
    }, 10000);

    // -----------------------------------------------------------------------
    // Event bindings
    // -----------------------------------------------------------------------

    // lxmd service control buttons
    $('#lxmd-btn-start').click(function() {
        lxmdAction('/api/reticulum/service/lxmdStart', '{{ lang._("Start") }}');
    });
    $('#lxmd-btn-stop').click(function() {
        lxmdAction('/api/reticulum/service/lxmdStop', '{{ lang._("Stop") }}');
    });
    $('#lxmd-btn-restart').click(function() {
        lxmdAction('/api/reticulum/service/lxmdRestart', '{{ lang._("Restart") }}');
    });

    // Propagation fields visibility toggle
    $('#lxmf\\.enable_node').change(function() {
        updatePropagationVisibility();
    });

    // Stamp cost cross-field validation
    $('#lxmf\\.stamp_cost_target, #lxmf\\.stamp_cost_flexibility').on('input change', checkStampFloor);

    // Sync size validation
    $('#lxmf\\.propagation_message_max_size, #lxmf\\.propagation_sync_max_size').on('input change', checkSyncSize);

    // Static-only peering warning
    $('#lxmf\\.from_static_only').change(checkStaticOnlyWarn);
    $('#lxmf\\.static_peers').on('change', checkStaticOnlyWarn);

    // Save form data
    $('#saveBtn').click(function() {
        saveFormToEndpoint('/api/reticulum/lxmd/set', 'lxmf', function() {});
    });

    // Apply changes (triggers configd reconfigure for both services)
    $('#applyBtn').click(function() {
        ajaxCall('/api/reticulum/service/reconfigure', {}, function(data) {
            // Refresh both status badges after reconfigure settles
            setTimeout(function() {
                updateRnsdStatus();
                updateLxmdStatus();
            }, 1200);
            $('#apply-success-msg').fadeIn().delay(3000).fadeOut();
        });
    });

});
</script>

{% endblock %}
