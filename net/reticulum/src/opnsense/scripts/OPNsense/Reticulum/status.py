#!/usr/local/bin/python3

"""
OPNsense Reticulum Plugin — Service Status Script
Returns JSON status for the OPNsense service status widget.
"""

import json
import subprocess
import sys


def is_process_running(process_name):
    """Check if a process is running by name."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', process_name],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def main():
    rnsd_running = is_process_running('/usr/local/bin/rnsd')
    lxmd_running = is_process_running('/usr/local/bin/lxmd')

    status = {
        'status': 'running' if rnsd_running else 'stopped',
        'rnsd': rnsd_running,
        'lxmd': lxmd_running
    }

    print(json.dumps(status))


if __name__ == '__main__':
    main()
