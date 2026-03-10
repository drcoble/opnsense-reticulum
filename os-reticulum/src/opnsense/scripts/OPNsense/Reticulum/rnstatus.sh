#!/bin/sh

VENV="/usr/local/reticulum-venv"
CONFIG="/usr/local/etc/reticulum"

# 5 second timeout
timeout 5 ${VENV}/bin/rnstatus --config ${CONFIG} --json 2>/dev/null || echo '{"error":"rnsd not reachable","interfaces":[]}'
