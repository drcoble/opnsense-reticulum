#!/bin/sh

SVC_USER="reticulum"

# Regenerate config files from templates
configctl template reload OPNsense/Reticulum

# Fix ownership and permissions of generated config files (template reload runs as root)
# chmod 640: owner (reticulum) can read/write; group can read; world cannot (X-703/X-704)
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/reticulum/config 2>/dev/null || true
chmod 640 /usr/local/etc/reticulum/config 2>/dev/null || true
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf/config 2>/dev/null || true
chmod 640 /usr/local/etc/lxmf/config 2>/dev/null || true
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf/allowed 2>/dev/null || true
chmod 640 /usr/local/etc/lxmf/allowed 2>/dev/null || true
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf/ignored 2>/dev/null || true
chmod 640 /usr/local/etc/lxmf/ignored 2>/dev/null || true

# Conditionally restart rnsd if enabled and running
if service rnsd enabled 2>/dev/null; then
    if service rnsd status >/dev/null 2>&1; then
        service rnsd restart
    fi
fi

# Conditionally restart lxmd if enabled and running
if service lxmd enabled 2>/dev/null; then
    if service lxmd status >/dev/null 2>&1; then
        service lxmd restart
    fi
fi

exit 0
