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
 * Register Reticulum services with the OPNsense service manager.
 * RNSD and LXMD are registered as independent services so they appear
 * separately on the Services dashboard and can be individually controlled.
 * @return array
 */
function reticulum_services()
{
    $services = array();
    $mdl = new Reticulum();

    if ((string)$mdl->general->enabled === '1') {
        $services[] = array(
            'name' => 'reticulum',
            'description' => 'Reticulum Network Daemon (rnsd)',
            'configd' => array(
                'start' => array('reticulum start_rnsd'),
                'stop' => array('reticulum stop_rnsd'),
                'restart' => array('reticulum restart_rnsd'),
            ),
            'nocheck' => false,
            'pidfile' => '/var/run/rnsd.pid'
        );
    }

    if ((string)$mdl->general->enable_lxmf === '1') {
        $services[] = array(
            'name' => 'lxmf',
            'description' => 'LXMF Messaging Daemon (lxmd)',
            'configd' => array(
                'start' => array('reticulum start_lxmd'),
                'stop' => array('reticulum stop_lxmd'),
                'restart' => array('reticulum restart_lxmd'),
            ),
            'nocheck' => false,
            'pidfile' => '/var/run/lxmd.pid'
        );
    }

    return $services;
}

/**
 * Hook called when configuration changes — regenerate configs and restart services
 * @param bool $verbose
 */
function reticulum_configure($verbose = false)
{
    if ($verbose) {
        echo "Configuring Reticulum...\n";
    }

    $mdl = new Reticulum();
    $rnsdEnabled = (string)$mdl->general->enabled === '1';
    $lxmdEnabled = (string)$mdl->general->enable_lxmf === '1';

    // Always regenerate configuration files from templates
    if ($rnsdEnabled || $lxmdEnabled) {
        configd_run('template reload OPNsense/Reticulum');
    }

    if ($rnsdEnabled) {
        configd_run('reticulum restart_rnsd');
    } else {
        configd_run('reticulum stop_rnsd');
    }

    if ($lxmdEnabled) {
        configd_run('reticulum restart_lxmd');
    } else {
        configd_run('reticulum stop_lxmd');
    }
}

/**
 * Generate firewall rules for Reticulum interfaces.
 * Dynamically creates inbound allow rules for configured listener ports.
 * @param object $fw firmware rules object
 */
function reticulum_firewall($fw)
{
    $mdl = new Reticulum();

    if ((string)$mdl->general->enabled !== '1') {
        return;
    }

    $interfaces = $mdl->interfaces->iterateItems();
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
                            'to' => '(self)',
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
                            'to' => '(self)',
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
                            'to' => '(self)',
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
                            'to' => '(self)',
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
 * Register syslog facilities for Reticulum
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
    $result['services'] = array('reticulum', 'lxmf');
    return array($result);
}
