#!/usr/local/bin/python3

"""
OPNsense Reticulum Plugin — Utilities Script
Provides a safe interface to Reticulum CLI tools for the Utilities page.
Called via configd with a subcommand and optional sanitized arguments.
All parameters are validated against strict allowlists before use.
"""

import json
import re
import subprocess
import sys

RNS_CONFIG = '/usr/local/etc/reticulum'

# Valid hex hash: exactly 32 hex characters (128-bit Reticulum destination hash)
HASH_RE = re.compile(r'^[a-fA-F0-9]{32}$')
# Valid device path: /dev/ttyXXX or /dev/cuaXXX etc.
DEVICE_RE = re.compile(r'^/dev/[a-zA-Z0-9_.\-]+$')


def run_command(cmd, timeout=15):
    """Run a command and return structured output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        combined = (result.stdout + result.stderr).strip()
        return {
            'output': combined,
            'returncode': result.returncode,
            'success': result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {'output': 'Command timed out after ' + str(timeout) + ' seconds.',
                'returncode': 1, 'success': False}
    except FileNotFoundError as e:
        return {'output': f'Command not found: {cmd[0]}', 'returncode': 1, 'success': False}
    except OSError as e:
        return {'output': str(e), 'returncode': 1, 'success': False}


def util_rnstatus(args):
    """Run rnstatus, optionally with -a for all details."""
    cmd = ['rnstatus', '--config', RNS_CONFIG]
    if 'detail' in args:
        cmd.append('-a')
    return run_command(cmd)


def util_rnstatus_detail(args):
    """Run rnstatus -a for detailed output."""
    return run_command(['rnstatus', '-a', '--config', RNS_CONFIG])


def util_rnid(args):
    """Run rnid — show local identity or look up a hash."""
    extra = args[0] if args else None
    if extra:
        if not HASH_RE.match(extra):
            return {'output': 'Invalid destination hash. Must be 32 hex characters.',
                    'returncode': 1, 'success': False}
        cmd = ['rnid', extra, '--config', RNS_CONFIG]
    else:
        cmd = ['rnid', '--config', RNS_CONFIG]
    return run_command(cmd)


def util_rnpath(args):
    """Run rnpath — show path to a destination."""
    if not args:
        return {'output': 'Destination hash is required.', 'returncode': 1, 'success': False}
    dest = args[0]
    if not HASH_RE.match(dest):
        return {'output': 'Invalid destination hash. Must be 32 hex characters.',
                'returncode': 1, 'success': False}
    return run_command(['rnpath', dest, '--config', RNS_CONFIG])


def util_rnprobe(args):
    """Run rnprobe — probe a destination with optional timeout."""
    if not args:
        return {'output': 'Destination hash is required.', 'returncode': 1, 'success': False}
    dest = args[0]
    if not HASH_RE.match(dest):
        return {'output': 'Invalid destination hash. Must be 32 hex characters.',
                'returncode': 1, 'success': False}
    timeout = 10
    if len(args) > 1:
        try:
            timeout = max(1, min(60, int(args[1])))
        except ValueError:
            pass
    return run_command(['rnprobe', dest, '--config', RNS_CONFIG, '--timeout', str(timeout)],
                       timeout=timeout + 5)


def util_rnodeconf(args):
    """Run rnodeconf — configure or inspect an RNode device."""
    if not args:
        # List available serial devices
        return run_command(['rnodeconf', '--list'])
    device = args[0]
    if not DEVICE_RE.match(device):
        return {'output': 'Invalid device path. Must be a /dev/ path.',
                'returncode': 1, 'success': False}
    return run_command(['rnodeconf', device, '--info'])


def util_rncp_help(args):
    """Show rncp usage information."""
    result = run_command(['rncp', '--help'])
    if not result['success'] and not result['output']:
        result['output'] = (
            'rncp — Reticulum File Copy\n\n'
            'Usage: rncp [options] <source> <destination>\n\n'
            'rncp transfers files to or from a remote Reticulum destination.\n'
            'It is designed for use as a CLI tool and requires shell access.\n\n'
            'To use rncp from the command line:\n'
            '  rncp <local_file> <destination_hash>:<remote_path>\n'
            '  rncp <destination_hash>:<remote_path> <local_file>\n\n'
            'Run "rncp --help" from the shell for full documentation.'
        )
    return result


def util_rnx_help(args):
    """Show rnx usage information."""
    result = run_command(['rnx', '--help'])
    if not result['success'] and not result['output']:
        result['output'] = (
            'rnx — Reticulum Remote Execution\n\n'
            'Usage: rnx [options] <destination_hash> <command>\n\n'
            'rnx executes a command on a remote Reticulum destination.\n'
            'It is designed for use as a CLI tool and requires shell access.\n\n'
            'To use rnx from the command line:\n'
            '  rnx <destination_hash> <command>\n\n'
            'Run "rnx --help" from the shell for full documentation.'
        )
    return result


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'output': 'No utility subcommand specified.',
                          'returncode': 1, 'success': False}))
        sys.exit(1)

    subcommand = sys.argv[1]
    extra_args = sys.argv[2:]

    handlers = {
        'rnstatus': util_rnstatus,
        'rnstatus_detail': util_rnstatus_detail,
        'rnid': util_rnid,
        'rnpath': util_rnpath,
        'rnprobe': util_rnprobe,
        'rnodeconf': util_rnodeconf,
        'rncp_help': util_rncp_help,
        'rnx_help': util_rnx_help,
    }

    handler = handlers.get(subcommand)
    if handler is None:
        print(json.dumps({'output': 'Unknown utility: ' + subcommand,
                          'returncode': 1, 'success': False}))
        sys.exit(1)

    result = handler(extra_args)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
