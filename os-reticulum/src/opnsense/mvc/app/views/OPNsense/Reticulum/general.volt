{#
    OPNsense Reticulum Plugin — General Settings
    Copyright (C) 2024 OPNsense Community
    SPDX-License-Identifier: BSD-2-Clause
#}

{% extends 'layouts/default.volt' %}

{% block content %}

<div id="service_status_container"></div>

<div id="rnsd-runtime-info" class="row" style="margin-top:8px;">
    <div class="col-sm-12">
        <small>
            <strong>{{ lang._('Version') }}:</strong> <span id="rnsd-version">{{ lang._('loading...') }}</span>
            &nbsp;|&nbsp;
            <strong>{{ lang._('Identity') }}:</strong>
            <span id="rnsd-identity" title="{{ lang._('Full hash shown on hover') }}">{{ lang._('loading...') }}</span>
            &nbsp;|&nbsp;
            <strong>{{ lang._('Uptime') }}:</strong> <span id="rnsd-uptime">{{ lang._('loading...') }}</span>
        </small>
    </div>
</div>

<ul class="nav nav-tabs" data-tabs="tabs" id="maintabs" style="margin-top:12px;">
    <li class="active"><a data-toggle="tab" href="#tab-general">{{ lang._('General') }}</a></li>
    <li><a data-toggle="tab" href="#tab-transport">{{ lang._('Transport') }}</a></li>
    <li><a data-toggle="tab" href="#tab-sharing">{{ lang._('Sharing') }}</a></li>
    <li><a data-toggle="tab" href="#tab-management">{{ lang._('Management') }}</a></li>
    <li><a data-toggle="tab" href="#tab-logging">{{ lang._('Logging') }}</a></li>
</ul>

<div class="tab-content content-box" style="padding:16px;">
    <form id="general" class="form-horizontal">

        {# ======================== General Tab ======================== #}
        <div id="tab-general" class="tab-pane fade in active">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.enabled" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Enable Reticulum Service') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="general.enabled" />
                    <div class="hidden" data-for="help_for_general.enabled">
                        <small>{{ lang._('Enable the Reticulum Network Stack daemon (rnsd). When disabled, all Reticulum interfaces and transport functionality are stopped. This must be enabled before any interfaces or the LXMF propagation node can function.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Transport Tab ======================== #}
        <div id="tab-transport" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.enable_transport" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Enable Transport Node') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="general.enable_transport" />
                    <div class="hidden" data-for="help_for_general.enable_transport">
                        <small>{{ lang._('When enabled, this device acts as a mesh router — relaying packets and participating in path discovery for the Reticulum network. Without this, the node only handles traffic for applications running locally.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.respond_to_probes" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Respond to Probes') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="general.respond_to_probes" />
                    <div class="hidden" data-for="help_for_general.respond_to_probes">
                        <small>{{ lang._('When enabled, rnsd replies to diagnostic probe packets from other nodes. Useful for network troubleshooting and reachability testing, but disabled by default for privacy (probes can reveal node existence).') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.panic_on_interface_error" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Stop Service on Interface Failure') }}
                    <span class="text-muted" style="font-weight:normal; font-size:0.9em;">({{ lang._('debug only') }})</span>
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="general.panic_on_interface_error" />
                    <div class="hidden" data-for="help_for_general.panic_on_interface_error">
                        <small>{{ lang._('When enabled, the Reticulum service stops if any configured interface encounters a fatal error. Recommended only for debugging — in production, leave this disabled so the service continues operating on surviving interfaces even if one fails (e.g. a disconnected serial radio).') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Sharing Tab ======================== #}
        <div id="tab-sharing" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.share_instance" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Allow Application Sharing') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="general.share_instance" />
                    <div class="hidden" data-for="help_for_general.share_instance">
                        <small>{{ lang._('Allow multiple applications on this machine (e.g. Nomad, Sideband) to share a single Reticulum connection via a local socket rather than each running their own instance. Almost always leave this enabled. Disable only if you need strict isolation between applications.') }}</small>
                    </div>
                </div>
            </div>

            <p id="sharing-disabled-msg" class="text-muted" style="display:none; margin-left:16px; margin-top:4px;">
                <i class="fa fa-info-circle"></i>
                {{ lang._('Port settings are hidden because Application Sharing is disabled.') }}
            </p>

            <div class="form-group share_instance_dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.shared_instance_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Application Sharing Port') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="general.shared_instance_port"
                           placeholder="37428" />
                    <div class="hidden" data-for="help_for_general.shared_instance_port">
                        <small>{{ lang._('TCP port used for inter-process communication between local applications and the shared Reticulum instance. Default: 37428. Must be unique — cannot match the Service Management Port.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group share_instance_dep">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.instance_control_port" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Service Management Port') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="general.instance_control_port"
                           placeholder="37429" />
                    <span class="text-danger small" id="port-conflict-msg" style="display:none;">
                        {{ lang._('Application Sharing Port and Service Management Port must be different.') }}
                    </span>
                    <div class="hidden" data-for="help_for_general.instance_control_port">
                        <small>{{ lang._('TCP port for the Reticulum service management API. Default: 37429. Must be unique — cannot match the Application Sharing Port. Rarely needs changing unless another service conflicts.') }}</small>
                    </div>
                </div>
            </div>
        </div>

        {# ======================== Management Tab ======================== #}
        <div id="tab-management" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.enable_remote_management" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Enable Remote Management') }}
                </label>
                <div class="col-sm-10">
                    <input type="checkbox" id="general.enable_remote_management" />
                    <div class="hidden" data-for="help_for_general.enable_remote_management">
                        <small>{{ lang._('Enable the remote management interface, allowing authorised administrators to manage this Reticulum node over the network. Requires at least one entry in Authorized Administrators. Disabled by default — only enable if you need remote administration.') }}</small>
                    </div>
                </div>
            </div>

            <div id="remote-mgmt-dep-fields">

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.remote_management_allowed" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Authorized Administrators') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="general.remote_management_allowed"
                           data-allownew="true"
                           data-nbdropdownelements="0"
                           data-placeholder="{{ lang._('Paste a 32-character hex identity hash and press Enter') }}"
                           data-error-msg="{{ lang._('%s is not a valid identity hash. Must be exactly 32 hex characters.') }}" />
                    <div class="hidden" data-for="help_for_general.remote_management_allowed">
                        <small>{{ lang._('Reticulum identity hashes of trusted administrators permitted to remotely manage this node. Each entry is a 32-character hexadecimal string identifying a Reticulum identity. Leave empty to allow no remote management even if the feature is enabled.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.rpc_key" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Remote Management Key') }}
                </label>
                <div class="col-sm-10">
                    <input type="password" class="form-control" id="general.rpc_key"
                           placeholder="{{ lang._('Enter new value to change (current value not shown)') }}" />
                    <div class="hidden" data-for="help_for_general.rpc_key">
                        <small>{{ lang._('Authentication key for the remote management interface. Enter a hex string (up to 128 characters). Leave blank to auto-generate a key on next startup. For security, the current value is never displayed. Enter a new value only if you want to change it; leave blank to keep the existing key. Store this key securely — it controls administrative access to the node.') }}</small>
                    </div>
                </div>
            </div>

            </div>{# /remote-mgmt-dep-fields #}

            <p id="remote-mgmt-disabled-msg" class="text-muted" style="display:none; margin-left:16px; margin-top:4px;">
                <i class="fa fa-info-circle"></i>
                {{ lang._('Administrator and key settings are hidden because Remote Management is disabled.') }}
            </p>
        </div>

        {# ======================== Logging Tab ======================== #}
        <div id="tab-logging" class="tab-pane fade">
            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.loglevel" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Log Level') }}
                </label>
                <div class="col-sm-10">
                    <select id="general.loglevel" class="form-control">
                        <option value="0">{{ lang._('Critical') }} (0)</option>
                        <option value="1">{{ lang._('Error') }} (1)</option>
                        <option value="2">{{ lang._('Warning') }} (2)</option>
                        <option value="3">{{ lang._('Notice') }} (3)</option>
                        <option value="4" selected="selected">{{ lang._('Info') }} (4)</option>
                        <option value="5">{{ lang._('Debug') }} (5)</option>
                        <option value="6">{{ lang._('Extreme') }} (6)</option>
                        <option value="7">{{ lang._('Trace') }} (7)</option>
                    </select>
                    <div class="hidden" data-for="help_for_general.loglevel">
                        <small>{{ lang._('Controls how much detail the Reticulum service writes to the log file. Higher levels produce more output and are useful for debugging. Select from: Critical, Error, Warning, Notice, Info (recommended), Debug, Extreme, Trace.') }}</small>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label class="col-sm-2 control-label">
                    <a id="help_for_general.logfile" href="#" class="showhelp"><i class="fa fa-info-circle"></i></a>
                    {{ lang._('Log File') }}
                </label>
                <div class="col-sm-10">
                    <input type="text" class="form-control" id="general.logfile"
                           placeholder="/var/log/reticulum/rnsd.log" />
                    <div class="hidden" data-for="help_for_general.logfile">
                        <small>{{ lang._('Absolute path to the Reticulum log file. Default: /var/log/reticulum/rnsd.log. The reticulum service user must have write access to this path. Changing this requires a service restart.') }}</small>
                    </div>
                </div>
            </div>
        </div>

    </form>

    {# ======================== Form Footer ======================== #}
    <div class="row">
        <div class="col-md-12 text-right">
            <button class="btn btn-primary" id="saveBtn" type="button">
                <i class="fa fa-floppy-o"></i> {{ lang._('Save') }}
            </button>
            <button class="btn btn-default" id="applyBtn" type="button"
                    title="{{ lang._('Saves and signals rnsd to reload its configuration. A full service restart may occur.') }}">
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

    /**
     * Fetch runtime info (version, identity, uptime) from the rnsd service
     * and update the info bar. Silently handles errors — the fields simply
     * remain at their last known value (or the initial dash).
     */
    function updateRnsdRuntimeInfo() {
        ajaxCall('/api/reticulum/service/rnsdInfo', {}, function(data) {
            if (data && data.version) {
                $('#rnsd-version').text(data.version);
            }
            if (data && data.identity) {
                var truncated = data.identity.length > 16
                    ? data.identity.substring(0, 16) + '...'
                    : data.identity;
                $('#rnsd-identity').text(truncated).attr('title', data.identity);
            }
            if (data && data.uptime) {
                $('#rnsd-uptime').text(data.uptime);
            }
        });
    }

    /**
     * Show or hide the port fields that depend on share_instance being enabled.
     */
    function updateShareInstanceVisibility() {
        if ($('#general\\.share_instance').is(':checked')) {
            $('.share_instance_dep').show();
            $('#sharing-disabled-msg').hide();
        } else {
            $('.share_instance_dep').hide();
            $('#sharing-disabled-msg').show();
        }
    }

    /**
     * Validate that the two port fields do not have the same value.
     */
    function checkPortConflict() {
        var p1 = $('#general\\.shared_instance_port').val();
        var p2 = $('#general\\.instance_control_port').val();
        if (p1 && p2 && p1 === p2) {
            $('#port-conflict-msg').show();
        } else {
            $('#port-conflict-msg').hide();
        }
    }

    // Load settings from the API and populate the form
    ajaxCall('/api/reticulum/rnsd/get', {}, function(data, status) {
        mapDataToFormUI(data).done(function() {
            formatTokenizersUI();
            updateShareInstanceVisibility();
            updateRemoteMgmtVisibility();
            checkPortConflict();
            updateServiceControlUI('reticulum');
            updateRnsdRuntimeInfo();
        });
    });

    // Refresh service status and runtime info every 10 seconds
    setInterval(function() {
        updateServiceControlUI('reticulum');
        updateRnsdRuntimeInfo();
    }, 10000);

    /**
     * Show or hide the remote management config fields based on the checkbox.
     */
    function updateRemoteMgmtVisibility() {
        if ($('#general\\.enable_remote_management').is(':checked')) {
            $('#remote-mgmt-dep-fields').show();
            $('#remote-mgmt-disabled-msg').hide();
        } else {
            $('#remote-mgmt-dep-fields').hide();
            $('#remote-mgmt-disabled-msg').show();
        }
    }

    // Toggle port field visibility when share_instance checkbox changes
    $('#general\\.share_instance').change(function() {
        updateShareInstanceVisibility();
    });

    // Toggle remote management config fields visibility
    $('#general\\.enable_remote_management').change(function() {
        updateRemoteMgmtVisibility();
    });

    // Port conflict validation on input
    $('#general\\.shared_instance_port, #general\\.instance_control_port').on('input change', checkPortConflict);

    // Save form data
    $('#saveBtn').click(function() {
        saveFormToEndpoint('/api/reticulum/rnsd/set', 'general', function() {});
    });

    // Apply changes (triggers configd reconfigure)
    $('#applyBtn').click(function() {
        ajaxCall('/api/reticulum/service/reconfigure', {}, function(data) {
            updateServiceControlUI('reticulum');
            $('#apply-success-msg').fadeIn().delay(3000).fadeOut();
        });
    });

});
</script>

{% endblock %}
