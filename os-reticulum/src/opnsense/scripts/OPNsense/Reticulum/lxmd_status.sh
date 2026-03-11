#!/bin/sh

if service lxmd status >/dev/null 2>&1; then
    echo '{"status":"running"}'
else
    echo '{"status":"stopped"}'
fi
