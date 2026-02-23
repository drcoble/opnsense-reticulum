{#
    OPNsense Reticulum Plugin — General Settings View
    Displays RNSD service status and provides start/stop/restart controls.
#}

<script>
    $(document).ready(function () {
        // Load general settings into the form
        var data_get_map = {'frm_GeneralSettings': '/api/reticulum/settings/get'};
        mapDataToFormUI(data_get_map).done(function () {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
            updateAdvancedVisibility();
        });

        // Load initial service status
        refreshServiceStatus();

        // Save without reconfigure
        $('#saveAct').click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_GeneralSettings', function () {
                $('#responseMsg').removeClass('hidden');
                setTimeout(function () { $('#responseMsg').addClass('hidden'); }, 3000);
            }, true);
        });

        // Save and apply: write config then reconfigure (template reload + restart)
        $('#applyAct').click(function () {
            var $btn = $(this).prop('disabled', true);
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_GeneralSettings', function () {
                ajaxCall('/api/reticulum/service/reconfigure', {}, function () {
                    setTimeout(function () {
                        refreshServiceStatus();
                        $btn.prop('disabled', false);
                    }, 2000);
                });
            }, true);
        });

        // Service control buttons
        $('#startAct').click(function () {
            serviceAction('start', 1500);
        });
        $('#stopAct').click(function () {
            serviceAction('stop', 1500);
        });
        $('#restartAct').click(function () {
            serviceAction('restart', 2500);
        });

        // Advanced mode toggle
        $('#showAdvanced').change(function () {
            updateAdvancedVisibility();
        });
    });

    /**
     * Call a service control action and refresh status after a delay.
     */
    function serviceAction(action, delay) {
        setStatusSpinner();
        disableServiceButtons(true);
        ajaxCall('/api/reticulum/service/' + action, {}, function () {
            setTimeout(function () {
                refreshServiceStatus();
                disableServiceButtons(false);
            }, delay);
        });
    }

    function disableServiceButtons(disabled) {
        $('#startAct, #stopAct, #restartAct').prop('disabled', disabled);
    }

    function setStatusSpinner() {
        $('#rnsd_status_badge').html('<i class="fa fa-spinner fa-spin"></i>');
    }

    function refreshServiceStatus() {
        ajaxCall('/api/reticulum/service/status', {}, function (data) {
            var running  = false;
            var disabled = false;
            if (data) {
                if (data.status === 'disabled') {
                    disabled = true;
                } else {
                    running = (data.rnsd === true || data.status === 'running');
                }
            }
            renderStatusBadge(running, disabled);
        });
    }

    function renderStatusBadge(running, disabled) {
        var $badge = $('#rnsd_status_badge');
        if (disabled) {
            $badge.html(
                '<span class="label label-opnsense label-opnsense-xs label-default">' +
                '{{ lang._("Disabled") }}</span>'
            );
        } else if (running) {
            $badge.html(
                '<span class="label label-opnsense label-opnsense-xs label-success">' +
                '{{ lang._("Running") }}</span>'
            );
        } else {
            $badge.html(
                '<span class="label label-opnsense label-opnsense-xs label-danger">' +
                '{{ lang._("Stopped") }}</span>'
            );
        }
    }

    function updateAdvancedVisibility() {
        if ($('#showAdvanced').is(':checked')) {
            $('.advanced-setting').slideDown(150);
        } else {
            $('.advanced-setting').slideUp(150);
        }
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum — General') }}
            <span id="rnsd_status_badge" class="pull-right">
                <i class="fa fa-spinner fa-spin"></i>
            </span>
        </h3>
    </div>
    <div class="content-box-main">

        <!-- Service Control Buttons -->
        <div class="row" style="margin-bottom: 15px;">
            <div class="col-md-12">
                <button class="btn btn-sm btn-success" id="startAct" type="button">
                    <i class="fa fa-play"></i> {{ lang._('Start') }}
                </button>
                <button class="btn btn-sm btn-danger" id="stopAct" type="button" style="margin-left: 4px;">
                    <i class="fa fa-stop"></i> {{ lang._('Stop') }}
                </button>
                <button class="btn btn-sm btn-warning" id="restartAct" type="button" style="margin-left: 4px;">
                    <i class="fa fa-refresh"></i> {{ lang._('Restart') }}
                </button>
                <small class="text-muted" style="margin-left: 12px;">
                    {{ lang._('Use Apply to save settings and restart the service.') }}
                </small>
            </div>
        </div>

        <hr/>

        <!-- General Settings Form (Enable RNSD + advanced options from rns.xml) -->
        <div class="table-responsive">
            <form id="frm_GeneralSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': generalForm]) }}
            </form>
        </div>

        <!-- Advanced toggle -->
        <hr/>
        <div style="margin-bottom: 10px;">
            <label class="checkbox-inline">
                <input type="checkbox" id="showAdvanced">
                <strong>{{ lang._('Show Advanced Options') }}</strong>
            </label>
            <small class="text-muted" style="margin-left: 8px;">
                {{ lang._('Reveals advanced configuration options not needed for most deployments.') }}
            </small>
        </div>

    </div>
    <div class="content-box-footer">
        <div id="responseMsg" class="alert alert-info hidden" role="alert">
            {{ lang._('Settings saved. Click Apply to put changes into effect.') }}
        </div>
        <button class="btn btn-primary" id="saveAct" type="button">
            <b>{{ lang._('Save') }}</b> <i id="saveAct_progress"></i>
        </button>
        <button class="btn btn-primary" id="applyAct" type="button" style="margin-left: 4px;">
            <b>{{ lang._('Apply') }}</b> <i id="applyAct_progress"></i>
        </button>
    </div>
</div>
