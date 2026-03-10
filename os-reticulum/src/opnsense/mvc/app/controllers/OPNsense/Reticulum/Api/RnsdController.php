<?php

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiMutableModelControllerBase;

class RnsdController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'Reticulum';
    protected static $internalModelClass = 'OPNsense\Reticulum\Reticulum';

    /**
     * GET api/reticulum/rnsd/get
     * Returns the general settings node
     */
    public function getAction()
    {
        return $this->getBase('general', 'general');
    }

    /**
     * POST api/reticulum/rnsd/set
     * Saves general settings
     */
    public function setAction()
    {
        return $this->setBase('general', 'general');
    }

    /**
     * GET api/reticulum/rnsd/searchInterfaces
     * Paginated search of interface ArrayField
     */
    public function searchInterfacesAction()
    {
        return $this->searchBase(
            'interfaces.interface',
            ['name', 'type', 'enabled', 'mode'],
            'name'
        );
    }

    /**
     * GET api/reticulum/rnsd/getInterface/{uuid}
     * Get single interface by UUID
     */
    public function getInterfaceAction($uuid = null)
    {
        return $this->getBase('interface', 'interfaces.interface', $uuid);
    }

    /**
     * POST api/reticulum/rnsd/addInterface
     * Create new interface record
     */
    public function addInterfaceAction()
    {
        return $this->addBase('interface', 'interfaces.interface');
    }

    /**
     * POST api/reticulum/rnsd/setInterface/{uuid}
     * Update existing interface
     */
    public function setInterfaceAction($uuid)
    {
        return $this->setBase('interface', 'interfaces.interface', $uuid);
    }

    /**
     * POST api/reticulum/rnsd/delInterface/{uuid}
     * Delete interface
     */
    public function delInterfaceAction($uuid)
    {
        return $this->delBase('interfaces.interface', $uuid);
    }

    /**
     * POST api/reticulum/rnsd/toggleInterface/{uuid}
     * Toggle interface enabled state
     */
    public function toggleInterfaceAction($uuid, $enabled = null)
    {
        return $this->toggleBase('interfaces.interface', $uuid, $enabled);
    }
}
