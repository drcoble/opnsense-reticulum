{#
    OPNsense Reticulum Plugin — Diagnostics View
#}

<script>
    var autoRefreshTimer = null;

    $(document).ready(function () {
        // Load initial data for the active tab
        loadDiagnosticTab('status');

        // Tab click handlers
        $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
            var tab = $(e.target).attr('href').replace('#tab-', '');
            loadDiagnosticTab(tab);
        });

        // Auto-refresh toggle
        $('#autoRefreshToggle').change(function () {
            if ($(this).is(':checked')) {
                autoRefreshTimer = setInterval(function () {
                    var activeTab = $('.nav-tabs .active a').attr('href').replace('#tab-', '');
                    loadDiagnosticTab(activeTab);
                }, 5000);
            } else {
                if (autoRefreshTimer) {
                    clearInterval(autoRefreshTimer);
                    autoRefreshTimer = null;
                }
            }
        });

        // Manual refresh button
        $('#refreshBtn').click(function () {
            var activeTab = $('.nav-tabs .active a').attr('href').replace('#tab-', '');
            loadDiagnosticTab(activeTab);
        });
    });

    function loadDiagnosticTab(tab) {
        var endpoint;
        switch (tab) {
            case 'status':
                endpoint = '/api/reticulum/diagnostics/rnstatus';
                break;
            case 'interfaces':
                endpoint = '/api/reticulum/diagnostics/interfaces';
                break;
            case 'paths':
                endpoint = '/api/reticulum/diagnostics/paths';
                break;
            case 'announces':
                endpoint = '/api/reticulum/diagnostics/announces';
                break;
            case 'propagation':
                endpoint = '/api/reticulum/diagnostics/propagation';
                break;
            default:
                return;
        }

        $('#tab-' + tab + ' .diagnostics-content').html('<i class="fa fa-spinner fa-spin"></i> Loading...');

        ajaxCall(endpoint, {}, function (data, status) {
            var content;
            if (data && data.status === 'ok' && data.data) {
                if (data.data.raw) {
                    // Fallback: raw text output
                    content = '<pre class="pre-scrollable">' + $('<span>').text(data.data.raw).html() + '</pre>';
                } else {
                    content = renderDiagnosticData(tab, data.data);
                }
            } else {
                content = '<div class="alert alert-warning">Service not running or data unavailable.</div>';
            }
            $('#tab-' + tab + ' .diagnostics-content').html(content);
        });
    }

    function renderDiagnosticData(tab, data) {
        var html = '';

        if (tab === 'status') {
            html += '<table class="table table-condensed table-striped">';
            $.each(data, function (key, value) {
                html += '<tr><td><strong>' + $('<span>').text(key).html() + '</strong></td>';
                html += '<td>' + $('<span>').text(String(value)).html() + '</td></tr>';
            });
            html += '</table>';
        } else if (tab === 'interfaces') {
            if (Array.isArray(data)) {
                html += '<table class="table table-condensed table-striped table-hover">';
                html += '<thead><tr><th>Name</th><th>Type</th><th>Status</th><th>TX</th><th>RX</th><th>RSSI</th><th>SNR</th></tr></thead>';
                html += '<tbody>';
                $.each(data, function (idx, iface) {
                    html += '<tr>';
                    html += '<td>' + $('<span>').text(iface.name || '-').html() + '</td>';
                    html += '<td>' + $('<span>').text(iface.type || '-').html() + '</td>';
                    html += '<td>' + (iface.status === 'up' ? '<span class="label label-success">Up</span>' : '<span class="label label-danger">Down</span>') + '</td>';
                    html += '<td>' + $('<span>').text(formatBytes(iface.txb || 0)).html() + '</td>';
                    html += '<td>' + $('<span>').text(formatBytes(iface.rxb || 0)).html() + '</td>';
                    html += '<td>' + $('<span>').text(iface.rssi !== undefined ? iface.rssi + ' dBm' : '-').html() + '</td>';
                    html += '<td>' + $('<span>').text(iface.snr !== undefined ? iface.snr + ' dB' : '-').html() + '</td>';
                    html += '</tr>';
                });
                html += '</tbody></table>';
            } else {
                html += '<pre>' + $('<span>').text(JSON.stringify(data, null, 2)).html() + '</pre>';
            }
        } else if (tab === 'paths') {
            if (Array.isArray(data)) {
                html += '<table class="table table-condensed table-striped table-hover">';
                html += '<thead><tr><th>Destination</th><th>Hops</th><th>Next Hop</th><th>Interface</th><th>Expires</th></tr></thead>';
                html += '<tbody>';
                $.each(data, function (idx, path) {
                    html += '<tr>';
                    html += '<td><code>' + $('<span>').text(path.hash || '-').html() + '</code></td>';
                    html += '<td>' + $('<span>').text(path.hops !== undefined ? path.hops : '-').html() + '</td>';
                    html += '<td><code>' + $('<span>').text(path.next_hop || '-').html() + '</code></td>';
                    html += '<td>' + $('<span>').text(path.interface || '-').html() + '</td>';
                    html += '<td>' + $('<span>').text(path.expires || '-').html() + '</td>';
                    html += '</tr>';
                });
                html += '</tbody></table>';
            } else {
                html += '<pre>' + $('<span>').text(JSON.stringify(data, null, 2)).html() + '</pre>';
            }
        } else if (tab === 'announces') {
            if (Array.isArray(data)) {
                html += '<table class="table table-condensed table-striped table-hover">';
                html += '<thead><tr><th>Timestamp</th><th>Destination Hash</th><th>Hops</th><th>Interface</th></tr></thead>';
                html += '<tbody>';
                $.each(data, function (idx, ann) {
                    html += '<tr>';
                    html += '<td>' + $('<span>').text(ann.timestamp || '-').html() + '</td>';
                    html += '<td><code>' + $('<span>').text(ann.hash || '-').html() + '</code></td>';
                    html += '<td>' + $('<span>').text(ann.hops !== undefined ? ann.hops : '-').html() + '</td>';
                    html += '<td>' + $('<span>').text(ann.interface || '-').html() + '</td>';
                    html += '</tr>';
                });
                html += '</tbody></table>';
            } else {
                html += '<pre>' + $('<span>').text(JSON.stringify(data, null, 2)).html() + '</pre>';
            }
        } else if (tab === 'propagation') {
            html += '<table class="table table-condensed table-striped">';
            $.each(data, function (key, value) {
                html += '<tr><td><strong>' + $('<span>').text(key).html() + '</strong></td>';
                if (typeof value === 'object') {
                    html += '<td><pre>' + $('<span>').text(JSON.stringify(value, null, 2)).html() + '</pre></td>';
                } else {
                    html += '<td>' + $('<span>').text(String(value)).html() + '</td>';
                }
                html += '</tr>';
            });
            html += '</table>';
        }

        return html || '<pre>' + $('<span>').text(JSON.stringify(data, null, 2)).html() + '</pre>';
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        var k = 1024;
        var sizes = ['B', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
</script>

<div class="content-box">
    <div class="content-box-header">
        <h3>{{ lang._('Reticulum Diagnostics') }}
            <div class="pull-right">
                <label class="checkbox-inline" style="margin-right: 10px;">
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
                <a href="#tab-status" aria-controls="tab-status" role="tab" data-toggle="tab">
                    <i class="fa fa-dashboard"></i> {{ lang._('Status') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-interfaces" aria-controls="tab-interfaces" role="tab" data-toggle="tab">
                    <i class="fa fa-plug"></i> {{ lang._('Interfaces') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-paths" aria-controls="tab-paths" role="tab" data-toggle="tab">
                    <i class="fa fa-road"></i> {{ lang._('Paths') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-announces" aria-controls="tab-announces" role="tab" data-toggle="tab">
                    <i class="fa fa-bullhorn"></i> {{ lang._('Announces') }}
                </a>
            </li>
            <li role="presentation">
                <a href="#tab-propagation" aria-controls="tab-propagation" role="tab" data-toggle="tab">
                    <i class="fa fa-envelope"></i> {{ lang._('Propagation') }}
                </a>
            </li>
        </ul>

        <div class="tab-content" style="padding: 15px;">
            <div role="tabpanel" class="tab-pane active" id="tab-status">
                <div class="diagnostics-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>
            <div role="tabpanel" class="tab-pane" id="tab-interfaces">
                <div class="diagnostics-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>
            <div role="tabpanel" class="tab-pane" id="tab-paths">
                <div class="diagnostics-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>
            <div role="tabpanel" class="tab-pane" id="tab-announces">
                <div class="diagnostics-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>
            <div role="tabpanel" class="tab-pane" id="tab-propagation">
                <div class="diagnostics-content">
                    <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading...') }}
                </div>
            </div>
        </div>
    </div>
</div>
