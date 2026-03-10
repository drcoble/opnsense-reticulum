"""Shared pytest fixtures for OPNsense Reticulum integration tests."""

import os
import pytest
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.fixture(scope="session")
def opnsense_cfg():
    host = os.environ.get("OPNSENSE_HOST")
    key = os.environ.get("OPNSENSE_API_KEY")
    secret = os.environ.get("OPNSENSE_API_SECRET")
    if not all([host, key, secret]):
        pytest.skip("OPNSENSE_HOST / OPNSENSE_API_KEY / OPNSENSE_API_SECRET not set")
    return {"base_url": f"https://{host}", "auth": (key, secret)}


@pytest.fixture(scope="session")
def api(opnsense_cfg):
    cfg = opnsense_cfg

    class Client:
        def get(self, path, **kw):
            return self._req("GET", path, **kw)

        def post(self, path, **kw):
            return self._req("POST", path, **kw)

        def _req(self, method, path, **kw):
            kw.setdefault("auth", cfg["auth"])
            kw.setdefault("verify", False)
            kw.setdefault("timeout", 30)
            return requests.request(method, cfg["base_url"] + path, **kw)

    return Client()
