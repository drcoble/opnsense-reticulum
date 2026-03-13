<?php

namespace OPNsense\Reticulum;

class LogsController extends \OPNsense\Base\IndexController
{
    /**
     * Log Viewer page
     */
    public function indexAction()
    {
        $this->view->pick('OPNsense/Reticulum/logs');
    }
}
