{#
    OPNsense Reticulum Plugin — RNS Configuration View
    All Reticulum daemon (rnsd) settings in order per the Reticulum User Guide.
#}

<script>
    $(document).ready(function () {
        var data_get_map = {'frm_RNSSettings': '/api/reticulum/settings/get'};
        mapDataToFormUI(data_get_map).done(function () {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
            updateAdvancedVisibility();
        });

        // Initial service status
        ajaxCall('/api/reticulum/service/status', {}, function (data) {
            updateServiceStatusUI(data);
        });

        // Save without reconfigure
        $("#saveAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_RNSSettings', function () {
                $("#responseMsg").removeClass("hidden");
                setTimeout(function () { $("#responseMsg").addClass("hidden"); }, 3000);
            }, true);
        });

        // Save + apply
        $("#applyAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_RNSSettings', function () {
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
        var running = data && (data.rnsd || data.status === 'running');
        if (running) {
            $("#rnsd_status_badge").html('<span class="label label-opnsense label-opnsense-xs label-success">{{ lang._("Running") }}</span>');
        } else {
            $("#rnsd_status_badge").html('<span class="label label-opnsense label-opnsense-xs label-danger">{{ lang._("Stopped") }}</span>');
        }
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum — RNS Configuration') }}
            <span id="rnsd_status_badge" class="pull-right"><i class="fa fa-spinner fa-spin"></i></span>
        </h3>
    </div>
    <div class="content-box-main">

        <div class="alert alert-info" role="alert" style="margin-bottom:15px;">
            <p>
                <i class="fa fa-info-circle"></i>
                {{ lang._('These settings configure the Reticulum network daemon (rnsd). They correspond to the [reticulum] section of the Reticulum configuration file. Interface-specific settings are configured in the Interfaces section.') }}
            </p>
        </div>

        <!-- Advanced toggle -->
        <div style="margin-bottom:12px;">
            <label class="checkbox-inline">
                <input type="checkbox" id="showAdvanced">
                <strong>{{ lang._('Show Advanced Settings') }}</strong>
            </label>
            <small class="text-muted" style="margin-left:8px;">
                {{ lang._('Advanced settings are hidden by default. Enable only if you need to customise instance ports, error behaviour, or outgoing interface settings.') }}
            </small>
        </div>

        <div class="table-responsive">
            <form id="frm_RNSSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': rnsForm]) }}
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
