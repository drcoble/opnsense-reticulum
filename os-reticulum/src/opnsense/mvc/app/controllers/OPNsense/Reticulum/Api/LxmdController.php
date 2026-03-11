<?php

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiMutableModelControllerBase;

class LxmdController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'Reticulum';
    protected static $internalModelClass = 'OPNsense\Reticulum\Reticulum';

    /**
     * GET api/reticulum/lxmd/get
     * Returns the lxmf settings node
     */
    public function getAction()
    {
        return $this->getBase('lxmf', 'lxmf');
    }

    /**
     * POST api/reticulum/lxmd/set
     * Saves lxmf settings
     */
    public function setAction()
    {
        return $this->setBase('lxmf', 'lxmf');
    }
}
