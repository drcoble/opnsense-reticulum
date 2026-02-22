#!/usr/local/bin/python3

"""
OPNsense Reticulum Plugin — Diagnostics Script
Provides status data for the Status page tabs.
Called via configd with a subcommand argument. The subcommand is validated
against an explicit allowlist in main() — unknown values are rejected.
"""

import json
import os
import subprocess
import sys
import time

RNS_CONFIG = '/usr/local/etc/reticulum'
LXMD_PIDFILE = '/var/run/lxmd.pid'
RNSD_PIDFILE = '/var/run/rnsd.pid'
LXMD_BIN = '/usr/local/bin/lxmd'
RNSD_BIN = '/usr/local/bin/rnsd'

# Medium type classification by interface type keyword
MEDIUM_TYPES = {
    'UDPInterface': 'udp',
    'TCPServerInterface': 'tcp',
    'TCPClientInterface': 'tcp',
    'AutoInterface': 'auto',
    'I2PInterface': 'i2p',
    'RNodeInterface': 'radio',
    'KISSInterface': 'radio',
    'AX25KISSInterface': 'radio',
    'SerialInterface': 'serial',
}


def run_command(cmd, timeout=10):
    """Run a command and return its stdout."""
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
    """Run a command with -j (JSON) flag first, fall back if not supported."""
    output, _ = run_command(args_with_json)
    try:
        return json.loads(output)
    except (json.JSONDecodeError, ValueError):
        pass
    output, _ = run_command(args_without_json)
    return parse_json_or_raw(output)


def _is_process_running(pidfile, binary_path):
    """Check if a process is running using its PID file, falling back to pgrep."""
    try:
        if os.path.isfile(pidfile):
            with open(pidfile) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True, pid
    except (OSError, ValueError):
        pass
    try:
        result = subprocess.run(
            ['pgrep', '-f', binary_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split()
            return True, int(pids[0]) if pids else 0
    except (subprocess.TimeoutExpired, OSError, ValueError):
        pass
    return False, 0


def _get_process_uptime(pid):
    """Return process uptime in seconds using /proc or ps."""
    try:
        if pid > 0:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'etime='],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _get_binary_version(binary, flag='--version'):
    """Get version string from a binary."""
    try:
        result = subprocess.run(
            [binary, flag],
            capture_output=True, text=True, timeout=5
        )
        out = (result.stdout + result.stderr).strip()
        return out.split('\n')[0] if out else 'unknown'
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return 'unavailable'


def _get_dir_size_mb(path):
    """Return total size of a directory in MB."""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for fname in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, fname))
                except OSError:
                    pass
    except OSError:
        pass
    return round(total / (1024 * 1024), 2)


def diag_general_status():
    """Interface counts and bandwidth summary grouped by medium type."""
    raw = _run_with_json_fallback(
        ['rnstatus', '-j', '--config', RNS_CONFIG],
        ['rnstatus', '--config', RNS_CONFIG],
    )

    interfaces = []
    if isinstance(raw, list):
        interfaces = raw
    elif isinstance(raw, dict):
        # Some versions return a dict with 'interfaces' key
        interfaces = raw.get('interfaces', [])

    total = len(interfaces)
    enabled = sum(1 for i in interfaces if i.get('status') not in ('disabled',))
    up = sum(1 for i in interfaces if i.get('status') == 'up')

    # Group TX/RX by medium type
    medium_totals = {}
    for iface in interfaces:
        itype = iface.get('type', '')
        medium = MEDIUM_TYPES.get(itype, 'other')
        if medium not in medium_totals:
            medium_totals[medium] = {'tx': 0, 'rx': 0}
        medium_totals[medium]['tx'] += iface.get('txb', 0)
        medium_totals[medium]['rx'] += iface.get('rxb', 0)

    return {
        'total_interfaces': total,
        'enabled_interfaces': enabled,
        'up_interfaces': up,
        'bandwidth_by_medium': medium_totals,
    }


def diag_rnstatus():
    """Get Reticulum network status."""
    return _run_with_json_fallback(
        ['rnstatus', '-j', '--config', RNS_CONFIG],
        ['rnstatus', '--config', RNS_CONFIG],
    )


def diag_rnsd_info():
    """RNSD version and uptime."""
    running, pid = _is_process_running(RNSD_PIDFILE, RNSD_BIN)
    version = _get_binary_version(RNSD_BIN)
    uptime = _get_process_uptime(pid) if (running and pid) else None
    return {
        'running': running,
        'version': version,
        'uptime': uptime,
    }


def diag_lxmf_info():
    """LXMF daemon version and uptime."""
    running, pid = _is_process_running(LXMD_PIDFILE, LXMD_BIN)
    version = _get_binary_version(LXMD_BIN)
    uptime = _get_process_uptime(pid) if (running and pid) else None

    result = {
        'running': running,
        'version': version,
        'uptime': uptime,
    }

    if running:
        storage_path = "/var/db/lxmd/messagestore"
        try:
            if os.path.isdir(storage_path):
                msg_count = sum(
                    1 for f in os.listdir(storage_path)
                    if os.path.isfile(os.path.join(storage_path, f))
                )
                result['message_count'] = msg_count
        except OSError:
            pass

    return result


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
    """Get LXMF propagation node status (basic)."""
    running, _ = _is_process_running(LXMD_PIDFILE, LXMD_BIN)
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


def diag_propagation_detail():
    """Detailed propagation status including storage MB, peer count, errors."""
    running, pid = _is_process_running(LXMD_PIDFILE, LXMD_BIN)

    storage_path = "/var/db/lxmd/messagestore"
    message_count = 0
    storage_mb = 0.0

    if running:
        try:
            if os.path.isdir(storage_path):
                files = [
                    f for f in os.listdir(storage_path)
                    if os.path.isfile(os.path.join(storage_path, f))
                ]
                message_count = len(files)
                storage_mb = _get_dir_size_mb(storage_path)
        except OSError:
            pass

    # Read configured storage limit from lxmd config
    storage_limit_mb = None
    lxmd_conf = '/usr/local/etc/lxmd/config'
    try:
        if os.path.isfile(lxmd_conf):
            with open(lxmd_conf) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('message_storage_limit'):
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            val = parts[1].strip()
                            if val.isdigit() and int(val) > 0:
                                # Convert message count limit to estimated MB
                                # This is an approximation; lxmd config uses message count not bytes
                                storage_limit_mb = int(val)  # treat as message count
    except OSError:
        pass

    storage_pct = None
    if storage_limit_mb and storage_limit_mb > 0 and message_count > 0:
        storage_pct = round((message_count / storage_limit_mb) * 100, 1)

    return {
        'running': running,
        'message_count': message_count,
        'storage_mb': storage_mb,
        'storage_limit_messages': storage_limit_mb,
        'storage_used_pct': storage_pct,
        'peer_count': 0,   # Would need lxmd RPC or socket API to get live peer count
        'errors': [],       # Would need log parsing or lxmd API
    }


def diag_interfaces():
    """Get active interface statistics (rnstatus -i)."""
    return _run_with_json_fallback(
        ['rnstatus', '-j', '-i', '--config', RNS_CONFIG],
        ['rnstatus', '-i', '--config', RNS_CONFIG],
    )


def diag_interfaces_detail():
    """Get detailed interface statistics (rnstatus -a)."""
    return _run_with_json_fallback(
        ['rnstatus', '-j', '-a', '--config', RNS_CONFIG],
        ['rnstatus', '-a', '--config', RNS_CONFIG],
    )


def diag_log():
    """Return the last 500 lines of the rnsd log with metadata."""
    log_file = '/var/log/reticulum/rnsd.log'
    if not os.path.exists(log_file):
        return {'lines': [], 'message': 'Log file not found. Start the service first.'}
    try:
        with open(log_file, 'r', errors='replace') as f:
            lines = f.readlines()
        return {
            'lines': [line.rstrip('\n') for line in lines[-500:]],
            'total_lines': len(lines),
            'log_file': log_file,
        }
    except OSError as e:
        return {'error': str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No diagnostic subcommand specified"}))
        sys.exit(1)

    subcommand = sys.argv[1]

    handlers = {
        'general_status': diag_general_status,
        'rnstatus': diag_rnstatus,
        'rnsd_info': diag_rnsd_info,
        'lxmf_info': diag_lxmf_info,
        'paths': diag_paths,
        'announces': diag_announces,
        'propagation': diag_propagation,
        'propagation_detail': diag_propagation_detail,
        'interfaces': diag_interfaces,
        'interfaces_detail': diag_interfaces_detail,
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
