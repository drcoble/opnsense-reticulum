"""Reticulum peer node manager for integration testing.

Starts a minimal rnsd instance on the CI runner with a TCPServerInterface
so the OPNsense VM under test can connect to a real peer.

In CI the workflow starts the peer before pytest runs and passes the
peer hash/port via environment variables. This module is also used
directly by the workflow start step.
"""

import os
import re
import shutil
import subprocess
import tempfile
import time

PEER_PORT = 14242
HASH_RE = re.compile(r"[a-fA-F0-9]{32,64}")


class ReticulumPeer:
    """Manages a local rnsd process for integration test peer connectivity."""

    def __init__(self, port: int = PEER_PORT):
        self.port = port
        self.peer_hash: str = ""
        self._tempdir: str = ""
        self._proc: subprocess.Popen | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, listen_ip: str = "0.0.0.0") -> "ReticulumPeer":
        """Start rnsd and capture the local destination hash."""
        self._tempdir = tempfile.mkdtemp(prefix="rns-peer-test-")
        self._write_config(listen_ip)

        self._proc = subprocess.Popen(
            ["rnsd", "--config", self._tempdir, "--verbose"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # Give rnsd time to initialise and write its identity
        time.sleep(6)

        self.peer_hash = self._get_local_hash()
        if not self.peer_hash:
            raise RuntimeError("Failed to retrieve peer hash from rnid — rnsd may not have started")

        return self

    def stop(self) -> None:
        """Terminate rnsd and clean up temporary files."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
        if self._tempdir and os.path.isdir(self._tempdir):
            shutil.rmtree(self._tempdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "ReticulumPeer":
        return self.start()

    def __exit__(self, *_) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_config(self, listen_ip: str) -> None:
        config_path = os.path.join(self._tempdir, "config")
        config = (
            "[reticulum]\n"
            "enable_transport = Yes\n"
            "share_instance = No\n"
            "\n"
            "[[TCPServerInterface]]\n"
            "  type = TCPServerInterface\n"
            "  enabled = Yes\n"
            f"  listen_ip = {listen_ip}\n"
            f"  listen_port = {self.port}\n"
        )
        with open(config_path, "w") as f:
            f.write(config)

    def _get_local_hash(self) -> str:
        """Run rnid against the peer config dir and extract the destination hash."""
        try:
            result = subprocess.run(
                ["rnid", "--config", self._tempdir],
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = result.stdout + result.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""

        # Look for a 32-char hex hash on a line containing "Hash" or "hash"
        for line in output.splitlines():
            if "hash" in line.lower() or "destination" in line.lower():
                match = re.search(r"\b([a-fA-F0-9]{32})\b", line)
                if match:
                    return match.group(1).lower()

        # Fallback: first 32-char hex string in output
        match = HASH_RE.search(output)
        if match and len(match.group(0)) == 32:
            return match.group(0).lower()

        return ""


# ---------------------------------------------------------------------------
# CLI entry point — used by the workflow start step
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import signal
    import sys

    peer = ReticulumPeer()
    peer.start(listen_ip="0.0.0.0")

    with open("/tmp/peer_hash.txt", "w") as f:
        f.write(peer.peer_hash)

    print(f"Peer started: hash={peer.peer_hash}, port={peer.port}", flush=True)

    def _shutdown(signum, frame):
        peer.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Block until killed
    peer._proc.wait()
