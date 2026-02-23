#!/usr/local/bin/python3.11

"""
OPNsense Reticulum Plugin — Service Status Script
Returns JSON status for the OPNsense service status widget.
"""

import json
import os
import subprocess

RNSD_PIDFILE = '/var/run/rnsd.pid'
RNSD_BIN = '/usr/local/bin/rnsd'


def is_process_running(pidfile, binary_name):
    """Check if a process is running via its PID file, falling back to pgrep.

    Reads the PID file first (consistent with the pidfile registered in
    plugins.inc.d/reticulum.inc). Falls back to pgrep -x if the PID file is
    absent or stale.
    """
    try:
        if os.path.isfile(pidfile):
            with open(pidfile) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # signal 0: existence check only
            return True
    except (OSError, ValueError):
        pass

    # Fallback: exact-name pgrep
    try:
        result = subprocess.run(
            ['pgrep', '-x', binary_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def main():
    rnsd_running = is_process_running(RNSD_PIDFILE, 'rnsd')

    status = {
        'status': 'running' if rnsd_running else 'stopped',
        'rnsd': rnsd_running,
    }

    print(json.dumps(status))


if __name__ == '__main__':
    main()
