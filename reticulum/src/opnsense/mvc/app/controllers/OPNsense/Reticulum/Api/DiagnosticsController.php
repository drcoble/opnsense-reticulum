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

class DiagnosticsController extends ApiControllerBase
{
    /**
     * Retrieve Reticulum network status
     * @return array
     */
    public function rnstatusAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum diagnostics rnstatus');
        return $this->parseJsonResponse($response);
    }

    /**
     * Retrieve path table
     * @return array
     */
    public function pathsAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum diagnostics paths');
        return $this->parseJsonResponse($response);
    }

    /**
     * Retrieve recent announcements
     * @return array
     */
    public function announcesAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum diagnostics announces');
        return $this->parseJsonResponse($response);
    }

    /**
     * Retrieve propagation node status
     * @return array
     */
    public function propagationAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum diagnostics propagation');
        return $this->parseJsonResponse($response);
    }

    /**
     * Retrieve active interface statistics
     * @return array
     */
    public function interfacesAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum diagnostics interfaces');
        return $this->parseJsonResponse($response);
    }

    /**
     * Retrieve recent rnsd log output
     * @return array
     */
    public function logAction()
    {
        $backend = new Backend();
        $response = $backend->configdRun('reticulum diagnostics log');
        return $this->parseJsonResponse($response);
    }

    /**
     * Parse JSON response from backend, falling back to raw text
     * @param string $response
     * @return array
     */
    private function parseJsonResponse($response)
    {
        $data = json_decode(trim($response), true);
        if (json_last_error() === JSON_ERROR_NONE) {
            return ['status' => 'ok', 'data' => $data];
        }
        return ['status' => 'ok', 'data' => ['raw' => $response]];
    }
}
