"""Proxmox API helper for VM snapshot restore and boot wait."""

import socket
import ssl
import time

from proxmoxer import ProxmoxAPI


def get_proxmox_client(host, user, token_name, token_value):
    """Create a Proxmox API client using token authentication."""
    # Strip protocol prefix if present
    host = host.replace("https://", "").replace("http://", "")
    # Strip port if present (ProxmoxAPI adds it)
    if ":" in host:
        host, port = host.rsplit(":", 1)
        port = int(port)
    else:
        port = 8006

    return ProxmoxAPI(
        host,
        port=port,
        user=user,
        token_name=token_name,
        token_value=token_value,
        verify_ssl=False,
    )


def stop_vm(proxmox, node, vmid):
    """Stop a VM and wait for it to be fully stopped."""
    status = proxmox.nodes(node).qemu(vmid).status.current.get()
    if status.get("status") == "stopped":
        return

    proxmox.nodes(node).qemu(vmid).status.stop.post()

    for _ in range(60):
        time.sleep(2)
        status = proxmox.nodes(node).qemu(vmid).status.current.get()
        if status.get("status") == "stopped":
            return
    raise TimeoutError("VM did not stop within 120 seconds")


def rollback_snapshot(proxmox, node, vmid, snapshot):
    """Rollback a VM to a named snapshot."""
    proxmox.nodes(node).qemu(vmid).snapshot(snapshot).rollback.post()


def start_vm(proxmox, node, vmid):
    """Start a VM."""
    proxmox.nodes(node).qemu(vmid).status.start.post()


def wait_for_ssh(host, port=22, timeout=120):
    """Poll until SSH port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(3)
    raise TimeoutError(f"SSH on {host}:{port} not ready within {timeout}s")


def wait_for_https(host, port=443, timeout=120):
    """Poll until HTTPS port is accepting TLS connections."""
    deadline = time.time() + timeout
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    while time.time() < deadline:
        try:
            sock = socket.create_connection((host, port), timeout=5)
            ssl_sock = ctx.wrap_socket(sock, server_hostname=host)
            ssl_sock.close()
            return True
        except (ConnectionRefusedError, socket.timeout, ssl.SSLError, OSError):
            time.sleep(3)
    raise TimeoutError(f"HTTPS on {host}:{port} not ready within {timeout}s")


def restore_snapshot_and_wait(host, user, token_name, token_value, node, vmid, snapshot, opnsense_host):
    """Full lifecycle: stop VM -> rollback snapshot -> start VM -> wait for services."""
    proxmox = get_proxmox_client(host, user, token_name, token_value)
    vmid = str(vmid)

    print(f"Stopping VM {vmid}...")
    stop_vm(proxmox, node, vmid)

    print(f"Rolling back to snapshot '{snapshot}'...")
    rollback_snapshot(proxmox, node, vmid, snapshot)

    print(f"Starting VM {vmid}...")
    start_vm(proxmox, node, vmid)

    print(f"Waiting for SSH on {opnsense_host}...")
    wait_for_ssh(opnsense_host)

    print(f"Waiting for HTTPS on {opnsense_host}...")
    wait_for_https(opnsense_host)

    print("OPNsense VM is ready.")
