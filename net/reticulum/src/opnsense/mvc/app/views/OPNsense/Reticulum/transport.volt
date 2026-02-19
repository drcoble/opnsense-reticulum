{#
    OPNsense Reticulum Plugin — Transport Node Settings View
#}

<script>
    $(document).ready(function () {
        var data_get_map = {'frm_TransportSettings': '/api/reticulum/settings/get'};
        mapDataToFormUI(data_get_map).done(function (data) {
            formatTokenizersUI();
            $('.selectpicker').selectpicker('refresh');
        });

        // Save transport settings (part of general settings)
        $("#saveAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_TransportSettings', function () {
                $("#responseMsg").removeClass("hidden");
                setTimeout(function () { $("#responseMsg").addClass("hidden"); }, 3000);
            }, true);
        });

        // Apply configuration
        $("#applyAct").click(function () {
            saveFormToEndpoint('/api/reticulum/settings/set', 'frm_TransportSettings', function () {
                ajaxCall('/api/reticulum/service/reconfigure', {}, function (data, status) {
                    // done
                });
            }, true);
        });

        // Load interface announce rate summary
        ajaxCall('/api/reticulum/settings/searchInterface', {}, function (data, status) {
            if (data.rows && data.rows.length > 0) {
                var tbody = '';
                $.each(data.rows, function (idx, row) {
                    tbody += '<tr>';
                    tbody += '<td>' + $('<span>').text(row.name).html() + '</td>';
                    tbody += '<td>' + $('<span>').text(row.interfaceType).html() + '</td>';
                    tbody += '<td>' + $('<span>').text(row.enabled === '1' ? 'Yes' : 'No').html() + '</td>';
                    tbody += '</tr>';
                });
                $('#interfaceSummaryBody').html(tbody);
            } else {
                $('#interfaceSummaryBody').html('<tr><td colspan="3">No interfaces configured.</td></tr>');
            }
        });
    });
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Transport Node Configuration') }}</h3>
    </div>
    <div class="content-box-main">
        <div class="alert alert-info" role="alert">
            <h4><i class="fa fa-info-circle"></i> {{ lang._('Transport Node Best Practices') }}</h4>
            <ul>
                <li><strong>{{ lang._('Stationary:') }}</strong> {{ lang._('Transport nodes must remain in fixed locations for reliable routing.') }}</li>
                <li><strong>{{ lang._('Always-on:') }}</strong> {{ lang._('Keep transport nodes running continuously for network stability.') }}</li>
                <li><strong>{{ lang._('Well-connected:') }}</strong> {{ lang._('Place transport nodes where they can reach multiple network segments.') }}</li>
                <li><strong>{{ lang._('Strategic placement:') }}</strong> {{ lang._('Only enable transport on nodes that provide connectivity between segments. Not every node should be a transport node.') }}</li>
                <li><strong>{{ lang._('Announce rates:') }}</strong> {{ lang._('Configure per-interface announce rate limits in the Interfaces tab to control bandwidth usage.') }}</li>
            </ul>
            <p>{{ lang._('Transport nodes maintain path tables, forward packets across multiple hops, and propagate announcements throughout the network. They act as distributed cryptographic keystores by caching public keys from announcements. A maximum of 128 hops is supported.') }}</p>
        </div>

        <div class="table-responsive">
            <form id="frm_TransportSettings" class="form-inline">
                {{ partial("layout_partials/base_form", ['fields': transportForm]) }}
            </form>
        </div>

        <hr/>
        <h4>{{ lang._('Configured Interfaces Summary') }}</h4>
        <table class="table table-condensed table-hover table-striped">
            <thead>
                <tr>
                    <th>{{ lang._('Name') }}</th>
                    <th>{{ lang._('Type') }}</th>
                    <th>{{ lang._('Enabled') }}</th>
                </tr>
            </thead>
            <tbody id="interfaceSummaryBody">
                <tr><td colspan="3">{{ lang._('Loading...') }}</td></tr>
            </tbody>
        </table>
        <p><a href="/ui/reticulum/interfaces"><i class="fa fa-arrow-right"></i> {{ lang._('Manage interfaces and announce rate settings') }}</a></p>
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
