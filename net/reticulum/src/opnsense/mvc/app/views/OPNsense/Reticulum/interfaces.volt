{#
    OPNsense Reticulum Plugin — Interfaces CRUD Grid View
#}

<script>
    $(document).ready(function () {
        // Initialize the interface grid
        $("#grid-interfaces").UIBootgrid({
            search: '/api/reticulum/settings/searchInterface',
            get: '/api/reticulum/settings/getInterface/',
            set: '/api/reticulum/settings/setInterface/',
            add: '/api/reticulum/settings/addInterface/',
            del: '/api/reticulum/settings/delInterface/',
            toggle: '/api/reticulum/settings/toggleInterface/',
            options: {
                requestHandler: function (request) {
                    // Add default sort
                    if (request.sort === undefined) {
                        request.sort = { name: 'asc' };
                    }
                    return request;
                }
            }
        });

        // Conditional field visibility based on interface type selection
        $(document).on('change', '#interface\\.interfaceType', function () {
            updateInterfaceTypeVisibility($(this).val());
        });

        // Also update visibility when dialog opens
        $(document).on('shown.bs.modal', '#DialogInterface', function () {
            var currentType = $('#interface\\.interfaceType').val();
            updateInterfaceTypeVisibility(currentType);
        });

        // Apply configuration
        $("#applyAct").click(function () {
            ajaxCall('/api/reticulum/service/reconfigure', {}, function (data, status) {
                ajaxCall('/api/reticulum/service/status', {}, function (data, status) {
                    updateServiceStatusUI(data);
                });
                // Refresh the grid
                $("#grid-interfaces").bootgrid("reload");
            });
        });

        // Initial service status
        ajaxCall('/api/reticulum/service/status', {}, function (data, status) {
            updateServiceStatusUI(data);
        });
    });

    /**
     * Show/hide interface type-specific form fields based on selected type
     */
    function updateInterfaceTypeVisibility(selectedType) {
        // List of all interface type prefixes
        var typeGroups = [
            'AutoInterface', 'UDPInterface', 'TCPServerInterface',
            'TCPClientInterface', 'RNodeInterface', 'KISSInterface',
            'AX25KISSInterface', 'SerialInterface', 'I2PInterface'
        ];

        // Hide all type-specific field rows
        $('tr[data-for-type]').hide();

        // Show fields matching the selected type
        if (selectedType) {
            $('tr[data-for-type="' + selectedType + '"]').show();
        }

        // Also use the style attribute pattern for OPNsense form rendering
        $('[id^="row_interface\\."]').each(function () {
            var row = $(this);
            var fieldId = row.attr('id').replace('row_', '');

            // Determine which type group this field belongs to
            var fieldName = fieldId.replace('interface.', '');
            var belongsToType = null;

            if (fieldName.startsWith('auto_')) belongsToType = 'AutoInterface';
            else if (fieldName.startsWith('udp_')) belongsToType = 'UDPInterface';
            else if (fieldName.startsWith('tcp_server_')) belongsToType = 'TCPServerInterface';
            else if (fieldName.startsWith('tcp_client_')) belongsToType = 'TCPClientInterface';
            else if (fieldName.startsWith('rnode_')) belongsToType = 'RNodeInterface';
            else if (fieldName.startsWith('kiss_')) belongsToType = 'KISSInterface';
            else if (fieldName.startsWith('ax25_')) belongsToType = 'AX25KISSInterface';
            else if (fieldName.startsWith('serial_')) belongsToType = 'SerialInterface';
            else if (fieldName.startsWith('i2p_')) belongsToType = 'I2PInterface';

            if (belongsToType !== null) {
                if (belongsToType === selectedType) {
                    row.show();
                } else {
                    row.hide();
                }
            }
        });
    }

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
        <h3>{{ lang._('Reticulum Interfaces') }}
            <span id="service_status_container" class="pull-right"></span>
        </h3>
    </div>
    <div class="content-box-main">
        <table id="grid-interfaces" class="table table-condensed table-hover table-striped"
               data-editDialog="DialogInterface"
               data-editAlert="InterfaceChangeMessage">
            <thead>
                <tr>
                    <th data-column-id="uuid" data-type="string" data-identifier="true" data-visible="false">{{ lang._('ID') }}</th>
                    <th data-column-id="enabled" data-width="6em" data-type="string" data-formatter="rowtoggle">{{ lang._('Enabled') }}</th>
                    <th data-column-id="name" data-type="string">{{ lang._('Name') }}</th>
                    <th data-column-id="interfaceType" data-type="string">{{ lang._('Type') }}</th>
                    <th data-column-id="mode" data-type="string">{{ lang._('Mode') }}</th>
                    <th data-column-id="commands" data-width="7em" data-formatter="commands" data-sortable="false">{{ lang._('Commands') }}</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
            <tfoot>
                <tr>
                    <td></td>
                    <td>
                        <button data-action="add" type="button" class="btn btn-xs btn-primary">
                            <span class="fa fa-fw fa-plus"></span>
                        </button>
                        <button data-action="deleteSelected" type="button" class="btn btn-xs btn-default">
                            <span class="fa fa-fw fa-trash-o"></span>
                        </button>
                    </td>
                </tr>
            </tfoot>
        </table>
    </div>
    <div class="content-box-footer">
        <div id="InterfaceChangeMessage" class="alert alert-info" style="display: none" role="alert">
            {{ lang._('After changing settings, please press Apply to reconfigure the service.') }}
        </div>
        <button class="btn btn-primary" id="applyAct" type="button">
            <b>{{ lang._('Apply') }}</b> <i id="applyAct_progress" class=""></i>
        </button>
    </div>
</div>

{{ partial("layout_partials/base_dialog", ['fields': interfaceForm, 'id': 'DialogInterface', 'label': lang._('Edit Reticulum Interface')]) }}
