#!/usr/local/bin/python3

"""
OPNsense Reticulum Plugin — Diagnostics Script
Wraps rnstatus, rnpath, and lxmd status utilities for the diagnostics view.
Called via configd with a subcommand argument. The subcommand is validated
against an explicit allowlist in main() — unknown values are rejected.
"""

import json
import os
import subprocess
import sys

RNS_CONFIG = '/usr/local/etc/reticulum'
LXMD_PIDFILE = '/var/run/lxmd.pid'
LXMD_BIN = '/usr/local/bin/lxmd'


def run_command(cmd, timeout=10):
    """Run a command and return its stdout. Captures stderr for error reporting."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0 and not result.stdout.strip():
            err = result.stderr.strip() or "command exited non-zero"
            return json.dumps({"error": err}), result.returncode
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out"}), 1
    except FileNotFoundError:
        return json.dumps({"error": f"Command not found: {cmd[0]}"}), 1
    except OSError as e:
        return json.dumps({"error": str(e)}), 1


def parse_json_or_raw(output):
    """Try to parse as JSON, fall back to raw text."""
    try:
        return json.loads(output)
    except (json.JSONDecodeError, ValueError):
        return {"raw": output}


def _run_with_json_fallback(args_with_json, args_without_json):
    """Run a command with -j (JSON) flag first.

    If the output cannot be parsed as valid JSON, retry without the flag for
    compatibility with older RNS versions that do not support -j.
    """
    output, _ = run_command(args_with_json)
    try:
        return json.loads(output)
    except (json.JSONDecodeError, ValueError):
        pass
    output, _ = run_command(args_without_json)
    return parse_json_or_raw(output)


def _is_lxmd_running():
    """Check if lxmd is running using its PID file, falling back to pgrep."""
    try:
        if os.path.isfile(LXMD_PIDFILE):
            with open(LXMD_PIDFILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # signal 0: probe only, raises OSError if not running
            return True
    except (OSError, ValueError):
        pass
    try:
        result = subprocess.run(
            ['pgrep', '-f', LXMD_BIN],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def diag_rnstatus():
    """Get Reticulum network status."""
    return _run_with_json_fallback(
        ['rnstatus', '-j', '--config', RNS_CONFIG],
        ['rnstatus', '--config', RNS_CONFIG],
    )


def diag_paths():
    """Get Reticulum path table."""
    return _run_with_json_fallback(
        ['rnpath', '-j', '--config', RNS_CONFIG],
        ['rnpath', '--config', RNS_CONFIG],
    )


def diag_announces():
    """Get recent announcement history."""
    return _run_with_json_fallback(
        ['rnstatus', '-j', '-a', '--config', RNS_CONFIG],
        ['rnstatus', '-a', '--config', RNS_CONFIG],
    )


def diag_propagation():
    """Get LXMF propagation node status."""
    running = _is_lxmd_running()

    result = {
        "running": running,
        "message_count": 0,
        "peer_count": 0
    }

    if running:
        storage_path = "/var/db/lxmd/messagestore"
        try:
            if os.path.isdir(storage_path):
                count = sum(
                    1 for f in os.listdir(storage_path)
                    if os.path.isfile(os.path.join(storage_path, f))
                )
                result["message_count"] = count
        except OSError:
            pass

    return result


def diag_interfaces():
    """Get active interface statistics."""
    return _run_with_json_fallback(
        ['rnstatus', '-j', '-i', '--config', RNS_CONFIG],
        ['rnstatus', '-i', '--config', RNS_CONFIG],
    )


def diag_log():
    """Return the last 200 lines of the rnsd log."""
    log_file = '/var/log/reticulum/rnsd.log'
    if not os.path.exists(log_file):
        return {'lines': [], 'message': 'Log file not found. Start the service first.'}
    try:
        with open(log_file, 'r', errors='replace') as f:
            lines = f.readlines()
        return {'lines': [line.rstrip('\n') for line in lines[-200:]]}
    except OSError as e:
        return {'error': str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No diagnostic subcommand specified"}))
        sys.exit(1)

    subcommand = sys.argv[1]

    # Explicit allowlist — configd passes %s from user input directly;
    # this dict lookup is the sole validation gate for the subcommand.
    handlers = {
        'rnstatus': diag_rnstatus,
        'paths': diag_paths,
        'announces': diag_announces,
        'propagation': diag_propagation,
        'interfaces': diag_interfaces,
        'log': diag_log,
    }

    handler = handlers.get(subcommand)
    if handler is None:
        print(json.dumps({"error": "Unknown subcommand: " + subcommand}))
        sys.exit(1)

    result = handler()
    print(json.dumps(result))


if __name__ == '__main__':
    main()
