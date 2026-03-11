<?php

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiMutableModelControllerBase;
use OPNsense\Core\Config;

class RnsdController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'Reticulum';
    protected static $internalModelClass = 'OPNsense\Reticulum\Reticulum';

    /**
     * GET api/reticulum/rnsd/get
     * Returns the general settings node.
     *
     * Note: getBase() is designed for ArrayField items and calls Add() which
     * does not exist on flat container nodes. For flat settings sections we
     * must access the model node directly via getNodes().
     */
    public function getAction()
    {
        return ['general' => $this->getModel()->general->getNodes()];
    }

    /**
     * POST api/reticulum/rnsd/set
     * Saves general settings.
     *
     * Note: setBase() requires a UUID (ArrayField pattern) and will either
     * throw a TypeError or skip the update when called without one. For flat
     * settings sections we apply the post data directly to the model node,
     * validate, and save — mirroring the parent setAction() pattern but
     * scoped to the 'general' subtree.
     */
    public function setAction()
    {
        $result = ['result' => 'failed'];
        if ($this->request->isPost()) {
            Config::getInstance()->lock();
            $mdl = $this->getModel();
            $mdl->general->setNodes($this->request->getPost('general'));
            $result = $this->validate();
            if (empty($result['result'])) {
                return $this->save(false, true);
            }
        }
        return $result;
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
