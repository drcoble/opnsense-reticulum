"""Shared pytest fixtures for OPNsense Reticulum integration tests."""

import io
import os
import time

import paramiko
import pytest

from tests.helpers.opnsense_api import OPNsenseAPI


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests requiring OPNsense VM")


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def _require_env(name):
    """Get a required environment variable or skip the test."""
    val = os.environ.get(name)
    if not val:
        pytest.skip(f"Missing required environment variable: {name}")
    return val


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def opnsense_host():
    return _require_env("OPNSENSE_HOST")


@pytest.fixture(scope="session")
def api(opnsense_host):
    """OPNsense API client for the test session."""
    return OPNsenseAPI(
        host=opnsense_host,
        api_key=_require_env("OPNSENSE_API_KEY"),
        api_secret=_require_env("OPNSENSE_API_SECRET"),
    )


@pytest.fixture(scope="session")
def ssh_client(opnsense_host):
    """Paramiko SSH client connected to the OPNsense VM."""
    key_str = _require_env("OPNSENSE_SSH_KEY")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_str))
    client.connect(hostname=opnsense_host, username="root", pkey=pkey)
    yield client
    client.close()


def ssh_exec(client, command, timeout=30):
    """Execute a command via SSH and return (stdout, stderr, exit_code)."""
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    return stdout.read().decode().strip(), stderr.read().decode().strip(), exit_code


@pytest.fixture(scope="session")
def ssh(ssh_client):
    """Convenience wrapper returning an ssh_exec function bound to the session client."""
    def _exec(command, timeout=30):
        return ssh_exec(ssh_client, command, timeout)
    return _exec


@pytest.fixture
def wait_for_service():
    """Return a callable that waits for a service condition with polling."""
    def _wait(check_fn, description="condition", timeout=30, interval=2):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if check_fn():
                return True
            time.sleep(interval)
        raise TimeoutError(f"Timed out waiting for: {description}")
    return _wait


@pytest.fixture(scope="session")
def runner_ip():
    """IP of the CI runner reachable from the OPNsense VM.

    Set via RUNNER_IP environment variable. Tests using this fixture
    will skip if the variable is absent (e.g. local dev runs).
    """
    return _require_env("RUNNER_IP")


@pytest.fixture(scope="session")
def reticulum_peer():
    """Provide metadata for the pre-started Reticulum peer node.

    In CI the peer is started by the workflow before pytest runs and the
    hash/port are passed as environment variables. Tests that depend on
    this fixture skip automatically when RUNNER_IP is not set.
    """
    peer_hash = os.environ.get("RETICULUM_PEER_HASH", "")
    peer_port = int(os.environ.get("RETICULUM_PEER_PORT", "14242"))

    if not peer_hash:
        pytest.skip("Reticulum peer not available (RETICULUM_PEER_HASH not set)")

    class _PeerInfo:
        hash = peer_hash
        port = peer_port

    return _PeerInfo()
