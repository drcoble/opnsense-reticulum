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

use OPNsense\Base\ApiMutableModelControllerBase;

class SettingsController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'Reticulum';
    protected static $internalModelClass = '\OPNsense\Reticulum\Reticulum';

    /**
     * Retrieve general and propagation settings
     * @return array
     */
    public function getAction()
    {
        $result = array();
        if ($this->request->isGet()) {
            $result['reticulum'] = $this->getModel()->general->getNodes();
        }
        return $result;
    }

    /**
     * Update general settings
     * @return array
     */
    public function setAction()
    {
        return $this->setBase('reticulum', 'general');
    }

    /**
     * Retrieve propagation settings
     * @return array
     */
    public function getPropagationAction()
    {
        $result = array();
        if ($this->request->isGet()) {
            $result['propagation'] = $this->getModel()->propagation->getNodes();
        }
        return $result;
    }

    /**
     * Update propagation settings
     * @return array
     */
    public function setPropagationAction()
    {
        return $this->setBase('propagation', 'propagation');
    }

    /**
     * Search/list interfaces for the grid
     * @return array
     */
    public function searchInterfaceAction()
    {
        return $this->searchBase(
            'interfaces',
            array('enabled', 'name', 'interfaceType', 'mode'),
            'name'
        );
    }

    /**
     * Retrieve a single interface by UUID
     * @param string $uuid
     * @return array
     */
    public function getInterfaceAction($uuid = null)
    {
        return $this->getBase('interface', 'interfaces', $uuid);
    }

    /**
     * Add a new interface
     * @return array
     */
    public function addInterfaceAction()
    {
        return $this->addBase('interface', 'interfaces');
    }

    /**
     * Update an existing interface
     * @param string $uuid
     * @return array
     */
    public function setInterfaceAction($uuid)
    {
        return $this->setBase('interface', 'interfaces', $uuid);
    }

    /**
     * Delete an interface
     * @param string $uuid
     * @return array
     */
    public function delInterfaceAction($uuid)
    {
        return $this->delBase('interfaces', $uuid);
    }

    /**
     * Toggle an interface enabled/disabled
     * @param string $uuid
     * @param string $enabled
     * @return array
     */
    public function toggleInterfaceAction($uuid, $enabled = null)
    {
        return $this->toggleBase('interfaces', $uuid, $enabled);
    }
}
