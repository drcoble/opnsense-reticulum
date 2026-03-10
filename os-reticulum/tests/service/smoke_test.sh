#!/bin/sh
# Quick Smoke Test — Post-install verification on OPNsense VM
# Run as root on the OPNsense VM after: pkg install os-reticulum
#
# Usage: sh smoke_test.sh

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
RST='\033[0m'

PASS=0
FAIL=0
INFO=0

ok()   { printf "${GRN}PASS${RST}  %s\n" "$1"; PASS=$((PASS+1)); }
err()  { printf "${RED}FAIL${RST}  %s\n" "$1"; FAIL=$((FAIL+1)); }
info() { printf "${YEL}INFO${RST}  %s\n" "$1"; INFO=$((INFO+1)); }

echo "=== OPNsense Reticulum Smoke Test ==="
echo "Date: $(date)"
echo ""

# ---------------------------------------------------------------------------
# S-401: User and group
# ---------------------------------------------------------------------------

echo "--- User & group ---"
if pw usershow reticulum >/dev/null 2>&1; then
    ok "S-401a: reticulum user exists"
else
    err "S-401a: reticulum user MISSING"
fi

if id reticulum 2>/dev/null | grep -q "dialer"; then
    ok "S-401b: reticulum user in dialer group"
else
    err "S-401b: reticulum user NOT in dialer group"
fi

# ---------------------------------------------------------------------------
# S-401: Virtualenv
# ---------------------------------------------------------------------------

echo ""
echo "--- Virtualenv ---"
if [ -x /usr/local/reticulum-venv/bin/rnsd ]; then
    ok "S-401c: rnsd binary in virtualenv"
else
    err "S-401c: rnsd binary MISSING at /usr/local/reticulum-venv/bin/rnsd"
fi

if [ -x /usr/local/reticulum-venv/bin/lxmd ]; then
    ok "S-401d: lxmd binary in virtualenv"
else
    err "S-401d: lxmd binary MISSING at /usr/local/reticulum-venv/bin/lxmd"
fi

RNSD_VER=$(/usr/local/reticulum-venv/bin/rnsd --version 2>&1 | head -1)
info "rnsd version: ${RNSD_VER:-unknown}"

# ---------------------------------------------------------------------------
# S-401: Directories
# ---------------------------------------------------------------------------

echo ""
echo "--- Directories ---"
for d in /usr/local/etc/reticulum /usr/local/etc/lxmf /var/db/reticulum /var/db/lxmf /var/log/reticulum; do
    if [ -d "$d" ]; then
        OWNER=$(stat -f "%Su" "$d" 2>/dev/null)
        MODE=$(stat -f "%Lp" "$d" 2>/dev/null)
        ok "S-401e: $d exists (owner=$OWNER mode=$MODE)"
    else
        err "S-401e: $d MISSING"
    fi
done

# ---------------------------------------------------------------------------
# S-401: Services not running on fresh install
# ---------------------------------------------------------------------------

echo ""
echo "--- Service state (should be stopped on fresh install) ---"
if service rnsd status 2>&1 | grep -qi "not running\|stopped"; then
    ok "S-401f: rnsd not running (expected on fresh install)"
else
    info "S-401f: rnsd appears to be running (may be expected if configured)"
fi

if service lxmd status 2>&1 | grep -qi "not running\|stopped"; then
    ok "S-401g: lxmd not running (expected on fresh install)"
else
    info "S-401g: lxmd appears to be running"
fi

# ---------------------------------------------------------------------------
# configd actions
# ---------------------------------------------------------------------------

echo ""
echo "--- configd actions ---"
if configctl reticulum status.rnsd 2>/dev/null | grep -qi "running\|stopped\|not"; then
    ok "configd: reticulum status.rnsd action works"
else
    err "configd: reticulum status.rnsd action FAILED"
fi

# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

echo ""
echo "--- Template rendering ---"
if configctl template reload OPNsense/Reticulum 2>/dev/null; then
    ok "Template reload: OPNsense/Reticulum rendered without error"
else
    err "Template reload: FAILED"
fi

if [ -f /usr/local/etc/reticulum/config ]; then
    ok "Generated: /usr/local/etc/reticulum/config exists"
else
    info "Generated: /usr/local/etc/reticulum/config not yet generated (not configured)"
fi

if [ -f /usr/local/etc/lxmf/config ]; then
    ok "Generated: /usr/local/etc/lxmf/config exists"
else
    info "Generated: /usr/local/etc/lxmf/config not yet generated (not configured)"
fi

# ---------------------------------------------------------------------------
# ACL / Menu
# ---------------------------------------------------------------------------

echo ""
echo "--- Plugin registration ---"
if grep -r "Reticulum" /usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/ >/dev/null 2>&1; then
    ok "Model files present"
else
    err "Model files MISSING"
fi

if [ -f /usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Menu/Menu.xml ]; then
    ok "Menu.xml present"
else
    err "Menu.xml MISSING"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================"
echo "Results: ${PASS} passed | ${FAIL} failed | ${INFO} info"
echo "============================================"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
