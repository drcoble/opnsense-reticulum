#!/usr/local/bin/python3

"""
OPNsense Reticulum Plugin — Service Status Script
Returns JSON status for the OPNsense service status widget.
"""

import json
import os
import subprocess

RNSD_PIDFILE = '/var/run/rnsd.pid'
LXMD_PIDFILE = '/var/run/lxmd.pid'
RNSD_BIN = '/usr/local/bin/rnsd'
LXMD_BIN = '/usr/local/bin/lxmd'


def is_process_running(pidfile, binary_path):
    """Check if a process is running using its PID file, falling back to pgrep.

    Reads the declared PID file first (consistent with the pidfile registered
    in plugins.inc.d/reticulum.inc). Falls back to pgrep -f if the PID file
    is absent or stale.
    """
    try:
        if os.path.isfile(pidfile):
            with open(pidfile) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # signal 0: probe only, raises OSError if not running
            return True
    except (OSError, ValueError):
        pass

    # Fallback: pgrep
    try:
        result = subprocess.run(
            ['pgrep', '-f', binary_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def main():
    rnsd_running = is_process_running(RNSD_PIDFILE, RNSD_BIN)
    lxmd_running = is_process_running(LXMD_PIDFILE, LXMD_BIN)

    status = {
        'status': 'running' if rnsd_running else 'stopped',
        'rnsd': rnsd_running,
        'lxmd': lxmd_running
    }

    print(json.dumps(status))


if __name__ == '__main__':
    main()
