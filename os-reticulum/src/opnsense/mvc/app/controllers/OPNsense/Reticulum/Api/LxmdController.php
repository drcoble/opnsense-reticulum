<?php

namespace OPNsense\Reticulum\Api;

use OPNsense\Base\ApiMutableModelControllerBase;
use OPNsense\Core\Config;

class LxmdController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'Reticulum';
    protected static $internalModelClass = 'OPNsense\Reticulum\Reticulum';

    /**
     * Flatten getNodes()-style option metadata to scalar values.
     *
     * @see RnsdController::flattenOptionValues() for detailed documentation.
     *
     * @param array $data POST data, possibly containing option metadata arrays
     * @return array flattened data with only scalar string values
     */
    private function flattenOptionValues(array $data): array
    {
        $result = [];
        foreach ($data as $key => $value) {
            if (is_array($value)) {
                $selected = null;
                foreach ($value as $optKey => $optMeta) {
                    if (is_array($optMeta) && !empty($optMeta['selected'])) {
                        $selected = (string)$optKey;
                        break;
                    }
                }
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
     * GET api/reticulum/lxmd/get
     * Returns the lxmf settings node.
     *
     * Note: getBase() is designed for ArrayField items and calls Add() which
     * does not exist on flat container nodes. For flat settings sections we
     * must access the model node directly via getNodes().
     */
    public function getAction()
    {
        return ['lxmf' => $this->getModel()->lxmf->getNodes()];
    }

    /**
     * POST api/reticulum/lxmd/set
     * Saves lxmf settings.
     *
     * Note: setBase() requires a UUID (ArrayField pattern) and will either
     * throw a TypeError or skip the update when called without one. For flat
     * settings sections we apply the post data directly to the model node,
     * validate, and save — mirroring the parent setAction() pattern but
     * scoped to the 'lxmf' subtree.
     */
    public function setAction()
    {
        $result = ['result' => 'failed'];
        if ($this->request->isPost()) {
            $mdl = $this->getModel();
            $postData = $this->request->getPost('lxmf') ?? [];
            $mdl->lxmf->setNodes($this->flattenOptionValues($postData));
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
}
