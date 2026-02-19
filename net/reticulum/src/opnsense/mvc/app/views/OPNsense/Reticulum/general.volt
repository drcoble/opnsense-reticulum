{#
    OPNsense Reticulum Plugin — General Settings View
#}

<script>
    $(document).ready(function () {
        var data_get_map = {'frm_GeneralSettings': '/api/reticulum/settings/get'};
        mapDataToFormUI(data_get_map).done(function (data) {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
        });

        // Save general settings
        $("#saveAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_GeneralSettings', function () {
                $("#responseMsg").removeClass("hidden");
                setTimeout(function () { $("#responseMsg").addClass("hidden"); }, 3000);
            }, true);
        });

        // Apply configuration (save + reconfigure service)
        $("#applyAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_GeneralSettings', function () {
                ajaxCall('/api/reticulum/service/reconfigure', {}, function (data, status) {
                    ajaxCall('/api/reticulum/service/status', {}, function (data, status) {
                        updateServiceStatusUI(data);
                    });
                });
            }, true);
        });

        // Initial service status check
        ajaxCall('/api/reticulum/service/status', {}, function (data, status) {
            updateServiceStatusUI(data);
        });
    });

    function updateServiceStatusUI(data) {
        var statusHtml;
        if (data['status'] === 'running') {
            statusHtml = '<span class="label label-opnsense label-opnsense-xs label-success pull-right">Running</span>';
        } else {
            statusHtml = '<span class="label label-opnsense label-opnsense-xs label-danger pull-right">Stopped</span>';
        }
        $("#service_status_container").html(statusHtml);
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum General Settings') }}
            <span id="service_status_container" class="pull-right"></span>
        </h3>
    </div>
    <div class="content-box-main">
        <div class="table-responsive">
            <form id="frm_GeneralSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': generalForm]) }}
            </form>
        </div>
    </div>
    <div class="content-box-footer">
        <div id="responseMsg" class="alert alert-info hidden" role="alert">
            {{ lang._('Settings saved successfully.') }}
        </div>
        <button class="btn btn-primary" id="saveAct" type="button">
            <b>{{ lang._('Save') }}</b> <i id="saveAct_progress" class=""></i>
        </button>
        <button class="btn btn-primary" id="applyAct" type="button">
            <b>{{ lang._('Apply') }}</b> <i id="applyAct_progress" class=""></i>
        </button>
    </div>
</div>
