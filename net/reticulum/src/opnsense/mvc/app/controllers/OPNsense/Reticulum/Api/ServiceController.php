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

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiMutableServiceControllerBase;
use OPNsense\Core\Backend;

class ServiceController extends ApiMutableServiceControllerBase
{
    protected static $internalServiceClass = '\OPNsense\Reticulum\Reticulum';
    protected static $internalServiceTemplate = 'OPNsense/Reticulum';
    protected static $internalServiceEnabled = 'general.enabled';
    protected static $internalServiceName = 'reticulum';

    /**
     * Return service status by querying configd directly.
     * The base class uses plugins_services() which requires the service to be
     * registered with a status configd action — instead we call status.py directly.
     * @return array
     */
    public function statusAction()
    {
        $mdl = $this->getModel();
        $enabled = (string)$mdl->getNodeByReference('general.enabled') === '1';
        if (!$enabled) {
            return ['status' => 'disabled', 'rnsd' => false, 'lxmd' => false];
        }
        $backend = new Backend();
        $response = trim($backend->configdRun('reticulum status'));
        $data = json_decode($response, true);
        if (is_array($data) && isset($data['status'])) {
            return $data;
        }
        return ['status' => 'unknown'];
    }

    /**
     * Reconfigure: reload templates then start or stop services based on enabled flag.
     * Overrides the base class which relies on plugins_configure() — the reticulum
     * configure hook uses a legacy direct-action format that the plugin runner skips.
     * @return array
     */
    public function reconfigureAction()
    {
        $result = ['status' => 'ok'];
        if ($this->request->isPost()) {
            $backend = new Backend();
            $backend->configdRun('template reload OPNsense/Reticulum');
            $mdl = $this->getModel();
            $enabled = (string)$mdl->getNodeByReference('general.enabled') === '1';
            if ($enabled) {
                $backend->configdRun('reticulum restart');
            } else {
                $backend->configdRun('reticulum stop');
            }
        }
        return $result;
    }
}
