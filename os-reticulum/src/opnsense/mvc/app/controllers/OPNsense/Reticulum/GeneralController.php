<?php

namespace OPNsense\Reticulum;

class GeneralController extends \OPNsense\Base\IndexController
{
    /**
     * General Settings page (rnsd core config)
     */
    public function indexAction()
    {
        $this->view->pick('OPNsense/Reticulum/general');
    }
}
