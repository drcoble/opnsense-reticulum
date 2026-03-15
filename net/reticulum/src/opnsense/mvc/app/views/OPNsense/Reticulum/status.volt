{#
    OPNsense Reticulum Plugin — Status View
    Tabbed status display: General, RNSD, LXMF, Propagation, Interfaces, Logs
#}

<script>
    var autoRefreshTimer = null;
    var logFilter = '';

    $(document).ready(function () {
        // Load the active tab on start
        loadTab('general');

        // Tab switch: load data for newly activated tab
        $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
            var tab = $(e.target).data('tab');
            loadTab(tab);
        });

        // Auto-refresh toggle
        $('#autoRefreshToggle').change(function () {
            if ($(this).is(':checked')) {
                autoRefreshTimer = setInterval(function () {
                    var activeTab = $('.nav-tabs .active a').data('tab');
                    loadTab(activeTab);
                }, 5000);
            } else {
                clearInterval(autoRefreshTimer);
                autoRefreshTimer = null;
            }
        });

        // Manual refresh
        $('#refreshBtn').click(function () {
            var activeTab = $('.nav-tabs .active a').data('tab');
            loadTab(activeTab);
        });

        // Log filter
        $('#logFilter').on('input', function () {
            logFilter = $(this).val().toLowerCase();
            applyLogFilter();
        });

        $(window).on('beforeunload', function () {
            if (autoRefreshTimer) { clearInterval(autoRefreshTimer); }
        });
    });

    function loadTab(tab) {
        switch (tab) {
            case 'general':     loadGeneralStatus(); break;
            case 'rnsd':        loadRNSDStatus(); break;
            case 'lxmf':        loadLXMFStatus(); break;
            case 'propagation': loadPropagationStatus(); break;
            case 'interfaces':  loadInterfacesStatus(); break;
            case 'logs':        loadLogs(); break;
        }
    }

    // ── General Status ────────────────────────────────────────────────────────
    function loadGeneralStatus() {
        setLoading('#tab-general .status-content');
        ajaxCall('/api/reticulum/diagnostics/generalStatus', {}, function (data) {
            if (!data || data.status !== 'ok' || !data.data) {
                setError('#tab-general .status-content', '{{ lang._("Service not running or data unavailable.") }}');
                return;
            }
            var d = data.data;
            var html = '';

            // Interface count summary
            html += '<div class="row"><div class="col-md-6">';
            html += '<h4>{{ lang._("Interface Summary") }}</h4>';
            html += '<table class="table table-condensed table-striped">';
            html += '<tbody>';
            html += '<tr><td>{{ lang._("Total Interfaces") }}</td><td><strong>' + (d.total_interfaces || 0) + '</strong></td></tr>';
            html += '<tr><td>{{ lang._("Enabled") }}</td><td><strong>' + (d.enabled_interfaces || 0) + '</strong></td></tr>';
            html += '<tr><td>{{ lang._("Currently Up") }}</td><td><strong>' + (d.up_interfaces || 0) + '</strong></td></tr>';
            html += '</tbody></table>';
            html += '</div>';

            // Bandwidth by medium type
            html += '<div class="col-md-6">';
            html += '<h4>{{ lang._("Bandwidth by Medium") }}</h4>';
            var mediums = d.bandwidth_by_medium || {};
            var mediumNames = {
                'udp': 'UDP', 'tcp': 'TCP', 'auto': 'Auto (mDNS)',
                'i2p': 'I2P', 'radio': 'Radio (LoRa/KISS)', 'serial': 'Serial', 'other': 'Other'
            };
            var hasMediums = Object.keys(mediums).length > 0;
            if (hasMediums) {
                html += '<table class="table table-condensed table-striped">';
                html += '<thead><tr><th>{{ lang._("Medium") }}</th><th>{{ lang._("TX") }}</th><th>{{ lang._("RX") }}</th></tr></thead>';
                html += '<tbody>';
                $.each(mediums, function (medium, stats) {
                    html += '<tr>';
                    html += '<td><strong>' + (mediumNames[medium] || medium) + '</strong></td>';
                    html += '<td>' + formatBytes(stats.tx || 0) + '</td>';
                    html += '<td>' + formatBytes(stats.rx || 0) + '</td>';
                    html += '</tr>';
                });
                html += '</tbody></table>';
            } else {
                html += '<p class="text-muted">{{ lang._("No interface bandwidth data available.") }}</p>';
            }
            html += '</div></div>';

            $('#tab-general .status-content').html(html);
        });
    }

    // ── RNSD Status ───────────────────────────────────────────────────────────
    function loadRNSDStatus() {
        setLoading('#tab-rnsd .status-content');
        ajaxCall('/api/reticulum/diagnostics/rnsdInfo', {}, function (data) {
            if (!data || data.status !== 'ok' || !data.data) {
                setError('#tab-rnsd .status-content', '{{ lang._("Service not running or data unavailable.") }}');
                return;
            }
            var d = data.data;
            var runningLabel = d.running
                ? '<span class="label label-success">{{ lang._("Running") }}</span>'
                : '<span class="label label-danger">{{ lang._("Stopped") }}</span>';
            var html = '<table class="table table-condensed table-striped" style="max-width:600px;">';
            html += '<tbody>';
            html += '<tr><td>{{ lang._("Status") }}</td><td>' + runningLabel + '</td></tr>';
            html += '<tr><td>{{ lang._("Version") }}</td><td><code>' + esc(d.version || 'unknown') + '</code></td></tr>';
            html += '<tr><td>{{ lang._("Uptime") }}</td><td>' + esc(d.uptime || '—') + '</td></tr>';
            html += '</tbody></table>';

            // Load path/node list
            html += '<h4>{{ lang._("Connected Nodes (Path Table)") }}</h4>';
            ajaxCall('/api/reticulum/diagnostics/paths', {}, function (pdata) {
                var pathHtml = '';
                if (pdata && pdata.status === 'ok' && Array.isArray(pdata.data)) {
                    if (pdata.data.length === 0) {
                        pathHtml = '<p class="text-muted">{{ lang._("No paths in table yet.") }}</p>';
                    } else {
                        pathHtml += '<table class="table table-condensed table-striped table-hover">';
                        pathHtml += '<thead><tr><th>{{ lang._("Destination Hash") }}</th><th>{{ lang._("Hops") }}</th><th>{{ lang._("Next Hop") }}</th><th>{{ lang._("Interface") }}</th><th>{{ lang._("Expires") }}</th></tr></thead>';
                        pathHtml += '<tbody>';
                        $.each(pdata.data, function (i, p) {
                            pathHtml += '<tr>';
                            pathHtml += '<td><code>' + esc(p.hash || '—') + '</code></td>';
                            pathHtml += '<td>' + esc(p.hops !== undefined ? String(p.hops) : '—') + '</td>';
                            pathHtml += '<td><code>' + esc(p.next_hop || '—') + '</code></td>';
                            pathHtml += '<td>' + esc(p.interface || '—') + '</td>';
                            pathHtml += '<td>' + esc(p.expires || '—') + '</td>';
                            pathHtml += '</tr>';
                        });
                        pathHtml += '</tbody></table>';
                    }
                } else if (pdata && pdata.status === 'ok' && pdata.data && pdata.data.raw) {
                    pathHtml = '<pre class="pre-scrollable">' + esc(pdata.data.raw) + '</pre>';
                } else {
                    pathHtml = '<p class="text-muted">{{ lang._("Path data unavailable.") }}</p>';
                }
                $('#tab-rnsd .status-content').html(html + pathHtml);
            });
        });
    }

    // ── LXMF Status ───────────────────────────────────────────────────────────
    function loadLXMFStatus() {
        setLoading('#tab-lxmf .status-content');
        ajaxCall('/api/reticulum/diagnostics/lxmfInfo', {}, function (data) {
            if (!data || data.status !== 'ok' || !data.data) {
                setError('#tab-lxmf .status-content', '{{ lang._("LXMF service not running or data unavailable.") }}');
                return;
            }
            var d = data.data;
            var runningLabel = d.running
                ? '<span class="label label-success">{{ lang._("Running") }}</span>'
                : '<span class="label label-danger">{{ lang._("Stopped") }}</span>';
            var html = '<table class="table table-condensed table-striped" style="max-width:600px;">';
            html += '<tbody>';
            html += '<tr><td>{{ lang._("Status") }}</td><td>' + runningLabel + '</td></tr>';
            html += '<tr><td>{{ lang._("Version") }}</td><td><code>' + esc(d.version || 'unknown') + '</code></td></tr>';
            html += '<tr><td>{{ lang._("Uptime") }}</td><td>' + esc(d.uptime || '—') + '</td></tr>';
            if (d.message_count !== undefined) {
                html += '<tr><td>{{ lang._("Messages in Store") }}</td><td>' + d.message_count + '</td></tr>';
            }
            html += '</tbody></table>';
            $('#tab-lxmf .status-content').html(html);
        });
    }

    // ── Propagation Status ────────────────────────────────────────────────────
    function loadPropagationStatus() {
        setLoading('#tab-propagation .status-content');
        ajaxCall('/api/reticulum/diagnostics/propagationDetail', {}, function (data) {
            if (!data || data.status !== 'ok' || !data.data) {
                setError('#tab-propagation .status-content', '{{ lang._("Propagation service data unavailable.") }}');
                return;
            }
            var d = data.data;
            var runningLabel = d.running
                ? '<span class="label label-success">{{ lang._("Running") }}</span>'
                : '<span class="label label-danger">{{ lang._("Stopped") }}</span>';

            var storagePct = d.storage_used_pct !== null && d.storage_used_pct !== undefined
                ? d.storage_used_pct + '%' : '—';
            var storageLimit = d.storage_limit_messages
                ? d.storage_limit_messages + ' {{ lang._("messages") }}' : '{{ lang._("Unlimited") }}';

            var html = '<table class="table table-condensed table-striped" style="max-width:700px;">';
            html += '<tbody>';
            html += '<tr><td style="width:240px;">{{ lang._("Status") }}</td><td>' + runningLabel + '</td></tr>';
            html += '<tr><td>{{ lang._("Messages in Store") }}</td><td>' + (d.message_count || 0) + '</td></tr>';
            html += '<tr><td>{{ lang._("Storage Used") }}</td><td>' + (d.storage_mb || 0) + ' MB</td></tr>';
            html += '<tr><td>{{ lang._("Storage Limit") }}</td><td>' + storageLimit + '</td></tr>';
            html += '<tr><td>{{ lang._("Storage Used (%)") }}</td><td>';
            if (d.storage_used_pct !== null && d.storage_used_pct !== undefined) {
                var pctClass = d.storage_used_pct > 90 ? 'danger' : (d.storage_used_pct > 70 ? 'warning' : 'success');
                html += '<div class="progress" style="margin-bottom:0; max-width:250px;">';
                html += '<div class="progress-bar progress-bar-' + pctClass + '" style="width:' + Math.min(100, d.storage_used_pct) + '%;">';
                html += d.storage_used_pct + '%</div></div>';
            } else {
                html += '—';
            }
            html += '</td></tr>';
            html += '<tr><td>{{ lang._("Active Peers") }}</td><td>' + (d.peer_count || 0) + '</td></tr>';
            html += '</tbody></table>';

            // Errors section
            if (d.errors && d.errors.length > 0) {
                html += '<h4>{{ lang._("Recent Errors") }}</h4>';
                html += '<ul class="list-unstyled">';
                $.each(d.errors, function (i, err) {
                    html += '<li><span class="label label-danger">{{ lang._("Error") }}</span> ' + esc(err) + '</li>';
                });
                html += '</ul>';
            }

            $('#tab-propagation .status-content').html(html);
        });
    }

    // ── Interfaces Status ─────────────────────────────────────────────────────
    function loadInterfacesStatus() {
        setLoading('#tab-interfaces .status-content');
        ajaxCall('/api/reticulum/diagnostics/interfacesDetail', {}, function (data) {
            if (!data || data.status !== 'ok') {
                setError('#tab-interfaces .status-content', '{{ lang._("Interface data unavailable.") }}');
                return;
            }
            var d = data.data;
            // If data is raw text, display it in a pre block
            if (d && d.raw) {
                $('#tab-interfaces .status-content').html(
                    '<pre class="pre-scrollable" style="max-height:500px;">' + esc(d.raw) + '</pre>'
                );
                return;
            }
            var interfaces = Array.isArray(d) ? d : (d && d.interfaces ? d.interfaces : []);
            if (interfaces.length === 0) {
                $('#tab-interfaces .status-content').html(
                    '<p class="text-muted">{{ lang._("No interface data available. Start the Reticulum daemon first.") }}</p>'
                );
                return;
            }

            var html = '<table class="table table-condensed table-striped table-hover">';
            html += '<thead><tr>';
            html += '<th>{{ lang._("Name") }}</th><th>{{ lang._("Type") }}</th><th>{{ lang._("Status") }}</th>';
            html += '<th>{{ lang._("TX") }}</th><th>{{ lang._("RX") }}</th>';
            html += '<th>{{ lang._("RSSI") }}</th><th>{{ lang._("SNR") }}</th><th>{{ lang._("Airtime") }}</th>';
            html += '</tr></thead><tbody>';
            $.each(interfaces, function (i, iface) {
                var statusLabel = iface.status === 'up'
                    ? '<span class="label label-success">{{ lang._("Up") }}</span>'
                    : '<span class="label label-danger">{{ lang._("Down") }}</span>';
                html += '<tr>';
                html += '<td><strong>' + esc(iface.name || '—') + '</strong></td>';
                html += '<td>' + esc(iface.type || '—') + '</td>';
                html += '<td>' + statusLabel + '</td>';
                html += '<td>' + formatBytes(iface.txb || 0) + '</td>';
                html += '<td>' + formatBytes(iface.rxb || 0) + '</td>';
                html += '<td>' + (iface.rssi !== undefined ? iface.rssi + ' dBm' : '—') + '</td>';
                html += '<td>' + (iface.snr !== undefined ? iface.snr + ' dB' : '—') + '</td>';
                html += '<td>' + (iface.airtime !== undefined ? iface.airtime + '%' : '—') + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';
            $('#tab-interfaces .status-content').html(html);
        });
    }

    // ── Logs ──────────────────────────────────────────────────────────────────
    function loadLogs() {
        setLoading('#tab-logs .log-container');
        ajaxCall('/api/reticulum/diagnostics/log', {}, function (data) {
            if (!data || data.status !== 'ok' || !data.data) {
                setError('#tab-logs .log-container', '{{ lang._("Log data unavailable.") }}');
                return;
            }
            var d = data.data;
            if (d.error) {
                setError('#tab-logs .log-container', d.error);
                return;
            }
            var lines = d.lines || [];
            if (lines.length === 0) {
                $('#tab-logs .log-container').html(
                    '<p class="text-muted">' + (d.message || '{{ lang._("No log data.") }}') + '</p>'
                );
                return;
            }

            // Store lines globally for filter
            window._logLines = lines;
            renderLogTable(lines);
        });
    }

    function renderLogTable(lines) {
        var html = '<table class="table table-condensed table-striped" id="logTable" style="font-size:11px; font-family:monospace;">';
        html += '<thead><tr><th style="width:30px;">#</th><th>{{ lang._("Log Entry") }}</th></tr></thead><tbody>';
        $.each(lines, function (i, line) {
            if (logFilter && line.toLowerCase().indexOf(logFilter) === -1) { return; }
            var cls = '';
            if (/error|critical|fatal/i.test(line)) { cls = 'danger'; }
            else if (/warning|warn/i.test(line)) { cls = 'warning'; }
            html += '<tr class="' + cls + '">';
            html += '<td class="text-muted">' + (i + 1) + '</td>';
            html += '<td>' + esc(line) + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';
        $('#tab-logs .log-container').html(html);
        // Scroll to bottom
        var container = $('#tab-logs .log-container');
        container.scrollTop(container[0].scrollHeight);
    }

    function applyLogFilter() {
        if (window._logLines) {
            renderLogTable(window._logLines);
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    function setLoading(selector) {
        $(selector).html('<i class="fa fa-spinner fa-spin"></i> {{ lang._("Loading...") }}');
    }

    function setError(selector, msg) {
        $(selector).html('<div class="alert alert-warning"><i class="fa fa-exclamation-triangle"></i> ' + esc(msg) + '</div>');
    }

    function esc(str) {
        return $('<span>').text(String(str)).html();
    }

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) { return '0 B'; }
        var k = 1024;
        var sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum — Status') }}
            <div class="pull-right">
                <label class="checkbox-inline" style="margin-right:10px; font-weight:normal;">
                    <input type="checkbox" id="autoRefreshToggle"> {{ lang._('Auto-refresh (5s)') }}
                </label>
                <button class="btn btn-default btn-xs" id="refreshBtn" type="button">
                    <i class="fa fa-refresh"></i> {{ lang._('Refresh') }}
                </button>
            </div>
        </h3>
    </div>
    <div class="content-box-main">

        <ul class="nav nav-tabs" role="tablist">
            <li role="presentation" class="active">
                <a href="#tab-general" data-tab="general" role="tab" data-toggle="tab">
                    <i class="fa fa-dashboard"></i> {{ lang._('General') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-rnsd" data-tab="rnsd" role="tab" data-toggle="tab">
                    <i class="fa fa-share-alt"></i> {{ lang._('RNSD') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-lxmf" data-tab="lxmf" role="tab" data-toggle="tab">
                    <i class="fa fa-envelope"></i> {{ lang._('LXMF') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-propagation" data-tab="propagation" role="tab" data-toggle="tab">
                    <i class="fa fa-arrows-alt"></i> {{ lang._('Propagation') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-interfaces" data-tab="interfaces" role="tab" data-toggle="tab">
                    <i class="fa fa-plug"></i> {{ lang._('Interfaces') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-logs" data-tab="logs" role="tab" data-toggle="tab">
                    <i class="fa fa-file-text-o"></i> {{ lang._('Logs') }}
                </a>
            </li>
        </ul>

        <div class="tab-content" style="padding:15px;">

            <!-- General Tab -->
            <div role="tabpanel" class="tab-pane active" id="tab-general">
                <div class="status-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>

            <!-- RNSD Tab -->
            <div role="tabpanel" class="tab-pane" id="tab-rnsd">
                <div class="status-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>

            <!-- LXMF Tab -->
            <div role="tabpanel" class="tab-pane" id="tab-lxmf">
                <div class="status-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>

            <!-- Propagation Tab -->
            <div role="tabpanel" class="tab-pane" id="tab-propagation">
                <div class="status-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>

            <!-- Interfaces Tab -->
            <div role="tabpanel" class="tab-pane" id="tab-interfaces">
                <div class="status-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>

            <!-- Logs Tab -->
            <div role="tabpanel" class="tab-pane" id="tab-logs">
                <div class="row" style="margin-bottom:10px;">
                    <div class="col-md-4">
                        <div class="input-group input-group-sm">
                            <span class="input-group-addon"><i class="fa fa-search"></i></span>
                            <input type="text" id="logFilter" class="form-control"
                                   placeholder="{{ lang._('Filter log entries...') }}">
                            <span class="input-group-btn">
                                <button class="btn btn-default" type="button" onclick="$('#logFilter').val(''); logFilter=''; applyLogFilter();">
                                    <i class="fa fa-times"></i>
                                </button>
                            </span>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <small class="text-muted">
                            <span class="label label-danger">{{ lang._('Red') }}</span> {{ lang._('= Error/Critical') }} &nbsp;
                            <span class="label label-warning">{{ lang._('Yellow') }}</span> {{ lang._('= Warning') }}
                        </small>
                    </div>
                </div>
                <div class="log-container" style="max-height:550px; overflow-y:auto; border:1px solid #ddd; border-radius:4px; padding:5px;">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>

        </div>
    </div>
</div>
