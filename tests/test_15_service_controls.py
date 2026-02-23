"""Test 15: Service controls and status reporting.

Tests for the General page service controls (Start/Stop/Restart) and the
status indicator that shows rnsd state.  Covers both the API layer and
the web GUI HTML to confirm they agree with each other.

Coverage:
  - /api/reticulum/service/status returns correct structure and values
  - Service start/stop/restart transitions via the control API endpoints
  - Disabled state is reported correctly
  - /ui/reticulum/general HTML contains the status badge and control buttons
  - Page JavaScript references the correct API endpoints and functions
  - API status accurately reflects the actual process state (SSH cross-check)
"""

import time

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _status(api):
    """Fetch service status and return the parsed response dict."""
    return api.service_status()


# ---------------------------------------------------------------------------
# Status API structure
# ---------------------------------------------------------------------------

class TestServiceStatusAPI:
    """Tests for the /api/reticulum/service/status endpoint."""

    def test_status_returns_dict(self, api):
        """Status endpoint returns a dict."""
        data = _status(api)
        assert isinstance(data, dict), f"Expected dict, got: {type(data)}"

    def test_status_has_status_key(self, api):
        """Response contains a 'status' key."""
        data = _status(api)
        assert "status" in data, f"Missing 'status' key: {data}"

    def test_status_value_is_recognised(self, api):
        """'status' value is one of: running, stopped, disabled."""
        data = _status(api)
        assert data["status"] in ("running", "stopped", "disabled"), (
            f"Unexpected status value: {data['status']}"
        )

    def test_disabled_state_when_plugin_disabled(self, api):
        """Disabling the plugin causes status to return 'disabled'."""
        api.set_settings({"enabled": "0"})
        api.service_reconfigure()
        time.sleep(4)

        data = _status(api)
        assert data["status"] == "disabled", (
            f"Expected 'disabled' after setting enabled=0, got: {data}"
        )

    def test_rnsd_false_when_stopped(self, api):
        """'rnsd' field is falsy when the service is not running."""
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(5)
        api.service_stop()
        time.sleep(4)

        data = _status(api)
        assert data["status"] == "stopped", f"Expected 'stopped': {data}"
        assert not data.get("rnsd"), f"Expected rnsd falsy when stopped: {data}"

    def test_rnsd_true_when_running(self, api, wait_for_service):
        """'rnsd' field is True when the service is running."""
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(3)
        api.service_start()

        def check():
            d = _status(api)
            return d.get("status") == "running" and d.get("rnsd") is True

        wait_for_service(check, "rnsd=true in status response", timeout=30)

        data = _status(api)
        assert data["status"] == "running", f"Expected 'running': {data}"
        assert data.get("rnsd") is True, f"Expected rnsd=true: {data}"


# ---------------------------------------------------------------------------
# Service lifecycle transitions
# ---------------------------------------------------------------------------

class TestServiceLifecycleTransitions:
    """Start/Stop/Restart lifecycle tests verifying clean state transitions."""

    @pytest.fixture(autouse=True, scope="class")
    def ensure_enabled(self, api):
        """Enable the plugin for all tests in this class; disable and stop after."""
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(5)
        yield
        try:
            api.service_stop()
        except Exception:
            pass
        time.sleep(2)
        api.set_settings({"enabled": "0"})

    def test_start_transitions_to_running(self, api, wait_for_service):
        """POST /service/start transitions status to 'running'."""
        api.service_start()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "service running after start", timeout=30)

    def test_stop_transitions_to_stopped(self, api):
        """POST /service/stop transitions status to 'stopped'."""
        api.service_start()
        time.sleep(6)

        api.service_stop()
        time.sleep(5)

        data = _status(api)
        assert data["status"] == "stopped", f"Expected 'stopped' after stop: {data}"

    def test_restart_from_stopped_starts_service(self, api, wait_for_service):
        """POST /service/restart from stopped state starts the service."""
        api.service_stop()
        time.sleep(4)

        api.service_restart()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "service running after restart from stopped", timeout=35)

    def test_restart_from_running_returns_to_running(self, api, wait_for_service):
        """POST /service/restart from running state restarts and returns to 'running'."""
        api.service_start()
        time.sleep(6)

        assert _status(api).get("status") == "running", "Pre-condition: service must be running"

        api.service_restart()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "service running after restart from running", timeout=35)

    def test_reconfigure_with_enabled_starts_service(self, api, wait_for_service):
        """POST /service/reconfigure with enabled=1 starts the service."""
        api.service_stop()
        time.sleep(3)

        api.service_reconfigure()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "service running after reconfigure", timeout=30)

    def test_reconfigure_with_disabled_reports_disabled(self, api):
        """POST /service/reconfigure with enabled=0 stops and reports 'disabled'."""
        api.set_settings({"enabled": "0"})
        api.service_reconfigure()
        time.sleep(5)

        data = _status(api)
        assert data["status"] == "disabled", (
            f"Expected 'disabled' after reconfigure with enabled=0: {data}"
        )

        # Re-enable for subsequent tests in this class
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(5)


# ---------------------------------------------------------------------------
# General page UI elements
# ---------------------------------------------------------------------------

class TestGeneralPageUIElements:
    """Tests that the General page HTML contains the status badge and controls.

    The status badge is rendered dynamically by JavaScript after calling
    /api/reticulum/service/status. These tests verify that the correct DOM
    elements and JavaScript functions are present in the page source.
    """

    @pytest.fixture(scope="class")
    def page_html(self, ui_session):
        """Fetch and return the General settings page HTML once per class."""
        url = f"{ui_session.base_url}/ui/reticulum/general"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200, (
            f"/ui/reticulum/general returned HTTP {resp.status_code}"
        )
        return resp.text

    def test_general_page_returns_200(self, ui_session):
        """GET /ui/reticulum/general returns HTTP 200."""
        url = f"{ui_session.base_url}/ui/reticulum/general"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200

    def test_page_contains_reticulum_content(self, page_html):
        """Page body references 'Reticulum' and is not an error page."""
        assert "reticulum" in page_html.lower()

    # -- DOM elements --

    def test_page_has_status_badge(self, page_html):
        """HTML contains the rnsd_status_badge element."""
        assert "rnsd_status_badge" in page_html, (
            "Status badge element (id='rnsd_status_badge') missing from page HTML"
        )

    def test_page_has_start_button(self, page_html):
        """HTML contains the Start service button."""
        assert "startAct" in page_html, (
            "Start button (id='startAct') missing from page HTML"
        )

    def test_page_has_stop_button(self, page_html):
        """HTML contains the Stop service button."""
        assert "stopAct" in page_html, (
            "Stop button (id='stopAct') missing from page HTML"
        )

    def test_page_has_restart_button(self, page_html):
        """HTML contains the Restart service button."""
        assert "restartAct" in page_html, (
            "Restart button (id='restartAct') missing from page HTML"
        )

    def test_page_has_save_button(self, page_html):
        """HTML contains the Save settings button."""
        assert "saveAct" in page_html, (
            "Save button (id='saveAct') missing from page HTML"
        )

    def test_page_has_apply_button(self, page_html):
        """HTML contains the Apply (save + reconfigure) button."""
        assert "applyAct" in page_html, (
            "Apply button (id='applyAct') missing from page HTML"
        )

    # -- JavaScript functions --

    def test_page_js_calls_status_api(self, page_html):
        """Page JavaScript calls the service status API endpoint."""
        assert "reticulum/service/status" in page_html, (
            "Status API endpoint reference missing from page JavaScript"
        )

    def test_page_js_has_refresh_status_fn(self, page_html):
        """Page JavaScript defines refreshServiceStatus."""
        assert "refreshServiceStatus" in page_html, (
            "refreshServiceStatus function missing from page JavaScript"
        )

    def test_page_js_has_render_badge_fn(self, page_html):
        """Page JavaScript defines renderStatusBadge."""
        assert "renderStatusBadge" in page_html, (
            "renderStatusBadge function missing from page JavaScript"
        )

    def test_page_js_has_service_action_fn(self, page_html):
        """Page JavaScript defines serviceAction (used by Start/Stop/Restart)."""
        assert "serviceAction" in page_html, (
            "serviceAction function missing from page JavaScript"
        )

    # -- Badge CSS classes for status states --

    def test_page_js_has_running_badge_class(self, page_html):
        """Page JavaScript contains label-success CSS class for 'Running' state."""
        assert "label-success" in page_html, (
            "label-success CSS class (Running badge) missing from page JavaScript"
        )

    def test_page_js_has_stopped_badge_class(self, page_html):
        """Page JavaScript contains label-danger CSS class for 'Stopped' state."""
        assert "label-danger" in page_html, (
            "label-danger CSS class (Stopped badge) missing from page JavaScript"
        )

    def test_page_js_has_disabled_badge_class(self, page_html):
        """Page JavaScript contains label-default CSS class for 'Disabled' state."""
        assert "label-default" in page_html, (
            "label-default CSS class (Disabled badge) missing from page JavaScript"
        )


# ---------------------------------------------------------------------------
# SSH cross-verification: API status vs actual process state
# ---------------------------------------------------------------------------

class TestSSHProcessVerification:
    """Cross-verify that the API status matches the actual rnsd process state."""

    @pytest.fixture(autouse=True, scope="class")
    def ensure_enabled(self, api):
        """Enable the plugin for SSH verification tests."""
        api.set_settings({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(5)
        yield
        try:
            api.service_stop()
        except Exception:
            pass
        time.sleep(2)
        api.set_settings({"enabled": "0"})

    def test_running_status_matches_pgrep(self, api, ssh, wait_for_service):
        """When API reports 'running', pgrep -x rnsd finds the process."""
        api.service_start()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "rnsd running via API", timeout=30)

        _, _, rc = ssh("pgrep -x rnsd")
        assert rc == 0, "API reports 'running' but pgrep -x rnsd found no process"

    def test_stopped_status_matches_no_process(self, api, ssh):
        """When API reports 'stopped', pgrep -x rnsd finds no process."""
        api.service_stop()
        time.sleep(5)

        data = _status(api)
        assert data["status"] == "stopped"

        _, _, rc = ssh("pgrep -x rnsd")
        assert rc != 0, "API reports 'stopped' but pgrep -x rnsd found a running process"

    def test_pid_file_exists_when_running(self, api, ssh, wait_for_service):
        """PID file /var/run/rnsd.pid is created when service starts."""
        ssh("rm -f /var/run/rnsd.pid")
        api.service_start()

        def check():
            stdout, _, _ = ssh("test -f /var/run/rnsd.pid && echo yes || echo no")
            return "yes" in stdout

        wait_for_service(check, "PID file created", timeout=20)

        pid_out, _, _ = ssh("cat /var/run/rnsd.pid")
        assert pid_out.strip().isdigit(), (
            f"PID file exists but contains non-numeric content: '{pid_out}'"
        )

    def test_pid_file_absent_when_stopped(self, api, ssh):
        """PID file /var/run/rnsd.pid is absent after service stops."""
        api.service_start()
        time.sleep(6)

        api.service_stop()
        time.sleep(5)

        stdout, _, _ = ssh("test -f /var/run/rnsd.pid && echo present || echo absent")
        assert "absent" in stdout, (
            f"PID file still present after service stop: {stdout}"
        )

    def test_service_runs_as_reticulum_user(self, api, ssh, wait_for_service):
        """rnsd process runs as the _reticulum service user."""
        api.service_start()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "rnsd running", timeout=25)

        stdout, _, _ = ssh(
            "ps -o user= -p $(pgrep -x rnsd 2>/dev/null | head -1) 2>/dev/null || echo ''"
        )
        assert "_reticulum" in stdout, (
            f"rnsd is not running as _reticulum user, got: '{stdout.strip()}'"
        )

    def test_log_file_written_when_running(self, api, ssh, wait_for_service):
        """Log file /var/log/reticulum/rnsd.log is written after service starts."""
        api.service_stop()
        time.sleep(3)
        ssh("truncate -s 0 /var/log/reticulum/rnsd.log 2>/dev/null || true")
        api.service_start()

        def check():
            return _status(api).get("status") == "running"

        wait_for_service(check, "rnsd running", timeout=25)
        # Give the daemon a moment to write its startup log lines
        time.sleep(3)

        stdout, _, _ = ssh(
            "test -s /var/log/reticulum/rnsd.log && echo has_content || echo empty"
        )
        assert "has_content" in stdout, (
            "rnsd.log is empty after service start — daemon may not be logging"
        )
