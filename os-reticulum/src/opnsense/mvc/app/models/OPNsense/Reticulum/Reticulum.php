<?php

namespace OPNsense\Reticulum;

use OPNsense\Base\BaseModel;
use OPNsense\Base\Messages\Message;

class Reticulum extends BaseModel
{
    /**
     * Custom validation: cross-field constraints
     * Called automatically by the framework during save
     */
    public function performValidation($validateFullModel = false)
    {
        $messages = parent::performValidation($validateFullModel);

        // shared_instance_port != instance_control_port
        $sip = (string)$this->general->shared_instance_port;
        $icp = (string)$this->general->instance_control_port;
        if (!empty($sip) && !empty($icp) && $sip === $icp) {
            $messages->appendMessage(new Message(
                "Shared instance port and instance control port must be different",
                "general.instance_control_port"
            ));
        }

        // Stamp cost floor: target - flexibility >= 13
        // lxmd subtracts flexibility from target to find the minimum accepted cost.
        // The absolute minimum cost is 13, so (target - flexibility) must be >= 13.
        $target = (int)(string)$this->lxmf->stamp_cost_target;
        $flex = (int)(string)$this->lxmf->stamp_cost_flexibility;
        if ($target - $flex < 13) {
            $messages->appendMessage(new Message(
                "Effective stamp cost (target minus flexibility) must be at least 13",
                "lxmf.stamp_cost_flexibility"
            ));
        }

        // ── Interface type-specific required fields ──
        // The XML model shares one ArrayField for all 12 interface types, so type-specific
        // required fields cannot be declared Required=Y in the XML. Enforce them here so
        // the template never renders an empty value (e.g. "frequency = ") that would cause
        // an rnsd parse failure at startup.
        $requiredByType = [
            'TCPClientInterface'  => ['target_host'],
            'UDPInterface'        => ['forward_ip'],
            'RNodeInterface'      => ['port', 'frequency', 'bandwidth', 'txpower', 'spreadingfactor', 'codingrate'],
            'RNodeMultiInterface' => ['port'],
            'SerialInterface'     => ['port'],
            'KISSInterface'       => ['port'],
            'AX25KISSInterface'   => ['port', 'callsign'],
            'PipeInterface'       => ['command'],
        ];
        foreach ($this->interfaces->interface->iterateItems() as $uuid => $iface) {
            $ifType = (string)$iface->type;
            if (!isset($requiredByType[$ifType])) {
                continue;
            }
            foreach ($requiredByType[$ifType] as $field) {
                if (empty((string)$iface->$field)) {
                    $messages->appendMessage(new Message(
                        "Field '{$field}' is required for interface type {$ifType}",
                        "interfaces.interface.{$uuid}.{$field}"
                    ));
                }
            }
        }

        // ── Interface cross-record uniqueness checks ──
        // Duplicate names produce INI section collisions (last wins, silently dropping one).
        // Duplicate TCP listen endpoints cause bind failures at runtime.
        // Duplicate serial ports cause device contention failures.
        $namesSeen = [];
        $tcpListenSeen = [];
        $serialPortSeen = [];
        $tcpServerTypes = ['TCPServerInterface', 'BackboneInterface'];
        $serialTypes = ['RNodeInterface', 'RNodeMultiInterface', 'SerialInterface', 'KISSInterface', 'AX25KISSInterface'];

        foreach ($this->interfaces->interface->iterateItems() as $uuid => $iface) {
            $ifName = (string)$iface->name;
            $ifType = (string)$iface->type;
            $ifEnabled = (string)$iface->enabled;

            // 1. Interface name uniqueness (all interfaces, regardless of enabled state,
            //    because names become INI section headers in the config file)
            if (!empty($ifName)) {
                if (isset($namesSeen[$ifName])) {
                    $messages->appendMessage(new Message(
                        "Interface name '{$ifName}' is already used by another interface",
                        "interfaces.interface.{$uuid}.name"
                    ));
                }
                $namesSeen[$ifName] = true;
            }

            // Skip disabled interfaces for resource-contention checks
            if ($ifEnabled !== '1') {
                continue;
            }

            // 2. TCP listen IP+port uniqueness (enabled TCPServer/Backbone only)
            if (in_array($ifType, $tcpServerTypes, true)) {
                $listenIp = (string)$iface->listen_ip;
                $listenPort = (string)$iface->listen_port;
                if (!empty($listenPort)) {
                    $key = $listenIp . ':' . $listenPort;
                    if (isset($tcpListenSeen[$key])) {
                        $messages->appendMessage(new Message(
                            "Another enabled interface is already listening on {$key}",
                            "interfaces.interface.{$uuid}.listen_port"
                        ));
                    }
                    $tcpListenSeen[$key] = true;
                }
            }

            // 3. Serial port device uniqueness (enabled serial/radio types only)
            if (in_array($ifType, $serialTypes, true)) {
                $devPort = (string)$iface->port;
                if (!empty($devPort)) {
                    if (isset($serialPortSeen[$devPort])) {
                        $messages->appendMessage(new Message(
                            "Another enabled interface is already using device {$devPort}",
                            "interfaces.interface.{$uuid}.port"
                        ));
                    }
                    $serialPortSeen[$devPort] = true;
                }
            }
        }

        return $messages;
    }
}
