#!/bin/sh

# OPNsense Reticulum Plugin — Service Management Script
# Manages the rnsd (Reticulum daemon) service.

RNSD_BIN="/usr/local/bin/rnsd"
RNS_CONFIG_DIR="/usr/local/etc/reticulum"
SERVICE_USER="_reticulum"
RNSD_PID="/var/run/rnsd.pid"
RNSD_LOG="/var/log/reticulum/rnsd.log"

start_rnsd() {
    if [ -f "${RNSD_PID}" ]; then
        pid=$(cat "${RNSD_PID}" 2>/dev/null)
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            echo "rnsd is already running (pid ${pid})"
            return 0
        fi
        rm -f "${RNSD_PID}"
    fi

    echo "Starting rnsd..."
    /usr/sbin/daemon \
        -u "${SERVICE_USER}" \
        -p "${RNSD_PID}" \
        -o "${RNSD_LOG}" \
        -t "rnsd" \
        -- "${RNSD_BIN}" --config "${RNS_CONFIG_DIR}"

    # Allow rnsd a moment to start and write the shared-instance socket
    i=0
    while [ $i -lt 10 ]; do
        if [ -f "${RNSD_PID}" ] && kill -0 "$(cat "${RNSD_PID}" 2>/dev/null)" 2>/dev/null; then
            echo "rnsd started successfully (pid $(cat "${RNSD_PID}"))"
            return 0
        fi
        sleep 1
        i=$((i + 1))
    done

    echo "ERROR: rnsd failed to start — check ${RNSD_LOG}"
    return 1
}

stop_rnsd() {
    if [ -f "${RNSD_PID}" ]; then
        pid=$(cat "${RNSD_PID}" 2>/dev/null)
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            echo "Stopping rnsd (pid ${pid})..."
            kill "${pid}"
            i=0
            while [ $i -lt 10 ]; do
                kill -0 "${pid}" 2>/dev/null || break
                sleep 1
                i=$((i + 1))
            done
            if kill -0 "${pid}" 2>/dev/null; then
                echo "rnsd did not stop gracefully — sending SIGKILL"
                kill -9 "${pid}" 2>/dev/null
            fi
            rm -f "${RNSD_PID}"
            echo "rnsd stopped"
            return 0
        fi
        rm -f "${RNSD_PID}"
    fi

    # Fallback: catch any orphaned rnsd processes not tracked by the pid file
    if pgrep -x rnsd > /dev/null 2>&1; then
        echo "Stopping orphaned rnsd process..."
        pkill -x rnsd
        sleep 2
        pkill -9 -x rnsd 2>/dev/null || true
        echo "rnsd stopped"
    else
        echo "rnsd is not running"
    fi
}

status_rnsd() {
    if [ -f "${RNSD_PID}" ]; then
        pid=$(cat "${RNSD_PID}" 2>/dev/null)
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            echo "rnsd is running (pid ${pid})"
            return 0
        fi
    fi
    echo "rnsd is not running"
    return 1
}

case "$1" in
    start|start_rnsd)
        start_rnsd
        ;;
    stop|stop_rnsd)
        stop_rnsd
        ;;
    restart|restart_rnsd)
        stop_rnsd
        sleep 1
        start_rnsd
        ;;
    status)
        status_rnsd
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
