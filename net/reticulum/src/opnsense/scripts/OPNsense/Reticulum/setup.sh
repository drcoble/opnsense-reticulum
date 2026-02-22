#!/bin/sh

# OPNsense Reticulum Plugin — Service Management Script
# Manages both rnsd (Reticulum daemon) and lxmd (LXMF propagation daemon)
# independently based on per-service enable flags in the generated configs.

RNSD_BIN="/usr/local/bin/rnsd"
LXMD_BIN="/usr/local/bin/lxmd"
RNS_CONFIG_DIR="/usr/local/etc/reticulum"
LXMD_CONFIG_DIR="/usr/local/etc/lxmd"
SERVICE_USER="_reticulum"
RNSD_PID="/var/run/rnsd.pid"
LXMD_PID="/var/run/lxmd.pid"

# Check if the LXMF service is enabled via the generated lxmd config.
# The template writes a sentinel comment when general.enable_lxmf=1.
is_lxmf_enabled() {
    if [ -f "${LXMD_CONFIG_DIR}/config" ]; then
        grep -q "^# __lxmf_enabled__ = yes" "${LXMD_CONFIG_DIR}/config" 2>/dev/null
        return $?
    fi
    return 1
}

# Check if lxmd must wait for rnsd before starting.
# The template writes a sentinel comment when general.lxmf_bind_to_rnsd=1.
is_lxmf_bound_to_rnsd() {
    if [ -f "${LXMD_CONFIG_DIR}/config" ]; then
        grep -q "^# __lxmf_bind_rnsd__ = yes" "${LXMD_CONFIG_DIR}/config" 2>/dev/null
        return $?
    fi
    # Default: bound to rnsd for safety
    return 0
}

start_rnsd() {
    if pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
        echo "rnsd is already running"
        return 0
    fi

    echo "Starting rnsd..."
    daemon -u ${SERVICE_USER} -p ${RNSD_PID} -o /var/log/reticulum/rnsd.log \
        ${RNSD_BIN} --config "${RNS_CONFIG_DIR}"

    # Wait for rnsd to initialize and create the shared instance socket
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
        sleep 5
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
    if ! is_lxmf_enabled; then
        echo "LXMF service not enabled, skipping lxmd"
        return 0
    fi

    if pgrep -f "${LXMD_BIN}" > /dev/null 2>&1; then
        echo "lxmd is already running"
        return 0
    fi

    # Enforce rnsd dependency when binding is configured
    if is_lxmf_bound_to_rnsd; then
        if ! pgrep -f "${RNSD_BIN}" > /dev/null 2>&1; then
            echo "ERROR: rnsd must be running before starting lxmd (lxmf_bind_to_rnsd is enabled)"
            return 1
        fi
    fi

    echo "Starting lxmd..."
    daemon -u ${SERVICE_USER} -p ${LXMD_PID} -o /var/log/reticulum/lxmd.log \
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
        sleep 5
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
        start_rnsd
        start_lxmd
        ;;
    start_rnsd)
        start_rnsd
        ;;
    stop_rnsd)
        stop_rnsd
        ;;
    restart_rnsd)
        stop_rnsd
        sleep 1
        start_rnsd
        ;;
    start_lxmd)
        start_lxmd
        ;;
    stop_lxmd)
        stop_lxmd
        ;;
    restart_lxmd)
        stop_lxmd
        sleep 1
        start_lxmd
        ;;
    status)
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
        echo "Usage: $0 {start|stop|restart|start_rnsd|stop_rnsd|restart_rnsd|start_lxmd|stop_lxmd|restart_lxmd|status}"
        exit 1
        ;;
esac

exit 0
