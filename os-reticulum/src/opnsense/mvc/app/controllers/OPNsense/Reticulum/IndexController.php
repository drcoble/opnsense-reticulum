<?php

namespace OPNsense\Reticulum;

class IndexController extends \OPNsense\Base\IndexController
{
    /**
     * General Settings page (rnsd core config)
     */
    public function generalAction()
    {
        $this->view->pick('OPNsense/Reticulum/general');
    }

    /**
     * Interfaces list/editor page
     */
    public function interfacesAction()
    {
        $this->view->pick('OPNsense/Reticulum/interfaces');
    }

    /**
     * LXMF / Propagation Node page
     */
    public function lxmfAction()
    {
        $this->view->pick('OPNsense/Reticulum/lxmf');
    }

    /**
     * Log Viewer page
     */
    public function logsAction()
    {
        $this->view->pick('OPNsense/Reticulum/logs');
    }
}
