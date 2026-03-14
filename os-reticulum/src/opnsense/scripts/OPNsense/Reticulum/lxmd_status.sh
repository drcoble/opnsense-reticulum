#!/bin/sh

PIDFILE="/var/run/lxmd.pid"
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if [ -n "$PID" ] && ps -p "$PID" -o pid= >/dev/null 2>&1; then
        echo '{"status":"running"}'
        exit 0
    fi
fi
echo '{"status":"stopped"}'
