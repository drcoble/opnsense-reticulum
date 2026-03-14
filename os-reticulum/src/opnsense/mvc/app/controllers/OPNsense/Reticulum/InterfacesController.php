<?php

namespace OPNsense\Reticulum;

class InterfacesController extends \OPNsense\Base\IndexController
{
    /**
     * Interfaces list/editor page
     */
    public function indexAction()
    {
        $this->view->pick('OPNsense/Reticulum/interfaces');
    }
}
