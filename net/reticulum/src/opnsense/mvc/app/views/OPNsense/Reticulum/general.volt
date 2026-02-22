{#
    OPNsense Reticulum Plugin — General Settings View
    Controls RNSD and LXMF service enables and binding configuration.
#}

<script>
    $(document).ready(function () {
        // Load general settings (enable_rnsd, enable_lxmf, lxmf_bind_to_rnsd)
        var data_get_map = {'frm_GeneralSettings': '/api/reticulum/settings/get'};
        mapDataToFormUI(data_get_map).done(function () {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
            updateAdvancedVisibility();
        });

        // Load LXMF propagation enabled state separately (different model node)
        ajaxCall('/api/reticulum/settings/getPropagation', {}, function (data) {
            if (data && data.propagation) {
                var enabled = (data.propagation.enabled === '1' || data.propagation.enabled === true);
                $('#prop_enabled_toggle').prop('checked', enabled);
            }
        });

        // Load initial service status
        refreshServiceStatus();

        // Save without reconfigure
        $("#saveAct").click(function () {
            saveAllSettings(function () {
                $("#responseMsg").removeClass("hidden");
                setTimeout(function () { $("#responseMsg").addClass("hidden"); }, 3000);
            });
        });

        // Save and apply (reconfigure + restart services)
        $("#applyAct").click(function () {
            var $btn = $("#applyAct").prop('disabled', true);
            saveAllSettings(function () {
                ajaxCall('/api/reticulum/service/reconfigure', {}, function () {
                    refreshServiceStatus();
                    $btn.prop('disabled', false);
                });
            });
        });

        // Advanced mode toggle
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

    function saveAllSettings(callback) {
        // Step 1: save general settings (rnsd enable, lxmf enable, bind option)
        saveFormToEndpoint('/api/reticulum/settings/set', 'frm_GeneralSettings', function () {
            // Step 2: save propagation enabled state (separate model node)
            var propEnabled = $('#prop_enabled_toggle').is(':checked') ? '1' : '0';
            ajaxCall(
                '/api/reticulum/settings/setPropagation',
                {propagation: {enabled: propEnabled}},
                function () {
                    if (typeof callback === 'function') { callback(); }
                }
            );
        }, true);
    }

    function refreshServiceStatus() {
        ajaxCall('/api/reticulum/service/status', {}, function (data) {
            if (data) {
                updateDaemonBadge('#rnsd_status_badge', data.rnsd !== undefined ? data.rnsd : (data.status === 'running'));
                updateDaemonBadge('#lxmd_status_badge', data.lxmd !== undefined ? data.lxmd : false);
            }
        });
    }

    function updateDaemonBadge(selector, running) {
        if (running) {
            $(selector).html('<span class="label label-opnsense label-opnsense-xs label-success">{{ lang._("Running") }}</span>');
        } else {
            $(selector).html('<span class="label label-opnsense label-opnsense-xs label-danger">{{ lang._("Stopped") }}</span>');
        }
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum — General') }}</h3>
    </div>
    <div class="content-box-main">

        <!-- Daemon Status Summary -->
        <div class="row" style="margin-bottom:15px;">
            <div class="col-md-12">
                <table class="table table-condensed table-striped" style="margin-bottom:0; max-width:500px;">
                    <thead>
                        <tr>
                            <th>{{ lang._('Daemon') }}</th>
                            <th>{{ lang._('Description') }}</th>
                            <th>{{ lang._('Status') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>rnsd</strong></td>
                            <td><small>{{ lang._('Reticulum Network Daemon') }}</small></td>
                            <td><span id="rnsd_status_badge"><i class="fa fa-spinner fa-spin"></i></span></td>
                        </tr>
                        <tr>
                            <td><strong>lxmd</strong></td>
                            <td><small>{{ lang._('LXMF Messaging Daemon') }}</small></td>
                            <td><span id="lxmd_status_badge"><i class="fa fa-spinner fa-spin"></i></span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <hr/>

        <!-- Service Enable Settings (from generalForm / general model node) -->
        <div class="table-responsive">
            <form id="frm_GeneralSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': generalForm]) }}
            </form>
        </div>

        <!-- LXMF Propagation Enable (propagation model node, handled via JS) -->
        <div class="form-group">
            <label class="col-md-3 control-label">
                {{ lang._('Enable LXMF Propagation') }}
            </label>
            <div class="col-md-6">
                <input type="checkbox" id="prop_enabled_toggle">
                <p class="help-block">
                    {{ lang._('Enable the LXMF propagation node. When enabled, this system stores and forwards LXMF messages for offline recipients and synchronizes with peer propagation nodes. Requires the LXMF service to be enabled above. Configure detailed propagation settings in the LXMF section.') }}
                </p>
            </div>
        </div>

        <!-- Advanced toggle -->
        <hr/>
        <div style="margin-bottom:10px;">
            <label class="checkbox-inline">
                <input type="checkbox" id="showAdvanced">
                <strong>{{ lang._('Show Advanced Options') }}</strong>
            </label>
            <small class="text-muted" style="margin-left:8px;">
                {{ lang._('Reveals advanced configuration options not needed for most deployments.') }}
            </small>
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
