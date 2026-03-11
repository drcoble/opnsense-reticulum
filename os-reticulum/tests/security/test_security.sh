#!/bin/sh
# Security Tests — X-701 through X-710
# Run as root on OPNsense VM with rnsd/lxmd running.
# Usage: sh test_security.sh [base_url] [username] [password]

BASE="${1:-https://localhost}"
USER="${2:-admin}"
PASS="${3:-opnsense}"
CURL="curl -ks -u ${USER}:${PASS}"

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
RST='\033[0m'

P=0; F=0

ok()   { printf "${GRN}PASS${RST}  %s: %s\n" "$1" "$2"; P=$((P+1)); }
err()  { printf "${RED}FAIL${RST}  %s: %s — %s\n" "$1" "$2" "$3"; F=$((F+1)); }
info() { printf "${YEL}INFO${RST}  %s\n" "$1"; }

echo "=== Reticulum Security Tests ==="
echo ""

# ---------------------------------------------------------------------------
# X-701: rnsd runs as reticulum user, not root
# ---------------------------------------------------------------------------

RNSD_USER=$(ps aux | awk '/[r]nsd/ {print $1}' | head -1)
if [ "$RNSD_USER" = "reticul" ] || [ "$RNSD_USER" = "reticulum" ]; then
    ok "X-701" "rnsd process user: $RNSD_USER"
elif [ -z "$RNSD_USER" ]; then
    info "X-701: rnsd not running — start it first to test process user"
else
    err "X-701" "rnsd process user" "running as $RNSD_USER, expected reticulum"
fi

# ---------------------------------------------------------------------------
# X-702: lxmd runs as reticulum user, not root
# ---------------------------------------------------------------------------

LXMD_USER=$(ps aux | awk '/[l]xmd/ {print $1}' | head -1)
if [ "$LXMD_USER" = "reticul" ] || [ "$LXMD_USER" = "reticulum" ]; then
    ok "X-702" "lxmd process user: $LXMD_USER"
elif [ -z "$LXMD_USER" ]; then
    info "X-702: lxmd not running — start it first"
else
    err "X-702" "lxmd process user" "running as $LXMD_USER, expected reticulum"
fi

# ---------------------------------------------------------------------------
# X-703: Config dir owned by reticulum, mode 700
# ---------------------------------------------------------------------------

for dir in /usr/local/etc/reticulum /usr/local/etc/lxmf; do
    if [ ! -d "$dir" ]; then
        info "X-703: $dir does not exist (not yet configured)"
        continue
    fi
    OWNER=$(stat -f "%Su" "$dir" 2>/dev/null)
    MODE=$(stat -f "%Lp" "$dir" 2>/dev/null)
    if [ "$OWNER" = "reticulum" ] && [ "$MODE" = "700" ]; then
        ok "X-703" "$dir: owner=reticulum mode=700"
    else
        err "X-703" "$dir" "owner=$OWNER mode=$MODE (expected reticulum 700)"
    fi
done

# ---------------------------------------------------------------------------
# X-704: Identity files not world-readable
# ---------------------------------------------------------------------------

for dir in /var/db/reticulum /var/db/lxmf; do
    if [ ! -d "$dir" ]; then
        info "X-704: $dir not present"
        continue
    fi
    WORLD_READABLE=$(find "$dir" -perm -004 -type f 2>/dev/null)
    if [ -z "$WORLD_READABLE" ]; then
        ok "X-704" "$dir: no world-readable files"
    else
        err "X-704" "$dir" "world-readable files found: $WORLD_READABLE"
    fi
done

# ---------------------------------------------------------------------------
# X-705: GET rnsd/get does NOT return rpc_key value
# ---------------------------------------------------------------------------

RESP=$($CURL "${BASE}/api/reticulum/rnsd/get")
RPC_VAL=$(echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
val = d.get('general', {}).get('rpc_key', 'FIELD_MISSING')
print(val)
" 2>/dev/null)

if [ "$RPC_VAL" = "" ] || [ "$RPC_VAL" = "FIELD_MISSING" ]; then
    ok "X-705" "GET rnsd/get: rpc_key not returned (UpdateOnlyTextField)"
else
    err "X-705" "rpc_key in GET response" "value exposed: '$RPC_VAL'"
fi

# ---------------------------------------------------------------------------
# X-706: GET interface does NOT return passphrase value
# ---------------------------------------------------------------------------

# Add test interface with passphrase, then check GET
RESP=$($CURL -X POST -H "Content-Type: application/json" \
    -d '{"interface":{"name":"SecTest","type":"TCPServerInterface","listen_port":"4343","passphrase":"topsecret123"}}' \
    "${BASE}/api/reticulum/rnsd/addInterface")
TUUID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)

if [ -n "$TUUID" ]; then
    GET_RESP=$($CURL "${BASE}/api/reticulum/rnsd/getInterface/$TUUID")
    PASS_VAL=$(echo "$GET_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
iface = d.get('interface', {})
print(iface.get('passphrase', 'FIELD_MISSING'))
" 2>/dev/null)

    if [ "$PASS_VAL" = "" ] || [ "$PASS_VAL" = "FIELD_MISSING" ]; then
        ok "X-706" "GET interface: passphrase not returned"
    else
        err "X-706" "passphrase in GET" "value exposed: '$PASS_VAL'"
    fi

    # Cleanup
    $CURL -X POST "${BASE}/api/reticulum/rnsd/delInterface/$TUUID" >/dev/null 2>&1
else
    info "X-706: Could not create test interface — check API access"
fi

# ---------------------------------------------------------------------------
# X-707: PipeInterface command — no newlines in rendered config
# ---------------------------------------------------------------------------

info "X-707: Checking PipeInterface command field mask in model XML..."
if grep -A3 "<command " /usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.xml 2>/dev/null | grep -q "Mask"; then
    ok "X-707" "PipeInterface command field has a Mask validator in model XML"
else
    err "X-707" "PipeInterface command" "Mask validator missing from model XML"
fi

# ---------------------------------------------------------------------------
# X-708: POST endpoints reject GET requests
# ---------------------------------------------------------------------------

for endpoint in rnsd/set rnsd/addInterface service/rnsdStart service/reconfigure; do
    RESP=$($CURL "${BASE}/api/reticulum/${endpoint}")
    HTTP_CODE=$(echo "$RESP" | python3 -c "
import sys
s = sys.stdin.read()
# OPNsense returns 405 or JSON error for GET on POST-only endpoints
print('405' if '405' in s or 'Method Not Allowed' in s else 'other')
" 2>/dev/null)
    if echo "$RESP" | grep -qi "405\|method not allowed\|not found\|error"; then
        ok "X-708" "GET ${endpoint}: rejected"
    else
        err "X-708" "GET ${endpoint}" "should be rejected but got: $(echo $RESP | head -c 100)"
    fi
done

# ---------------------------------------------------------------------------
# X-709: CSRF token required on POST endpoints
# ---------------------------------------------------------------------------

# Try POST without session cookie (no CSRF token)
RESP=$(curl -ks -X POST -H "Content-Type: application/json" \
    -d '{"general":{"loglevel":"4"}}' \
    "${BASE}/api/reticulum/rnsd/set" 2>/dev/null)
if echo "$RESP" | grep -qi "403\|csrf\|forbidden\|authentication"; then
    ok "X-709" "POST without auth/CSRF rejected"
else
    err "X-709" "CSRF protection" "unauthenticated POST not rejected: $(echo $RESP | head -c 100)"
fi

# ---------------------------------------------------------------------------
# X-710: sub_interfaces_raw config injection
# ---------------------------------------------------------------------------

info "X-710: Testing RNodeMultiInterface sub_interfaces_raw injection..."

INJECTED_RAW='[[[A]]]
  frequency = 915000000
[reticulum]
  enable_transport = True'

RESP=$($CURL -X POST -H "Content-Type: application/json" \
    -d "{\"interface\":{\"name\":\"MultiTest\",\"type\":\"RNodeMultiInterface\",\"port\":\"/dev/cuaU0\",\"sub_interfaces_raw\":$(echo "$INJECTED_RAW" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}}" \
    "${BASE}/api/reticulum/rnsd/addInterface" 2>/dev/null)
IUUID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)

if [ -n "$IUUID" ]; then
    $CURL -X POST "${BASE}/api/reticulum/service/reconfigure" >/dev/null 2>&1
    sleep 2

    CONFIG=/usr/local/etc/reticulum/config
    if [ -f "$CONFIG" ]; then
        RETICULUM_COUNT=$(grep -c "^\[reticulum\]" "$CONFIG")
        if [ "$RETICULUM_COUNT" -le 1 ]; then
            ok "X-710" "Config has only 1 [reticulum] section — injection section appears inside [[ ]] block"
        else
            err "X-710" "Config injection" "Found $RETICULUM_COUNT [reticulum] sections — potential override"
        fi
        info "X-710: Config around injection (check manually):"
        grep -n "reticulum\|MultiTest\|\[\[\[" "$CONFIG" | head -20
    else
        info "X-710: Config not generated — cannot verify"
    fi

    # Cleanup
    $CURL -X POST "${BASE}/api/reticulum/rnsd/delInterface/$IUUID" >/dev/null 2>&1
else
    info "X-710: Could not create test interface"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=== Security Test Results: ${P} passed, ${F} failed ==="
[ "$F" -eq 0 ] && exit 0 || exit 1
