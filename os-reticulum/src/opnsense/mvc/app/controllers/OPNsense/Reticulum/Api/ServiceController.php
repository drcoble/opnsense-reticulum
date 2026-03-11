<?php

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\Core\Backend;

class ServiceController extends ApiControllerBase
{
    // ==================== rnsd ====================

    /**
     * POST api/reticulum/service/rnsdStart
     */
    public function rnsdStartAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $result = trim($backend->configdRun('reticulum start.rnsd'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * POST api/reticulum/service/rnsdStop
     */
    public function rnsdStopAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $result = trim($backend->configdRun('reticulum stop.rnsd'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * POST api/reticulum/service/rnsdRestart
     */
    public function rnsdRestartAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $result = trim($backend->configdRun('reticulum restart.rnsd'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * GET api/reticulum/service/rnsdStatus
     * Uses pgrep -F (pidfile) because rnsd runs as a Python process and
     * its ps name is the interpreter, not "rnsd".
     */
    public function rnsdStatusAction()
    {
        exec('pgrep -F /var/run/rnsd.pid 2>/dev/null', $pids, $code);
        return ['status' => $code === 0 ? 'running' : 'stopped'];
    }

    // ==================== lxmd ====================

    /**
     * POST api/reticulum/service/lxmdStart
     * Enforces rnsd dependency: checks rnsd is running before starting lxmd
     */
    public function lxmdStartAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();

            // Check rnsd is running first
            exec('pgrep -F /var/run/rnsd.pid 2>/dev/null', $pids, $code);
            if ($code !== 0) {
                return [
                    'result' => 'error',
                    'message' => 'Cannot start lxmd: rnsd is not running. Start rnsd first.'
                ];
            }

            $result = trim($backend->configdRun('reticulum start.lxmd'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * POST api/reticulum/service/lxmdStop
     */
    public function lxmdStopAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $result = trim($backend->configdRun('reticulum stop.lxmd'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * POST api/reticulum/service/lxmdRestart
     * Enforces rnsd dependency: checks rnsd is running before restarting lxmd
     */
    public function lxmdRestartAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();

            // Check rnsd is running first
            exec('pgrep -F /var/run/rnsd.pid 2>/dev/null', $pids, $code);
            if ($code !== 0) {
                return [
                    'result' => 'error',
                    'message' => 'Cannot restart lxmd: rnsd is not running. Start rnsd first.'
                ];
            }

            $result = trim($backend->configdRun('reticulum restart.lxmd'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * GET api/reticulum/service/lxmdStatus
     * Uses pgrep -F (pidfile) because lxmd runs as a Python process and
     * its ps name is the interpreter, not "lxmd".
     */
    public function lxmdStatusAction()
    {
        exec('pgrep -F /var/run/lxmd.pid 2>/dev/null', $pids, $code);
        return ['status' => $code === 0 ? 'running' : 'stopped'];
    }

    // ==================== Shared ====================

    /**
     * POST api/reticulum/service/reconfigure
     * Regenerate config files + conditional restart
     */
    public function reconfigureAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $result = trim($backend->configdRun('reticulum reconfigure'));
            return ['result' => $result];
        }
        return ['result' => 'error', 'message' => 'POST required'];
    }

    /**
     * GET api/reticulum/service/rnstatus
     * Proxy rnstatus --json output
     */
    public function rnstatusAction()
    {
        $backend = new Backend();
        $response = trim($backend->configdRun('reticulum rnstatus'));
        $data = json_decode($response, true);
        return $data ?: ['error' => 'Could not parse rnstatus output'];
    }

    /**
     * GET api/reticulum/service/info
     * Returns version info and node identity
     */
    public function infoAction()
    {
        $backend = new Backend();
        $response = trim($backend->configdRun('reticulum info'));
        $data = json_decode($response, true);
        return $data ?: [
            'rns_version' => 'unknown',
            'lxmf_version' => 'unknown',
            'node_identity' => ''
        ];
    }

    /**
     * GET api/reticulum/service/rnsdInfo
     * Returns rnsd version, node identity, and uptime for the GUI runtime info row
     */
    public function rnsdInfoAction()
    {
        $backend = new Backend();

        // Get version + identity from info script
        $infoRaw = trim($backend->configdRun('reticulum info'));
        $info = json_decode($infoRaw, true) ?: [];

        // Get uptime from rnstatus (only available when running)
        $uptime = '';
        $rnstatusRaw = trim($backend->configdRun('reticulum rnstatus'));
        $rnstatus = json_decode($rnstatusRaw, true);
        if (isset($rnstatus['uptime'])) {
            $uptime = $rnstatus['uptime'];
        }

        return [
            'version'  => $info['rns_version'] ?? 'unknown',
            'identity' => $info['node_identity'] ?? '',
            'uptime'   => $uptime,
        ];
    }

    /**
     * GET api/reticulum/service/lxmdInfo
     * Returns lxmd version and identity for the GUI runtime info row
     */
    public function lxmdInfoAction()
    {
        $backend = new Backend();
        $infoRaw = trim($backend->configdRun('reticulum info'));
        $info = json_decode($infoRaw, true) ?: [];

        return [
            'version'  => $info['lxmf_version'] ?? 'unknown',
            'identity' => '',
        ];
    }

    /**
     * GET api/reticulum/service/rnsdLogs
     * Returns the last N lines of the rnsd log
     */
    public function rnsdLogsAction()
    {
        $lines = $this->request->get('lines', 'int', 200);
        $lines = min(max($lines, 10), 500);
        $backend = new Backend();
        $result = trim($backend->configdRun('reticulum logs.rnsd', [$lines]));
        return ['logs' => explode("\n", $result)];
    }

    /**
     * GET api/reticulum/service/lxmdLogs
     * Returns the last N lines of the lxmd log
     */
    public function lxmdLogsAction()
    {
        $lines = $this->request->get('lines', 'int', 200);
        $lines = min(max($lines, 10), 500);
        $backend = new Backend();
        $result = trim($backend->configdRun('reticulum logs.lxmd', [$lines]));
        return ['logs' => explode("\n", $result)];
    }
}
