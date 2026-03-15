{#
    OPNsense Reticulum Plugin — LXMF Configuration View
    All LXMF daemon (lxmd) settings including propagation node configuration.
    Read-only fields derived from RNSD config are shown with an indicator.
#}

<script>
    $(document).ready(function () {
        // Load LXMF/propagation settings
        var data_get_map = {'frm_LXMFSettings': '/api/reticulum/settings/getPropagation'};
        mapDataToFormUI(data_get_map).done(function () {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
            updateAdvancedVisibility();
        });

        // Load RNS-derived read-only values
        ajaxCall('/api/reticulum/settings/get', {}, function (data) {
            if (data && data.general) {
                var port = data.general.shared_instance_port || '37428';
                $('#rns_shared_port_display').text(port);
                var shareEnabled = (data.general.share_instance === '1');
                if (!shareEnabled) {
                    $('#rns_share_warning').show();
                }
            }
        });

        // Initial service status
        ajaxCall('/api/reticulum/service/status', {}, function (data) {
            updateServiceStatusUI(data);
        });

        // Save without reconfigure
        $("#saveAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/setPropagation', 'frm_LXMFSettings', function () {
                $("#responseMsg").removeClass("hidden");
                setTimeout(function () { $("#responseMsg").addClass("hidden"); }, 3000);
            }, true);
        });

        // Save + apply
        $("#applyAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/setPropagation', 'frm_LXMFSettings', function () {
                ajaxCall('/api/reticulum/service/reconfigure', {}, function () {
                    ajaxCall('/api/reticulum/service/status', {}, function (data) {
                        updateServiceStatusUI(data);
                    });
                });
            }, true);
        });

        // Advanced toggle
        $('#showAdvanced').change(function () {
            updateAdvancedVisibility();
        });
    });

    function updateAdvancedVisibility() {
        if ($('#showAdvanced').is(':checked')) {
            $('.advanced-setting').slideDown(150);
        } else {
            $('.advanced-setting').slideUp(150);
        }
    }

    function updateServiceStatusUI(data) {
        var lxmdRunning = data && (data.lxmd === true);
        var rnsdRunning = data && (data.rnsd === true || data.status === 'running');

        if (lxmdRunning) {
            $("#lxmd_status_badge").html('<span class="label label-opnsense label-opnsense-xs label-success">{{ lang._("Running") }}</span>');
        } else {
            $("#lxmd_status_badge").html('<span class="label label-opnsense label-opnsense-xs label-danger">{{ lang._("Stopped") }}</span>');
        }

        if (!rnsdRunning) {
            $('#rnsd_dependency_warning').show();
        } else {
            $('#rnsd_dependency_warning').hide();
        }
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum — LXMF Configuration') }}
            <span id="lxmd_status_badge" class="pull-right"><i class="fa fa-spinner fa-spin"></i></span>
        </h3>
    </div>
    <div class="content-box-main">

        <!-- RNSD dependency warning -->
        <div id="rnsd_dependency_warning" class="alert alert-warning" style="display:none;" role="alert">
            <i class="fa fa-exclamation-triangle"></i>
            {{ lang._('The RNSD service is not running. The LXMF service requires RNSD to be running (when binding is enabled). Start RNSD from the General section or via the Services dashboard.') }}
        </div>

        <div class="alert alert-info" role="alert" style="margin-bottom:15px;">
            <i class="fa fa-info-circle"></i>
            {{ lang._('These settings configure the LXMF messaging daemon (lxmd). The LXMF service must be enabled in the General section. Enable the service and configure binding in General, then configure LXMF behaviour here.') }}
        </div>

        <!-- RNS-Derived Read-Only Values -->
        <div class="panel panel-default" style="margin-bottom:15px;">
            <div class="panel-heading">
                <h4 class="panel-title">
                    <i class="fa fa-lock"></i>
                    {{ lang._('RNS-Derived Settings') }}
                    <small class="text-muted" style="font-weight:normal; margin-left:8px;">
                        {{ lang._('These values are inherited from the RNS configuration and cannot be overridden here.') }}
                    </small>
                </h4>
            </div>
            <div class="panel-body">
                <table class="table table-condensed" style="margin-bottom:0;">
                    <thead>
                        <tr>
                            <th style="width:260px;">{{ lang._('Setting') }}</th>
                            <th>{{ lang._('Value') }}</th>
                            <th>{{ lang._('Source') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{{ lang._('Shared Instance Port') }}</td>
                            <td>
                                <code id="rns_shared_port_display">—</code>
                            </td>
                            <td>
                                <span class="label label-default">
                                    <i class="fa fa-link"></i> {{ lang._('Derived from RNS config') }}
                                </span>
                                <small class="text-muted" style="margin-left:6px;">
                                    {{ lang._('lxmd connects to rnsd on this port. Change via') }}
                                    <a href="/ui/reticulum/rns">{{ lang._('RNS › Advanced') }}</a>.
                                </small>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div id="rns_share_warning" class="alert alert-warning" style="display:none; margin-top:10px; margin-bottom:0;">
                    <i class="fa fa-exclamation-triangle"></i>
                    {{ lang._('Share Instance is disabled in the RNS configuration. The LXMF daemon requires Share Instance to be enabled to connect to the local rnsd. Enable it in the RNS section.') }}
                </div>
            </div>
        </div>

        <!-- Advanced toggle -->
        <div style="margin-bottom:12px;">
            <label class="checkbox-inline">
                <input type="checkbox" id="showAdvanced">
                <strong>{{ lang._('Show Advanced Settings') }}</strong>
            </label>
        </div>

        <!-- LXMF/Propagation Settings Form -->
        <div class="table-responsive">
            <form id="frm_LXMFSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': lxmfForm]) }}
            </form>
        </div>
    </div>
    <div class="content-box-footer">
        <div id="responseMsg" class="alert alert-info hidden" role="alert">
            {{ lang._('Settings saved successfully.') }}
        </div>
        <button class="btn btn-primary" id="saveAct" type="button">
            <b>{{ lang._('Save') }}</b> <i id="saveAct_progress"></i>
        </button>
        <button class="btn btn-primary" id="applyAct" type="button">
            <b>{{ lang._('Apply') }}</b> <i id="applyAct_progress"></i>
        </button>
    </div>
</div>
