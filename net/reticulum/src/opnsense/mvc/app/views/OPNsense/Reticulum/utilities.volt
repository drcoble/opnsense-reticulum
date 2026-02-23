{#
    OPNsense Reticulum Plugin — Utilities View
    Tabbed interface for Reticulum CLI tools: rnstatus, rnid, rnpath,
    rnprobe, rnodeconf.
#}

<script>
    $(document).ready(function () {
        // Load rnstatus on first tab by default
        runUtility('rnstatus', {});

        // Tab activation triggers auto-run for read-only tools
        $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
            var tab = $(e.target).data('tab');
            if (tab === 'rnstatus') {
                runUtility('rnstatus', {});
            } else if (tab === 'rnid') {
                runUtility('rnid', {});
            } else if (tab === 'rnodeconf') {
                runUtility('rnodeconf', {});
            }
        });

        // rnstatus form
        $('#btn_rnstatus').click(function () {
            var detail = $('#rnstatus_detail').is(':checked') ? 1 : 0;
            runUtility('rnstatus', {detail: detail});
        });

        // rnid form
        $('#btn_rnid').click(function () {
            var hash = $('#rnid_hash').val().trim();
            runUtility('rnid', hash ? {hash: hash} : {});
        });

        // rnpath form
        $('#btn_rnpath').click(function () {
            var hash = $('#rnpath_hash').val().trim();
            if (!hash) { showError('#output_rnpath', '{{ lang._("Destination hash is required.") }}'); return; }
            runUtility('rnpath', {hash: hash});
        });

        // rnprobe form
        $('#btn_rnprobe').click(function () {
            var hash = $('#rnprobe_hash').val().trim();
            var timeout = parseInt($('#rnprobe_timeout').val()) || 10;
            if (!hash) { showError('#output_rnprobe', '{{ lang._("Destination hash is required.") }}'); return; }
            runUtility('rnprobe', {hash: hash, timeout: timeout});
        });

        // rnodeconf form
        $('#btn_rnodeconf').click(function () {
            var device = $('#rnodeconf_device').val().trim();
            runUtility('rnodeconf', device ? {device: device} : {});
        });
    });

    function runUtility(tool, params) {
        // Map tool names to API endpoints and their output element IDs
        var toolMap = {
            'rnstatus':   {endpoint: '/api/reticulum/utilities/rnstatus',   out: '#output_rnstatus'},
            'rnid':       {endpoint: '/api/reticulum/utilities/rnid',       out: '#output_rnid'},
            'rnpath':     {endpoint: '/api/reticulum/utilities/rnpath',     out: '#output_rnpath'},
            'rnprobe':    {endpoint: '/api/reticulum/utilities/rnprobe',    out: '#output_rnprobe'},
            'rnodeconf':  {endpoint: '/api/reticulum/utilities/rnodeconfig', out: '#output_rnodeconf'},
        };
        var config = toolMap[tool];
        if (!config) { return; }

        $(config.out).html('<i class="fa fa-spinner fa-spin"></i> {{ lang._("Running...") }}');

        // Use OPNsense ajaxCall (POST) for API calls
        ajaxCall(config.endpoint, params || {}, function (data) {
            if (data && data.status === 'ok' && data.data) {
                var d = data.data;
                var text = d.output || d.raw || JSON.stringify(d, null, 2);
                var cls = (d.success === false || (d.returncode !== undefined && d.returncode > 0)) ? 'text-danger' : '';
                $(config.out).html(
                    '<pre class="pre-scrollable utility-output ' + cls + '">' +
                    $('<span>').text(text).html() + '</pre>'
                );
            } else if (data && data.status === 'error') {
                showError(config.out, data.message || '{{ lang._("An error occurred.") }}');
            } else {
                showError(config.out, '{{ lang._("No response from service.") }}');
            }
        });
    }

    function showError(selector, msg) {
        $(selector).html('<div class="alert alert-danger">' + $('<span>').text(msg).html() + '</div>');
    }
</script>

<style>
    .utility-output {
        max-height: 400px;
        background: #1a1a2e;
        color: #e0e0e0;
        font-size: 12px;
        padding: 12px;
        border-radius: 4px;
        border: 1px solid #333;
    }
    .utility-output.text-danger {
        border-color: #d9534f;
        background: #2a1010;
    }
    .utility-input-row {
        margin-bottom: 10px;
    }
</style>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum — Utilities') }}</h3>
    </div>
    <div class="content-box-main">

        <div class="alert alert-info" role="alert" style="margin-bottom:15px;">
            <i class="fa fa-info-circle"></i>
            {{ lang._('Interactive interfaces for Reticulum CLI utilities. The Reticulum daemon (rnsd) must be running for most tools to function.') }}
        </div>

        <ul class="nav nav-tabs" role="tablist">
            <li role="presentation" class="active">
                <a href="#tab-rnstatus" data-tab="rnstatus" role="tab" data-toggle="tab">
                    <i class="fa fa-dashboard"></i> rnstatus
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-rnid" data-tab="rnid" role="tab" data-toggle="tab">
                    <i class="fa fa-id-card"></i> rnid
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-rnpath" data-tab="rnpath" role="tab" data-toggle="tab">
                    <i class="fa fa-road"></i> rnpath
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-rnprobe" data-tab="rnprobe" role="tab" data-toggle="tab">
                    <i class="fa fa-crosshairs"></i> rnprobe
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-rnodeconf" data-tab="rnodeconf" role="tab" data-toggle="tab">
                    <i class="fa fa-microchip"></i> rnodeconf
                </a>
            </li>
        </ul>

        <div class="tab-content" style="padding:15px;">

            <!-- rnstatus -->
            <div role="tabpanel" class="tab-pane active" id="tab-rnstatus">
                <h4>{{ lang._('rnstatus — Reticulum Network Status') }}</h4>
                <p class="text-muted">{{ lang._('Displays the current status of the Reticulum daemon and all configured interfaces.') }}</p>
                <div class="utility-input-row">
                    <label class="checkbox-inline">
                        <input type="checkbox" id="rnstatus_detail">
                        {{ lang._('Detailed output (-a)') }}
                    </label>
                    <button class="btn btn-primary btn-sm" id="btn_rnstatus" style="margin-left:15px;">
                        <i class="fa fa-play"></i> {{ lang._('Run') }}
                    </button>
                </div>
                <div id="output_rnstatus"></div>
            </div>

            <!-- rnid -->
            <div role="tabpanel" class="tab-pane" id="tab-rnid">
                <h4>{{ lang._('rnid — Identity Information') }}</h4>
                <p class="text-muted">{{ lang._('Shows the local Reticulum identity, or looks up a specific destination hash.') }}</p>
                <div class="utility-input-row">
                    <div class="input-group" style="max-width:500px; display:inline-flex;">
                        <span class="input-group-addon"><i class="fa fa-hashtag"></i></span>
                        <input type="text" class="form-control" id="rnid_hash"
                               placeholder="{{ lang._('Destination hash (32 hex chars) — leave empty for local identity') }}"
                               maxlength="32" pattern="[a-fA-F0-9]{32}">
                    </div>
                    <button class="btn btn-primary btn-sm" id="btn_rnid" style="margin-left:8px;">
                        <i class="fa fa-play"></i> {{ lang._('Run') }}
                    </button>
                </div>
                <div id="output_rnid"></div>
            </div>

            <!-- rnpath -->
            <div role="tabpanel" class="tab-pane" id="tab-rnpath">
                <h4>{{ lang._('rnpath — Path Query') }}</h4>
                <p class="text-muted">{{ lang._('Queries the path table to show the route to a specific Reticulum destination.') }}</p>
                <div class="utility-input-row">
                    <div class="input-group" style="max-width:500px; display:inline-flex;">
                        <span class="input-group-addon"><i class="fa fa-hashtag"></i></span>
                        <input type="text" class="form-control" id="rnpath_hash"
                               placeholder="{{ lang._('Destination hash (32 hex characters)') }}"
                               maxlength="32" pattern="[a-fA-F0-9]{32}" required>
                    </div>
                    <button class="btn btn-primary btn-sm" id="btn_rnpath" style="margin-left:8px;">
                        <i class="fa fa-play"></i> {{ lang._('Run') }}
                    </button>
                </div>
                <div id="output_rnpath"></div>
            </div>

            <!-- rnprobe -->
            <div role="tabpanel" class="tab-pane" id="tab-rnprobe">
                <h4>{{ lang._('rnprobe — Destination Probe') }}</h4>
                <p class="text-muted">{{ lang._('Probes a Reticulum destination to verify reachability and measure latency.') }}</p>
                <div class="utility-input-row">
                    <div class="input-group" style="max-width:500px; display:inline-flex;">
                        <span class="input-group-addon"><i class="fa fa-hashtag"></i></span>
                        <input type="text" class="form-control" id="rnprobe_hash"
                               placeholder="{{ lang._('Destination hash (32 hex characters)') }}"
                               maxlength="32" pattern="[a-fA-F0-9]{32}" required>
                    </div>
                    <div class="input-group" style="max-width:120px; display:inline-flex; margin-left:8px;">
                        <span class="input-group-addon">{{ lang._('Timeout') }}</span>
                        <input type="number" class="form-control" id="rnprobe_timeout"
                               value="10" min="1" max="60">
                        <span class="input-group-addon">s</span>
                    </div>
                    <button class="btn btn-primary btn-sm" id="btn_rnprobe" style="margin-left:8px;">
                        <i class="fa fa-play"></i> {{ lang._('Run') }}
                    </button>
                </div>
                <div id="output_rnprobe"></div>
            </div>

            <!-- rnodeconf -->
            <div role="tabpanel" class="tab-pane" id="tab-rnodeconf">
                <h4>{{ lang._('rnodeconf — RNode Configuration') }}</h4>
                <p class="text-muted">{{ lang._('Configure or inspect RNode LoRa hardware devices. Leave the device field empty to list all detected RNode devices.') }}</p>
                <div class="utility-input-row">
                    <div class="input-group" style="max-width:400px; display:inline-flex;">
                        <span class="input-group-addon"><i class="fa fa-microchip"></i></span>
                        <input type="text" class="form-control" id="rnodeconf_device"
                               placeholder="{{ lang._('Device path, e.g. /dev/ttyUSB0 (empty = list all)') }}">
                    </div>
                    <button class="btn btn-primary btn-sm" id="btn_rnodeconf" style="margin-left:8px;">
                        <i class="fa fa-play"></i> {{ lang._('Run') }}
                    </button>
                </div>
                <div id="output_rnodeconf"></div>
            </div>

        </div>
    </div>
</div>
