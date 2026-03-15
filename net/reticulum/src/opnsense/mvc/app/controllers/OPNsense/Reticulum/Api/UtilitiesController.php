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

use OPNsense\Base\ApiControllerBase;
use OPNsense\Core\Backend;

class UtilitiesController extends ApiControllerBase
{
    /**
     * Run rnstatus — optionally detailed (-a)
     * POST param: detail (0|1)
     * @return array
     */
    public function rnstatusAction()
    {
        $detail = (int)$this->request->getPost('detail', 'int', 0);
        $arg = ($detail ? 'rnstatus_detail' : 'rnstatus');
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities ' . $arg);
        return $this->parseResponse($response);
    }

    /**
     * Run rnid — show local identity or look up a destination hash
     * POST param: hash (optional 32-char hex)
     * @return array
     */
    public function rnidAction()
    {
        $hash = (string)$this->request->getPost('hash', 'string', '');
        $safeHash = preg_replace('/[^a-fA-F0-9]/', '', $hash);
        $arg = 'rnid' . ($safeHash !== '' ? ' ' . $safeHash : '');
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities ' . $arg);
        return $this->parseResponse($response);
    }

    /**
     * Run rnpath — show path to a destination hash
     * POST param: hash (required, 32-char hex)
     * @return array
     */
    public function rnpathAction()
    {
        $hash = (string)$this->request->getPost('hash', 'string', '');
        if (empty($hash)) {
            return ['status' => 'error', 'message' => 'Destination hash is required'];
        }
        $safeHash = preg_replace('/[^a-fA-F0-9]/', '', $hash);
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities rnpath ' . $safeHash);
        return $this->parseResponse($response);
    }

    /**
     * Run rnprobe — probe a destination hash
     * POST params: hash (required), timeout (1-60, optional)
     * @return array
     */
    public function rnprobeAction()
    {
        $hash = (string)$this->request->getPost('hash', 'string', '');
        if (empty($hash)) {
            return ['status' => 'error', 'message' => 'Destination hash is required'];
        }
        $safeHash = preg_replace('/[^a-fA-F0-9]/', '', $hash);
        $timeout = max(1, min(60, (int)$this->request->getPost('timeout', 'int', 10)));
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities rnprobe ' . $safeHash . ' ' . $timeout);
        return $this->parseResponse($response);
    }

    /**
     * Run rnodeconf — list or inspect RNode devices
     * POST param: device (optional, /dev/... path)
     * @return array
     */
    public function rnodeconfigAction()
    {
        $device = (string)$this->request->getPost('device', 'string', '');
        $safeDevice = preg_replace('/[^a-zA-Z0-9\/_\-.]/', '', $device);
        $arg = 'rnodeconf' . ($safeDevice !== '' ? ' ' . $safeDevice : '');
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities ' . $arg);
        return $this->parseResponse($response);
    }

    /**
     * Run rncp — display remote file copy usage/help (no user params needed)
     * @return array
     */
    public function rncpAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities rncp_help');
        return $this->parseResponse($response);
    }

    /**
     * Run rnx — display remote execution usage/help (no user params needed)
     * @return array
     */
    public function rnxAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum utilities rnx_help');
        return $this->parseResponse($response);
    }

    /**
     * Parse backend response to structured array
     * @param string $response
     * @return array
     */
    private function parseResponse($response)
    {
        $data = json_decode(trim($response), true);
        if (json_last_error() === JSON_ERROR_NONE) {
            return ['status' => 'ok', 'data' => $data];
        }
        return ['status' => 'ok', 'data' => ['output' => $response]];
    }
}
