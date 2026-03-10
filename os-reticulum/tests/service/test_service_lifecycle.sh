#!/bin/sh
# Service Lifecycle Tests — S-401 through S-407
# Run as root on OPNsense VM AFTER installing and configuring the plugin.
#
# Usage: sh test_service_lifecycle.sh [test_id]
# Example: sh test_service_lifecycle.sh S-402
# Without argument: runs all tests sequentially (requires user confirmation between stages)

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
RST='\033[0m'

PASS=0; FAIL=0

ok()   { printf "${GRN}PASS${RST}  %s: %s\n" "$1" "$2"; PASS=$((PASS+1)); }
err()  { printf "${RED}FAIL${RST}  %s: %s\n" "$1" "$2"; FAIL=$((FAIL+1)); }
info() { printf "${YEL}INFO${RST}  %s\n" "$1"; }
confirm() { printf "\n>>> %s\nPress Enter when ready (Ctrl+C to skip)..." "$1"; read -r _; }

# ---------------------------------------------------------------------------
# S-402: Configure and start rnsd
# ---------------------------------------------------------------------------

test_S402() {
    echo "--- S-402: Configure and start rnsd ---"
    info "Prerequisite: rnsd must be enabled via GUI with at least one interface"
    confirm "Have you enabled rnsd and added a TCPServerInterface (port 4242) in the GUI?"

    configctl template reload OPNsense/Reticulum
    if [ -f /usr/local/etc/reticulum/config ]; then
        ok "S-402a" "Config file generated at /usr/local/etc/reticulum/config"
    else
        err "S-402a" "Config file not generated"
        return
    fi

    service rnsd start 2>/dev/null; sleep 2
    if service rnsd status 2>&1 | grep -qi "running"; then
        ok "S-402b" "rnsd service is running"
    else
        err "S-402b" "rnsd service failed to start"
    fi

    if ps aux | grep "[r]nsd" | grep -q "reticulum"; then
        ok "S-402c" "rnsd process running as reticulum user"
    else
        err "S-402c" "rnsd not running as reticulum user (check ps aux | grep rnsd)"
    fi
}

# ---------------------------------------------------------------------------
# S-403: Configure and start lxmd
# ---------------------------------------------------------------------------

test_S403() {
    echo "--- S-403: Configure and start lxmd ---"
    info "Prerequisite: rnsd must be running (S-402 passed)"

    if ! service rnsd status 2>&1 | grep -qi "running"; then
        err "S-403" "rnsd is not running — cannot test lxmd start"
        return
    fi

    confirm "Have you enabled lxmd and propagation node in the GUI, then saved?"

    configctl template reload OPNsense/Reticulum
    if [ -f /usr/local/etc/lxmf/config ]; then
        ok "S-403a" "lxmf config generated at /usr/local/etc/lxmf/config"
    else
        err "S-403a" "lxmf config not generated"
    fi

    service lxmd start 2>/dev/null; sleep 2
    if service lxmd status 2>&1 | grep -qi "running"; then
        ok "S-403b" "lxmd service is running"
    else
        err "S-403b" "lxmd service failed to start"
    fi

    if ps aux | grep "[l]xmd" | grep -q "reticulum"; then
        ok "S-403c" "lxmd process running as reticulum user"
    else
        err "S-403c" "lxmd not running as reticulum user"
    fi
}

# ---------------------------------------------------------------------------
# S-404: Boot ordering
# ---------------------------------------------------------------------------

test_S404() {
    echo "--- S-404: Boot ordering ---"
    info "This test requires a reboot. Ensure both services are enabled and configured."
    confirm "Ready to verify post-reboot state? (Reboot the VM first, then run this)"

    if service rnsd status 2>&1 | grep -qi "running"; then
        ok "S-404a" "rnsd running after reboot"
    else
        err "S-404a" "rnsd NOT running after reboot"
    fi

    if service lxmd status 2>&1 | grep -qi "running"; then
        ok "S-404b" "lxmd running after reboot"
    else
        err "S-404b" "lxmd NOT running after reboot (may be expected if not enabled)"
    fi

    if [ -f /usr/local/etc/reticulum/config ]; then
        ok "S-404c" "rnsd config exists after reboot (syshook ran)"
    else
        err "S-404c" "rnsd config missing — syshook may not have run"
    fi
}

# ---------------------------------------------------------------------------
# S-405: Stop rnsd with lxmd running
# ---------------------------------------------------------------------------

test_S405() {
    echo "--- S-405: Stop rnsd with lxmd running ---"
    info "Both services should be running for this test"

    if ! service rnsd status 2>&1 | grep -qi "running"; then
        err "S-405" "rnsd not running — start both services first"
        return
    fi
    if ! service lxmd status 2>&1 | grep -qi "running"; then
        err "S-405" "lxmd not running — start both services first"
        return
    fi

    info "Stopping rnsd while lxmd is running..."
    service rnsd stop 2>/dev/null; sleep 3

    LXMD_STATUS=$(service lxmd status 2>&1)
    info "lxmd status after rnsd stop: $LXMD_STATUS"
    if echo "$LXMD_STATUS" | grep -qi "running"; then
        info "S-405: lxmd continues running after rnsd stop (degraded/expected behavior — document)"
        ok "S-405" "Documented: lxmd behavior when rnsd stops (still running — lxmd has its own identity)"
    else
        info "S-405: lxmd stopped when rnsd stopped"
        ok "S-405" "Documented: lxmd stopped with rnsd"
    fi
}

# ---------------------------------------------------------------------------
# S-406: Settings change via GUI (reconfigure)
# ---------------------------------------------------------------------------

test_S406() {
    echo "--- S-406: Settings change via GUI ---"
    confirm "Add or modify an interface in the GUI, click Save + Apply Changes"

    BEFORE=$(stat -f "%m" /usr/local/etc/reticulum/config 2>/dev/null)
    configctl template reload OPNsense/Reticulum
    AFTER=$(stat -f "%m" /usr/local/etc/reticulum/config 2>/dev/null)

    if [ "$BEFORE" != "$AFTER" ]; then
        ok "S-406a" "Config file timestamp updated after reconfigure"
    else
        info "S-406a" "Config file timestamp unchanged (may be OK if content unchanged)"
    fi

    sleep 2
    if service rnsd status 2>&1 | grep -qi "running"; then
        ok "S-406b" "rnsd running after reconfigure"
    else
        err "S-406b" "rnsd not running after reconfigure"
    fi
}

# ---------------------------------------------------------------------------
# S-407: Clean uninstall
# ---------------------------------------------------------------------------

test_S407() {
    echo "--- S-407: Clean uninstall ---"
    info "WARNING: This will remove the plugin. Run LAST."
    confirm "Ready to uninstall os-reticulum? (Type yes or Ctrl+C to skip)"

    BEFORE_USER=$(pw usershow reticulum 2>/dev/null)
    BEFORE_DATA=$(ls /var/db/reticulum 2>/dev/null | wc -l)

    pkg delete -y os-reticulum 2>/dev/null

    if ! service rnsd status 2>&1 | grep -qi "running"; then
        ok "S-407a" "rnsd stopped after uninstall"
    else
        err "S-407a" "rnsd still running after uninstall"
    fi

    if ! [ -f /usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/Api/RnsdController.php ]; then
        ok "S-407b" "Plugin PHP files removed"
    else
        err "S-407b" "Plugin PHP files still present"
    fi

    if [ -d /var/db/reticulum ]; then
        ok "S-407c" "User data preserved: /var/db/reticulum"
    else
        err "S-407c" "User data at /var/db/reticulum was deleted (should be preserved)"
    fi

    if [ -d /usr/local/etc/reticulum ]; then
        ok "S-407d" "User config preserved: /usr/local/etc/reticulum"
    else
        info "S-407d" "/usr/local/etc/reticulum removed (check if expected per pkg-deinstall)"
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

case "${1:-all}" in
    S-402) test_S402 ;;
    S-403) test_S403 ;;
    S-404) test_S404 ;;
    S-405) test_S405 ;;
    S-406) test_S406 ;;
    S-407) test_S407 ;;
    all)
        test_S402
        test_S403
        test_S404
        test_S405
        test_S406
        test_S407
        ;;
    *) echo "Unknown test: $1"; echo "Valid: S-402 S-403 S-404 S-405 S-406 S-407 all"; exit 1 ;;
esac

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
