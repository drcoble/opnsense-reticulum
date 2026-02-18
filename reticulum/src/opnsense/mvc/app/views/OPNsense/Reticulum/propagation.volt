{#
    OPNsense Reticulum Plugin — Propagation Node (LXMF) Settings View
#}

<script>
    $(document).ready(function () {
        var data_get_map = {'frm_PropagationSettings': '/api/reticulum/settings/getPropagation'};
        mapDataToFormUI(data_get_map).done(function (data) {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
        });

        // Save propagation settings
        $("#saveAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/setPropagation', 'frm_PropagationSettings', function () {
                $("#responseMsg").removeClass("hidden");
                setTimeout(function () { $("#responseMsg").addClass("hidden"); }, 3000);
            }, true);
        });

        // Apply configuration
        $("#applyAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/setPropagation', 'frm_PropagationSettings', function () {
                ajaxCall('/api/reticulum/service/reconfigure', {}, function (data, status) {
                    updatePropagationStatus();
                });
            }, true);
        });

        // Initial propagation status check
        updatePropagationStatus();
    });

    function updatePropagationStatus() {
        ajaxCall('/api/reticulum/diagnostics/propagation', {}, function (data, status) {
            if (data && data.status === 'ok' && data.data) {
                var d = data.data;
                var html = '<table class="table table-condensed">';
                if (d.running !== undefined) {
                    html += '<tr><td><strong>Status</strong></td><td>' +
                        (d.running ? '<span class="label label-success">Running</span>' : '<span class="label label-danger">Stopped</span>') +
                        '</td></tr>';
                }
                if (d.message_count !== undefined) {
                    html += '<tr><td><strong>Stored Messages</strong></td><td>' + d.message_count + '</td></tr>';
                }
                if (d.peer_count !== undefined) {
                    html += '<tr><td><strong>Peered Nodes</strong></td><td>' + d.peer_count + '</td></tr>';
                }
                html += '</table>';
                $('#propagationStatusPanel').html(html);
            } else {
                $('#propagationStatusPanel').html('<span class="text-muted">Propagation node not running or status unavailable.</span>');
            }
        });
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('LXMF Propagation Node') }}</h3>
    </div>
    <div class="content-box-main">
        <div class="alert alert-info" role="alert">
            <p><i class="fa fa-info-circle"></i>
                {{ lang._('The LXMF propagation node provides store-and-forward messaging for the Reticulum network. When enabled, it stores messages for offline recipients and synchronizes with other propagation nodes. This requires the Reticulum daemon (rnsd) to be enabled and running.') }}
            </p>
        </div>

        <h4>{{ lang._('Propagation Node Status') }}</h4>
        <div id="propagationStatusPanel">
            <span class="text-muted">{{ lang._('Loading...') }}</span>
        </div>
        <hr/>

        <div class="table-responsive">
            <form id="frm_PropagationSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': propagationForm]) }}
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
