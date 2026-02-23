"""Deploy plugin files to OPNsense VM via SCP and run POST_INSTALL."""

import io
import os
import stat

import paramiko


def _get_ssh_client(host, ssh_key_str, username="root", port=22):
    """Create an SSH client connected to the OPNsense VM."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    pkey = paramiko.RSAKey.from_private_key(io.StringIO(ssh_key_str))

    client.connect(hostname=host, port=port, username=username, pkey=pkey)
    return client


def _upload_directory(sftp, local_dir, remote_dir):
    """Recursively upload a local directory to the remote host via SFTP."""
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"

        if os.path.isdir(local_path):
            # Skip git submodule .git files and __pycache__
            if item in (".git", "__pycache__", ".gitkeep"):
                continue
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                sftp.mkdir(remote_path)
            _upload_directory(sftp, local_path, remote_path)
        else:
            print(f"  Uploading {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)


def _deploy_plugin_files(sftp, plugin_src):
    """Deploy plugin source files to their OPNsense filesystem locations."""
    # Map source subdirectories to their OPNsense install paths
    mappings = [
        ("opnsense/mvc", "/usr/local/opnsense/mvc"),
        ("opnsense/service", "/usr/local/opnsense/service"),
        ("opnsense/scripts", "/usr/local/opnsense/scripts"),
        ("etc", "/usr/local/etc"),
        ("lib/rns-src", "/usr/local/lib/rns-src"),
        ("lib/lxmf-src", "/usr/local/lib/lxmf-src"),
    ]

    for src_subdir, remote_base in mappings:
        local_dir = os.path.join(plugin_src, src_subdir)
        if os.path.isdir(local_dir):
            print(f"Deploying {src_subdir} -> {remote_base}")
            _upload_directory(sftp, local_dir, remote_base)

    # Upload +POST_INSTALL script
    post_install_local = os.path.join(plugin_src, "+POST_INSTALL")
    if os.path.isfile(post_install_local):
        sftp.put(post_install_local, "/usr/local/+POST_INSTALL")


def deploy(host, ssh_key, plugin_src, username="root", port=22):
    """Deploy plugin to OPNsense VM and run POST_INSTALL.

    Args:
        host: OPNsense VM IP/hostname
        ssh_key: SSH private key string
        plugin_src: Local path to plugin source (e.g., 'net/reticulum/src')
        username: SSH username (default: root)
        port: SSH port (default: 22)
    """
    client = _get_ssh_client(host, ssh_key, username, port)
    try:
        sftp = client.open_sftp()

        print(f"Deploying plugin from {plugin_src} to {host}...")
        _deploy_plugin_files(sftp, plugin_src)
        sftp.close()

        # Run POST_INSTALL
        print("Running +POST_INSTALL...")
        stdin, stdout, stderr = client.exec_command("sh /usr/local/+POST_INSTALL")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        errors = stderr.read().decode()

        print(output)
        if errors:
            print(f"STDERR: {errors}")

        if exit_code != 0:
            raise RuntimeError(f"+POST_INSTALL failed with exit code {exit_code}: {errors}")

        print("Plugin deployment complete.")
    finally:
        client.close()
