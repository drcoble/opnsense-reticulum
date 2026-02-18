<?php

/**
 *    Copyright (C) 2024 Decimus Technology Ltd
 *
 *    All rights reserved.
 *
 *    Redistribution and use in source and binary forms, with or without
 *    modification, are permitted provided that the following conditions are met:
 *
 *    1. Redistributions of source code must retain the above copyright notice,
 *       this list of conditions and the following disclaimer.
 *
 *    2. Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *
 *    THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
 *    INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
 *    AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *    AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 *    OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 *    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 *    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 *    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 *    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *    POSSIBILITY OF SUCH DAMAGE.
 */

use OPNsense\Reticulum\Reticulum;

/**
 * Register Reticulum services with the OPNsense service manager
 * @return array
 */
function reticulum_services()
{
    $services = array();

    $mdl = new Reticulum();
    if ((string)$mdl->general->enabled === '1') {
        $services[] = array(
            'name' => 'reticulum',
            'description' => 'Reticulum Network Daemon',
            'configd' => array(
                'start' => array('reticulum start'),
                'stop' => array('reticulum stop'),
                'restart' => array('reticulum restart'),
            ),
            'nocheck' => false,
            'pidfile' => '/var/run/rnsd.pid'
        );
    }

    return $services;
}

/**
 * Hook called when configuration changes — regenerate configs and restart
 * @param bool $verbose
 */
function reticulum_configure($verbose = false)
{
    if ($verbose) {
        echo "Configuring Reticulum...\n";
    }

    $mdl = new Reticulum();
    if ((string)$mdl->general->enabled === '1') {
        // Regenerate configuration files from templates
        configd_run('template reload OPNsense/Reticulum');
        // Restart services to pick up new configuration
        configd_run('reticulum restart');
    } else {
        // If disabled, stop services
        configd_run('reticulum stop');
    }
}

/**
 * Generate firewall rules for Reticulum interfaces
 * Dynamically creates inbound allow rules for configured listener ports
 * @param object $fw firmware rules object
 */
function reticulum_firewall($fw)
{
    $mdl = new Reticulum();

    if ((string)$mdl->general->enabled !== '1') {
        return;
    }

    // Iterate all configured interfaces and create firewall rules for listeners
    $interfaces = $mdl->interfaces->interface->iterateItems();
    foreach ($interfaces as $uuid => $iface) {
        if ((string)$iface->enabled !== '1') {
            continue;
        }

        $ifaceName = (string)$iface->name;
        $ifaceType = (string)$iface->interfaceType;

        switch ($ifaceType) {
            case 'TCPServerInterface':
                $port = (string)$iface->tcp_server_listen_port;
                if (!empty($port)) {
                    $fw->registerFilterRule(
                        500000,
                        array(
                            'protocol' => 'tcp',
                            'to_port' => $port,
                            'direction' => 'in',
                            'label' => "Reticulum TCP: {$ifaceName}",
                            '#ref' => "ui/reticulum/interfaces"
                        )
                    );
                }
                break;

            case 'UDPInterface':
                $port = (string)$iface->udp_listen_port;
                if (!empty($port)) {
                    $fw->registerFilterRule(
                        500000,
                        array(
                            'protocol' => 'udp',
                            'to_port' => $port,
                            'direction' => 'in',
                            'label' => "Reticulum UDP: {$ifaceName}",
                            '#ref' => "ui/reticulum/interfaces"
                        )
                    );
                }
                break;

            case 'AutoInterface':
                $discoveryPort = (string)$iface->auto_discovery_port;
                $dataPort = (string)$iface->auto_data_port;
                if (!empty($discoveryPort)) {
                    $fw->registerFilterRule(
                        500000,
                        array(
                            'protocol' => 'udp',
                            'to_port' => $discoveryPort,
                            'direction' => 'in',
                            'label' => "Reticulum Auto Discovery: {$ifaceName}",
                            '#ref' => "ui/reticulum/interfaces"
                        )
                    );
                }
                if (!empty($dataPort)) {
                    $fw->registerFilterRule(
                        500000,
                        array(
                            'protocol' => 'udp',
                            'to_port' => $dataPort,
                            'direction' => 'in',
                            'label' => "Reticulum Auto Data: {$ifaceName}",
                            '#ref' => "ui/reticulum/interfaces"
                        )
                    );
                }
                break;

            // Serial/RNode/KISS/AX.25/I2P interfaces don't need firewall rules
            default:
                break;
        }
    }
}

/**
 * Register syslog facility for Reticulum
 * @return array
 */
function reticulum_syslog()
{
    return array(
        'reticulum' => array(
            'facility' => array('reticulum', 'lxmd')
        )
    );
}

/**
 * HA sync support for Reticulum configuration
 * @return array
 */
function reticulum_xmlrpc_sync()
{
    $result = array();
    $result['id'] = 'reticulum';
    $result['section'] = 'OPNsense.Reticulum';
    $result['description'] = 'Reticulum Network Stack';
    $result['services'] = array('reticulum');
    return array($result);
}
