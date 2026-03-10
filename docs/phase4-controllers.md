# Phase 4 — API Controllers

## Overview
PHP controllers handle REST API endpoints and GUI page routing. All follow OPNsense's MVC conventions: `ApiMutableModelControllerBase` for config CRUD, `ApiControllerBase` for service actions.

---

## Files

| File | Path | Purpose |
|------|------|---------|
| IndexController.php | `controllers/OPNsense/Reticulum/IndexController.php` | GUI page routing |
| RnsdController.php | `controllers/OPNsense/Reticulum/Api/RnsdController.php` | rnsd config API |
| LxmdController.php | `controllers/OPNsense/Reticulum/Api/LxmdController.php` | lxmd config API |
| ServiceController.php | `controllers/OPNsense/Reticulum/Api/ServiceController.php` | Service lifecycle API |

All paths relative to: `src/opnsense/mvc/app/`

---

## 1. IndexController.php — GUI Page Routing

```php
<?php

namespace OPNsense\Reticulum;

use OPNsense\Base\IndexController;

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
```

**Notes:**
- Each action maps to a Volt template in `views/OPNsense/Reticulum/`
- URLs: `/ui/reticulum/general`, `/ui/reticulum/interfaces`, `/ui/reticulum/lxmf`, `/ui/reticulum/logs`
- OPNsense routes `ui/<module>/<action>` to `<Module>\IndexController::<action>Action()`

---

## 2. RnsdController.php — rnsd Config CRUD API

```php
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
```

### API Endpoint Summary

| Method | URL | Action | Description |
|--------|-----|--------|-------------|
| GET | `api/reticulum/rnsd/get` | `getAction` | Get general settings |
| POST | `api/reticulum/rnsd/set` | `setAction` | Save general settings |
| GET | `api/reticulum/rnsd/searchInterfaces` | `searchInterfacesAction` | List interfaces (paginated) |
| GET | `api/reticulum/rnsd/getInterface/{uuid}` | `getInterfaceAction` | Get single interface |
| POST | `api/reticulum/rnsd/addInterface` | `addInterfaceAction` | Create interface |
| POST | `api/reticulum/rnsd/setInterface/{uuid}` | `setInterfaceAction` | Update interface |
| POST | `api/reticulum/rnsd/delInterface/{uuid}` | `delInterfaceAction` | Delete interface |
| POST | `api/reticulum/rnsd/toggleInterface/{uuid}` | `toggleInterfaceAction` | Toggle enabled |

### Base Method Reference

| Base Method | What It Does |
|-------------|-------------|
| `getBase($formKey, $modelPath)` | Serializes model node to JSON; masks UpdateOnlyTextField |
| `setBase($formKey, $modelPath)` | Deserializes POST JSON into model, validates, saves to config.xml |
| `searchBase($modelPath, $fields, $defaultSort)` | Returns paginated grid data from ArrayField |
| `getBase($formKey, $modelPath, $uuid)` | Gets single ArrayField record by UUID |
| `addBase($formKey, $modelPath)` | Creates new ArrayField record, validates, saves |
| `setBase($formKey, $modelPath, $uuid)` | Updates ArrayField record by UUID |
| `delBase($modelPath, $uuid)` | Deletes ArrayField record by UUID |
| `toggleBase($modelPath, $uuid)` | Flips boolean `enabled` field on ArrayField record |

---

## 3. LxmdController.php — lxmd Config API

```php
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
```

### API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `api/reticulum/lxmd/get` | Get LXMF settings |
| POST | `api/reticulum/lxmd/set` | Save LXMF settings |

---

## 4. ServiceController.php — Service Lifecycle API

```php
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
     */
    public function rnsdStatusAction()
    {
        $backend = new Backend();
        $response = trim($backend->configdRun('reticulum status.rnsd'));
        return json_decode($response, true) ?: ['status' => 'unknown'];
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
            $rnsdStatus = json_decode(
                trim($backend->configdRun('reticulum status.rnsd')),
                true
            );
            if (!isset($rnsdStatus['status']) || $rnsdStatus['status'] !== 'running') {
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
            $rnsdStatus = json_decode(
                trim($backend->configdRun('reticulum status.rnsd')),
                true
            );
            if (!isset($rnsdStatus['status']) || $rnsdStatus['status'] !== 'running') {
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
     */
    public function lxmdStatusAction()
    {
        $backend = new Backend();
        $response = trim($backend->configdRun('reticulum status.lxmd'));
        return json_decode($response, true) ?: ['status' => 'unknown'];
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
```

### API Endpoint Summary

| Method | URL | Description |
|--------|-----|-------------|
| POST | `api/reticulum/service/rnsdStart` | Start rnsd |
| POST | `api/reticulum/service/rnsdStop` | Stop rnsd |
| POST | `api/reticulum/service/rnsdRestart` | Restart rnsd |
| GET | `api/reticulum/service/rnsdStatus` | rnsd running state |
| POST | `api/reticulum/service/lxmdStart` | Start lxmd (checks rnsd first) |
| POST | `api/reticulum/service/lxmdStop` | Stop lxmd |
| POST | `api/reticulum/service/lxmdRestart` | Restart lxmd |
| GET | `api/reticulum/service/lxmdStatus` | lxmd running state |
| POST | `api/reticulum/service/reconfigure` | Regenerate configs + restart |
| GET | `api/reticulum/service/rnstatus` | rnstatus JSON |
| GET | `api/reticulum/service/info` | Version + identity info (raw) |
| GET | `api/reticulum/service/rnsdInfo` | rnsd version, identity, uptime for GUI |
| GET | `api/reticulum/service/lxmdInfo` | lxmd version for GUI |
| GET | `api/reticulum/service/rnsdLogs` | Last N lines of rnsd log |
| GET | `api/reticulum/service/lxmdLogs` | Last N lines of lxmd log |

---

## 5. Key Design Patterns

### configd Backend Calls
All service operations go through configd via `Backend::configdRun()`. This is mandatory — PHP controllers must never execute shell commands directly.

```php
$backend = new Backend();
$result = $backend->configdRun('reticulum start.rnsd');
```

The string `'reticulum start.rnsd'` maps to the `[start.rnsd]` section in `actions_reticulum.conf`.

### CSRF Protection
OPNsense's `ApiControllerBase` provides automatic CSRF token validation on all POST requests. No additional code needed.

### Authentication & ACL
Access is controlled by `ACL.xml` patterns (Phase 1). The framework checks the logged-in user's privileges against the URL pattern before the controller action executes.

### Error Handling Pattern
```php
// Service action error handling
$result = trim($backend->configdRun('reticulum start.rnsd'));
if (strpos($result, 'error') !== false || empty($result)) {
    return ['result' => 'error', 'message' => $result];
}
return ['result' => 'ok'];
```

### lxmd Dependency Enforcement
The `lxmdStartAction()` checks rnsd status server-side before starting lxmd. This is critical — the GUI may also disable the start button client-side, but the server-side check is the authoritative gate.

---

## 6. Implementation Checklist

- [ ] Create IndexController.php with 4 page actions
- [ ] Create RnsdController.php with get/set + interface CRUD (8 endpoints)
- [ ] Create LxmdController.php with get/set (2 endpoints)
- [ ] Create ServiceController.php with all service actions (15 endpoints)
- [ ] Test: GET api/reticulum/rnsd/get returns model defaults
- [ ] Test: POST api/reticulum/rnsd/set saves and validates
- [ ] Test: Interface CRUD cycle (add, get, search, set, toggle, delete)
- [ ] Test: searchInterfaces URL segment resolves correctly (method is searchInterfacesAction)
- [ ] Test: lxmdStart blocked when rnsd not running
- [ ] Test: lxmdRestart blocked when rnsd not running
- [ ] Test: reconfigure regenerates config files
- [ ] Test: rnstatus returns JSON when rnsd is running
- [ ] Test: rnsdInfo returns version, identity, uptime
- [ ] Test: rnsdLogs/lxmdLogs return log lines array; lines param clamped to 10–500
- [ ] Test: ACL read-only user cannot POST to mutating endpoints
- [ ] Test: ACL read-only user CAN GET rnsdInfo, lxmdInfo, rnsdLogs, lxmdLogs
- [ ] Validate: no two interfaces share the same name (implemented in model performValidation)
- [ ] Validate: no two TCP interfaces share the same listen_port on the same listen_ip (implemented in model performValidation)
- [ ] Validate: no two serial interfaces share the same /dev/ port path (implemented in model performValidation)
- [ ] Add all controller files to pkg-plist
