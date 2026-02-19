#!/bin/sh

# OPNsense Reticulum Plugin — Service Management Script
# Manages both rnsd (Reticulum daemon) and lxmd (LXMF propagation daemon)

RNSD_BIN="/usr/local/bin/rnsd"
LXMD_BIN="/usr/local/bin/lxmd"
RNS_CONFIG_DIR="/usr/local/etc/reticulum"
LXMD_CONFIG_DIR="/usr/local/etc/lxmd"
SERVICE_USER="_reticulum"
RNSD_PID="/var/run/rnsd.pid"
LXMD_PID="/var/run/lxmd.pid"

# Check if propagation is enabled by reading the generated lxmd config
is_propagation_enabled() {
    if [ -f "${LXMD_CONFIG_DIR}/config" ]; then
        grep -q "enable_propagation.*=.*Yes" "${LXMD_CONFIG_DIR}/config" 2>/dev/null
        return $?
    fi
    return 1
}

start_rnsd() {
    if pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
        echo "rnsd is already running"
        return 0
    fi

    # Regenerate configuration from templates
    configctl template reload OPNsense/Reticulum

    echo "Starting rnsd..."
    daemon -u ${SERVICE_USER} -p ${RNSD_PID} \
        ${RNSD_BIN} --config "${RNS_CONFIG_DIR}"

    # Wait for rnsd to initialize
    sleep 2

    if pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
        echo "rnsd started successfully"
    else
        echo "ERROR: rnsd failed to start"
        return 1
    fi
}

stop_rnsd() {
    if pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
        echo "Stopping rnsd..."
        pkill -f "${RNSD_BIN}"
        sleep 1
        # Force kill if still running
        if pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
            pkill -9 -f "${RNSD_BIN}"
        fi
        rm -f "${RNSD_PID}"
        echo "rnsd stopped"
    else
        echo "rnsd is not running"
    fi
}

start_lxmd() {
    if ! is_propagation_enabled; then
        echo "Propagation node not enabled, skipping lxmd"
        return 0
    fi

    if pgrep -f "${LXMD_BIN}" > /dev/null 2>&1; then
        echo "lxmd is already running"
        return 0
    fi

    # Ensure rnsd is running first
    if ! pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
        echo "ERROR: rnsd must be running before starting lxmd"
        return 1
    fi

    echo "Starting lxmd..."
    daemon -u ${SERVICE_USER} -p ${LXMD_PID} \
        ${LXMD_BIN} --config "${LXMD_CONFIG_DIR}"

    sleep 2

    if pgrep -f "${LXMD_BIN}" > /dev/null 2>&1; then
        echo "lxmd started successfully"
    else
        echo "ERROR: lxmd failed to start"
        return 1
    fi
}

stop_lxmd() {
    if pgrep -f "${LXMD_BIN}" > /dev/null 2>&1; then
        echo "Stopping lxmd..."
        pkill -f "${LXMD_BIN}"
        sleep 1
        if pgrep -f "${LXMD_BIN}" > /dev/null 2>&1; then
            pkill -9 -f "${LXMD_BIN}"
        fi
        rm -f "${LXMD_PID}"
        echo "lxmd stopped"
    else
        echo "lxmd is not running"
    fi
}

case "$1" in
    start)
        start_rnsd
        start_lxmd
        ;;
    stop)
        stop_lxmd
        stop_rnsd
        ;;
    restart)
        stop_lxmd
        stop_rnsd
        sleep 1
        # Regenerate config before restarting
        configctl template reload OPNsense/Reticulum
        start_rnsd
        start_lxmd
        ;;
    status)
        # Handled by status.py for JSON output
        if pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
            echo "rnsd is running"
        else
            echo "rnsd is not running"
        fi
        if pgrep -f "${LXMD_BIN}" > /dev/null 2>&1; then
            echo "lxmd is running"
        else
            echo "lxmd is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
