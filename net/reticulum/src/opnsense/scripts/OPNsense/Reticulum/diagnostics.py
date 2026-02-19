#!/usr/local/bin/python3

"""
OPNsense Reticulum Plugin — Diagnostics Script
Wraps rnstatus, rnpath, and lxmd status utilities for the diagnostics view.
Called via configd with a subcommand argument.
"""

import json
import subprocess
import sys


def run_command(cmd, timeout=10):
    """Run a command and return its stdout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return '{"error": "Command timed out"}', 1
    except FileNotFoundError:
        return '{"error": "Command not found: ' + cmd[0] + '"}', 1
    except OSError as e:
        return json.dumps({"error": str(e)}), 1


def parse_json_or_raw(output):
    """Try to parse as JSON, fall back to raw text."""
    try:
        return json.loads(output)
    except (json.JSONDecodeError, ValueError):
        return {"raw": output}


def diag_rnstatus():
    """Get Reticulum network status."""
    output, rc = run_command(['rnstatus', '-j', '--config', '/usr/local/etc/reticulum'])
    if rc != 0 and not output:
        # Try without JSON flag for older versions
        output, rc = run_command(['rnstatus', '--config', '/usr/local/etc/reticulum'])
    return parse_json_or_raw(output)


def diag_paths():
    """Get Reticulum path table."""
    output, rc = run_command(['rnpath', '-j', '--config', '/usr/local/etc/reticulum'])
    if rc != 0 and not output:
        output, rc = run_command(['rnpath', '--config', '/usr/local/etc/reticulum'])
    return parse_json_or_raw(output)


def diag_announces():
    """Get recent announcement history."""
    # rnstatus with verbose mode includes announce info
    output, rc = run_command(['rnstatus', '-j', '-a', '--config', '/usr/local/etc/reticulum'])
    if rc != 0 and not output:
        output, rc = run_command(['rnstatus', '-a', '--config', '/usr/local/etc/reticulum'])
    return parse_json_or_raw(output)


def diag_propagation():
    """Get LXMF propagation node status."""
    # Check if lxmd is running
    lxmd_output, lxmd_rc = run_command(['pgrep', '-f', '/usr/local/bin/lxmd'])
    running = lxmd_rc == 0

    result = {
        "running": running,
        "message_count": 0,
        "peer_count": 0
    }

    if running:
        # Try to get message store info
        storage_path = "/var/db/lxmd/messagestore"
        try:
            import os
            if os.path.isdir(storage_path):
                count = sum(1 for f in os.listdir(storage_path) if os.path.isfile(os.path.join(storage_path, f)))
                result["message_count"] = count
        except OSError:
            pass

    return result


def diag_interfaces():
    """Get active interface statistics."""
    output, rc = run_command(['rnstatus', '-j', '-i', '--config', '/usr/local/etc/reticulum'])
    if rc != 0 and not output:
        output, rc = run_command(['rnstatus', '-i', '--config', '/usr/local/etc/reticulum'])
    return parse_json_or_raw(output)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No diagnostic subcommand specified"}))
        sys.exit(1)

    subcommand = sys.argv[1]

    handlers = {
        'rnstatus': diag_rnstatus,
        'paths': diag_paths,
        'announces': diag_announces,
        'propagation': diag_propagation,
        'interfaces': diag_interfaces,
    }

    handler = handlers.get(subcommand)
    if handler is None:
        print(json.dumps({"error": "Unknown subcommand: " + subcommand}))
        sys.exit(1)

    result = handler()
    print(json.dumps(result))


if __name__ == '__main__':
    main()
