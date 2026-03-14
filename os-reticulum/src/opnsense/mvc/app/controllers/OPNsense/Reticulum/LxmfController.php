<?php

namespace OPNsense\Reticulum;

class LxmfController extends \OPNsense\Base\IndexController
{
    /**
     * LXMF / Propagation Node page
     */
    public function indexAction()
    {
        $this->view->pick('OPNsense/Reticulum/lxmf');
    }
}
