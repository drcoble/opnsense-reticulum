{#
    OPNsense Reticulum Plugin — Log Viewer
    Copyright (C) 2024 OPNsense Community
    SPDX-License-Identifier: BSD-2-Clause
#}

{% extends 'layouts/default.volt' %}

{% block content %}

<ul class="nav nav-tabs" id="log-tabs" style="margin-bottom:0;">
    <li class="active log-tab" data-service="rnsd">
        <a href="#" class="log-tab-link">{{ lang._('Transport Node (rnsd)') }}</a>
    </li>
    <li class="log-tab" data-service="lxmd">
        <a href="#" class="log-tab-link">{{ lang._('Propagation Node (lxmd)') }}</a>
    </li>
</ul>

<div class="content-box" style="padding:12px 16px;">
    <div class="row">
        <div class="col-sm-2">
            <label>{{ lang._('Severity') }}</label>
            <select id="log-level" class="form-control input-sm">
                <option value="">{{ lang._('All') }}</option>
                <option value="0">{{ lang._('Critical') }}</option>
                <option value="1">{{ lang._('Error') }}</option>
                <option value="2">{{ lang._('Warning') }}</option>
                <option value="3">{{ lang._('Notice') }}</option>
                <option value="4">{{ lang._('Info') }}</option>
                <option value="5">{{ lang._('Debug') }}</option>
                <option value="6">{{ lang._('Extreme') }}</option>
                <option value="7">{{ lang._('Trace') }}</option>
            </select>
        </div>
        <div class="col-sm-4">
            <label>{{ lang._('Search') }}</label>
            <input type="text" id="log-search" class="form-control input-sm"
                   placeholder="{{ lang._('Filter log lines...') }}" />
        </div>
        <div class="col-sm-2">
            <label>{{ lang._('Lines to Fetch') }}</label>
            <select id="log-lines" class="form-control input-sm">
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200" selected="selected">200</option>
                <option value="500">500</option>
            </select>
        </div>
        <div class="col-sm-4" style="padding-top:24px;">
            <button class="btn btn-default btn-sm" id="refresh-logs">
                <i class="fa fa-refresh"></i> {{ lang._('Refresh') }}
            </button>
            <button class="btn btn-default btn-sm" id="download-logs" style="margin-left:6px;">
                <i class="fa fa-download"></i> {{ lang._('Download') }}
            </button>
            <div style="margin-top:6px;">
                <label class="checkbox-inline" style="font-weight:normal;">
                    <input type="checkbox" id="auto-refresh" />
                    {{ lang._('Auto-refresh every 5 s') }}
                </label>
            </div>
        </div>
    </div>
</div>

<div class="content-box" style="padding:0; margin-top:4px;">
    <div id="log-loading" class="text-center text-muted" style="display:none; padding:24px;">
        <i class="fa fa-spinner fa-spin"></i> {{ lang._('Loading log data...') }}
    </div>
    <div id="log-empty-service" class="text-center text-muted" style="display:none; padding:24px;">
        <em>{{ lang._('No log entries found. The service may not have started yet, or the log file does not exist at the configured path.') }}</em>
    </div>
    <div id="log-empty-filter" class="text-center text-muted" style="display:none; padding:24px;">
        <em>{{ lang._('No log lines match the current severity and search filters. Try widening the filter or selecting a higher severity level.') }}</em>
    </div>
    <pre id="log-output" style="
        margin:0;
        padding:12px 16px;
        background:#1e1e1e;
        color:#d4d4d4;
        font-size:12px;
        max-height:600px;
        overflow-y:auto;
        border:none;
        border-radius:0;
        white-space:pre-wrap;
        word-break:break-all;
    "></pre>
</div>

<script>
$(document).ready(function() {
    var currentService = 'rnsd';
    var refreshInterval = null;
    var lastRawLogs = [];

    /**
     * Filter log lines by severity level. Reticulum embeds numeric levels
     * in brackets: [0]=Critical through [7]=Trace. Keep lines where the
     * level number <= the selected max level. Lines without a level tag
     * (e.g. continuation lines, stack traces) are always kept.
     */
    function filterByLevel(lines, levelStr) {
        if (!levelStr && levelStr !== '0') return lines;
        var maxLevel = parseInt(levelStr, 10);
        return lines.filter(function(line) {
            var m = line.match(/\[(\d+)\]/);
            if (!m) return true;
            return parseInt(m[1], 10) <= maxLevel;
        });
    }

    /**
     * Filter log lines by case-insensitive keyword substring match.
     */
    function filterByKeyword(lines, keyword) {
        if (!keyword) return lines;
        var kw = keyword.toLowerCase();
        return lines.filter(function(line) {
            return line.toLowerCase().indexOf(kw) !== -1;
        });
    }

    /**
     * Render filtered log lines into the output area. Handles two distinct
     * empty states: no raw logs at all (service not started / empty file)
     * vs. filters excluding all lines.
     */
    function renderLogs(lines) {
        $('#log-loading').hide();
        $('#log-empty-service').hide();
        $('#log-empty-filter').hide();
        $('#log-output').hide();

        if (lastRawLogs.length === 0) {
            $('#log-empty-service').show();
            return;
        }

        if (lines.length === 0) {
            $('#log-empty-filter').show();
            return;
        }

        $('#log-output').text(lines.join('\n')).show();
        var el = document.getElementById('log-output');
        if (el) el.scrollTop = el.scrollHeight;
    }

    /**
     * Apply severity and keyword filters to the cached raw log lines
     * and re-render. Called on filter input changes without re-fetching.
     */
    function applyFilters() {
        var filtered = filterByLevel(lastRawLogs, $('#log-level').val());
        filtered = filterByKeyword(filtered, $('#log-search').val());
        renderLogs(filtered);
    }

    /**
     * Fetch log lines from the API for the currently selected service,
     * cache them, and apply filters for display.
     */
    function loadLogs() {
        var lines = parseInt($('#log-lines').val(), 10) || 200;
        $('#log-output').hide();
        $('#log-empty-service').hide();
        $('#log-empty-filter').hide();
        $('#log-loading').show();

        ajaxCall('/api/reticulum/service/' + currentService + 'Logs', {lines: lines}, function(data) {
            if (data && data.logs) {
                lastRawLogs = data.logs.filter(function(l) { return l.trim() !== ''; });
            } else {
                lastRawLogs = [];
            }
            applyFilters();
        });
    }

    // Tab switching — custom tab navigation (not Bootstrap data-toggle)
    $('#log-tabs').on('click', '.log-tab-link', function(e) {
        e.preventDefault();
        var $tab = $(this).closest('.log-tab');
        $('.log-tab').removeClass('active');
        $tab.addClass('active');
        currentService = $tab.data('service');
        lastRawLogs = [];
        loadLogs();
    });

    // Filter controls — re-filter cached data without re-fetching
    $('#log-level, #log-search').on('input change', applyFilters);

    // Max lines change triggers a new fetch from the API
    $('#log-lines').on('change', loadLogs);

    // Manual refresh button
    $('#refresh-logs').click(loadLogs);

    // Auto-refresh toggle
    $('#auto-refresh').change(function() {
        if ($(this).is(':checked')) {
            refreshInterval = setInterval(loadLogs, 5000);
        } else {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }
    });

    // Download button — construct a Blob from the currently displayed (filtered) log lines
    $('#download-logs').click(function() {
        var filtered = filterByLevel(lastRawLogs, $('#log-level').val());
        filtered = filterByKeyword(filtered, $('#log-search').val());
        var content = filtered.join('\n');
        if (!content) {
            var $btn = $('#download-logs');
            var $msg = $('<span class="text-muted small" style="margin-left:8px;">{{ lang._("Nothing to download.") }}</span>');
            $btn.after($msg);
            setTimeout(function() { $msg.remove(); }, 3000);
            return;
        }
        var blob = new Blob([content], {type: 'text/plain'});
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'reticulum-' + currentService + '.log';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Initial load for the default tab (rnsd)
    loadLogs();
});
</script>

{% endblock %}
