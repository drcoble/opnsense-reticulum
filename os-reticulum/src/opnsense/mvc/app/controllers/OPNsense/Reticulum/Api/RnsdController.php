<?php

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiMutableModelControllerBase;
use OPNsense\Core\Config;

class RnsdController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'Reticulum';
    protected static $internalModelClass = 'OPNsense\Reticulum\Reticulum';

    /**
     * Flatten getNodes()-style option metadata to scalar values.
     *
     * getNodes() returns rich metadata for OptionField and BooleanField
     * types, e.g. {"enabled": {"1": {"value": "Yes", "selected": 1}, ...}}.
     * If a client GETs this data and POSTs it back without unwrapping,
     * setNodes()/setValue() receives arrays where it expects scalar strings.
     *
     * This method walks the POST data and converts any array values back to
     * the selected key string. Normal scalar values pass through unchanged.
     *
     * @param array $data POST data, possibly containing option metadata arrays
     * @return array flattened data with only scalar string values
     */
    private function flattenOptionValues(array $data): array
    {
        $result = [];
        foreach ($data as $key => $value) {
            if (is_array($value)) {
                // Option/Boolean metadata: {"1": {"value": "Yes", "selected": 1}, ...}
                // Find the entry with "selected" == 1 and use its key.
                $selected = null;
                foreach ($value as $optKey => $optMeta) {
                    if (is_array($optMeta) && !empty($optMeta['selected'])) {
                        $selected = (string)$optKey;
                        break;
                    }
                }
                // If we found a selected option, use it; otherwise skip the
                // field entirely (don't send an array to setValue).
                if ($selected !== null) {
                    $result[$key] = $selected;
                }
            } else {
                $result[$key] = $value;
            }
        }
        return $result;
    }

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
            $mdl = $this->getModel();
            $postData = $this->request->getPost('general') ?? [];
            $mdl->general->setNodes($this->flattenOptionValues($postData));
            $msgs = $mdl->performValidation();
            foreach ($msgs as $msg) {
                if (!isset($result['validations'])) {
                    $result['validations'] = [];
                }
                $result['validations'][$msg->getField()] = $msg->getMessage();
            }
            if (empty($result['validations'])) {
                $mdl->serializeToConfig();
                Config::getInstance()->save();
                $result['result'] = 'saved';
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
