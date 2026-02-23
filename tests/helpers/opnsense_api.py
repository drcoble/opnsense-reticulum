"""OPNsense REST API client wrapper for integration tests."""

import requests
import urllib3

# Suppress InsecureRequestWarning for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OPNsenseAPI:
    """Wrapper for OPNsense REST API calls with auth and TLS handling."""

    def __init__(self, host, api_key, api_secret, port=443, verify_ssl=False):
        self.base_url = f"https://{host}:{port}/api"
        self.auth = (api_key, api_secret)
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = self.verify_ssl

    def get(self, endpoint, **kwargs):
        """GET request to OPNsense API."""
        url = f"{self.base_url}/{endpoint}"
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint, json=None, **kwargs):
        """POST request to OPNsense API."""
        url = f"{self.base_url}/{endpoint}"
        resp = self.session.post(url, json=json, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # -- Settings endpoints --

    def get_settings(self):
        """Get general Reticulum settings."""
        return self.get("reticulum/settings/get")

    def set_settings(self, data):
        """Set general Reticulum settings."""
        return self.post("reticulum/settings/set", json={"reticulum": data})

    # -- Interface endpoints --

    def search_interfaces(self):
        """List all interfaces."""
        return self.get("reticulum/settings/searchInterface")

    def get_interface(self, uuid):
        """Get a single interface by UUID."""
        return self.get(f"reticulum/settings/getInterface/{uuid}")

    def add_interface(self, data):
        """Add a new interface."""
        return self.post("reticulum/settings/addInterface", json={"interface": data})

    def set_interface(self, uuid, data):
        """Update an existing interface."""
        return self.post(f"reticulum/settings/setInterface/{uuid}", json={"interface": data})

    def del_interface(self, uuid):
        """Delete an interface."""
        return self.post(f"reticulum/settings/delInterface/{uuid}")

    def toggle_interface(self, uuid, enabled=None):
        """Toggle interface enabled/disabled."""
        endpoint = f"reticulum/settings/toggleInterface/{uuid}"
        if enabled is not None:
            endpoint += f"/{int(enabled)}"
        return self.post(endpoint)

    # -- Service endpoints --

    def service_start(self):
        """Start the Reticulum service."""
        return self.post("reticulum/service/start")

    def service_stop(self):
        """Stop the Reticulum service."""
        return self.post("reticulum/service/stop")

    def service_restart(self):
        """Restart the Reticulum service."""
        return self.post("reticulum/service/restart")

    def service_status(self):
        """Get service status."""
        return self.get("reticulum/service/status")

    def service_reconfigure(self):
        """Reconfigure (template reload + restart)."""
        return self.post("reticulum/service/reconfigure")

    # -- Diagnostics endpoints --

    def diag_rnstatus(self):
        """Get Reticulum network status."""
        return self.get("reticulum/diagnostics/rnstatus")

    def diag_paths(self):
        """Get path table."""
        return self.get("reticulum/diagnostics/paths")

    def diag_announces(self):
        """Get recent announcements."""
        return self.get("reticulum/diagnostics/announces")

    def diag_interfaces(self):
        """Get active interface statistics."""
        return self.get("reticulum/diagnostics/interfaces")

    def diag_log(self):
        """Get recent rnsd log output."""
        return self.get("reticulum/diagnostics/log")

    def diag_general_status(self):
        """Get interface counts and bandwidth summary by medium type."""
        return self.get("reticulum/diagnostics/generalStatus")

    def diag_rnsd_info(self):
        """Get RNSD daemon info (version, uptime, running state)."""
        return self.get("reticulum/diagnostics/rnsdInfo")

    def diag_interfaces_detail(self):
        """Get detailed interface statistics (rnstatus -a)."""
        return self.get("reticulum/diagnostics/interfacesDetail")

    # -- Utilities endpoints --

    def util_rnstatus(self, detail=0):
        """Run rnstatus, optionally with detailed output (-a)."""
        return self.post("reticulum/utilities/rnstatus", json={"detail": detail})

    def util_rnid(self, hash=None):
        """Show local identity or look up a destination hash."""
        data = {}
        if hash:
            data["hash"] = hash
        return self.post("reticulum/utilities/rnid", json=data)

    def util_rnpath(self, hash=None):
        """Show path to a destination hash."""
        data = {}
        if hash:
            data["hash"] = hash
        return self.post("reticulum/utilities/rnpath", json=data)

    def util_rnprobe(self, hash=None, timeout=10):
        """Probe a destination hash with optional timeout."""
        data = {"timeout": timeout}
        if hash:
            data["hash"] = hash
        return self.post("reticulum/utilities/rnprobe", json=data)

    def util_rnodeconfig(self, device=None):
        """List or inspect RNode devices."""
        data = {}
        if device:
            data["device"] = device
        return self.post("reticulum/utilities/rnodeconfig", json=data)

    def util_rncp(self):
        """Get rncp usage/help text."""
        return self.post("reticulum/utilities/rncp", json={})

    def util_rnx(self):
        """Get rnx usage/help text."""
        return self.post("reticulum/utilities/rnx", json={})
