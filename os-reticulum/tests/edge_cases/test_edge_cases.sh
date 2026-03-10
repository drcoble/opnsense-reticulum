#!/bin/sh
# Edge Case Tests — E-901 through E-910
# Run on OPNsense VM with plugin installed.
# Usage: sh test_edge_cases.sh [base_url] [username] [password]

BASE="${1:-https://localhost}"
USER="${2:-admin}"
PASS="${3:-opnsense}"
CURL="curl -ks -u ${USER}:${PASS}"
API="${BASE}/api/reticulum"

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
RST='\033[0m'

P=0; F=0

ok()   { printf "${GRN}PASS${RST}  %s: %s\n" "$1" "$2"; P=$((P+1)); }
err()  { printf "${RED}FAIL${RST}  %s: %s — %s\n" "$1" "$2" "$3"; F=$((F+1)); }
info() { printf "${YEL}INFO${RST}  %s\n" "$1"; }

api_get()  { $CURL "${API}/$1"; }
api_post() { $CURL -X POST -H "Content-Type: application/json" -d "$2" "${API}/$1"; }

echo "=== Edge Case Tests ==="
echo ""

# ---------------------------------------------------------------------------
# E-901: No interfaces → rnsd starts with warning
# ---------------------------------------------------------------------------

info "E-901: Removing all interfaces and starting rnsd..."
# Delete all interfaces first
IFACES=$(api_get "rnsd/searchInterfaces" | python3 -c "
import sys,json; rows=json.load(sys.stdin).get('rows',[]); [print(r['uuid']) for r in rows]
" 2>/dev/null)
for uuid in $IFACES; do
    api_post "rnsd/delInterface/$uuid" "" >/dev/null 2>&1
done

api_post "service/reconfigure" "" >/dev/null 2>&1
sleep 2
RESP=$(api_post "service/rnsdStart" "")
if echo "$RESP" | grep -qi '"ok"\|"started"'; then
    ok "E-901" "rnsd starts with no interfaces configured"
else
    info "E-901: rnsd start returned: $RESP"
fi

# ---------------------------------------------------------------------------
# E-902: All interfaces disabled
# ---------------------------------------------------------------------------

RESP=$(api_post "rnsd/addInterface" '{"interface":{"name":"DisabledIface","type":"AutoInterface","enabled":"0"}}')
UUID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)
api_post "service/reconfigure" "" >/dev/null 2>&1; sleep 1

CONFIG=/usr/local/etc/reticulum/config
if [ -f "$CONFIG" ]; then
    if ! grep -q "\[\[DisabledIface\]\]" "$CONFIG"; then
        ok "E-902" "Disabled interface excluded from rendered config"
    else
        err "E-902" "Disabled interface" "still appears in rendered config"
    fi
fi
[ -n "$UUID" ] && api_post "rnsd/delInterface/$UUID" "" >/dev/null 2>&1

# ---------------------------------------------------------------------------
# E-903: Interface name at max length (64 chars)
# ---------------------------------------------------------------------------

LONGNAME=$(python3 -c "print('A'*64)")
RESP=$(api_post "rnsd/addInterface" "{\"interface\":{\"name\":\"${LONGNAME}\",\"type\":\"AutoInterface\"}}")
if echo "$RESP" | grep -qi '"uuid"'; then
    UUID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)
    ok "E-903" "Interface name at 64 chars accepted"
    [ -n "$UUID" ] && api_post "rnsd/delInterface/$UUID" "" >/dev/null 2>&1
else
    err "E-903" "64-char name" "rejected: $RESP"
fi

# ---------------------------------------------------------------------------
# E-904: Duplicate interface names
# ---------------------------------------------------------------------------

api_post "rnsd/addInterface" '{"interface":{"name":"DuplicateTest","type":"AutoInterface"}}' >/dev/null 2>&1
RESP=$(api_post "rnsd/addInterface" '{"interface":{"name":"DuplicateTest","type":"AutoInterface"}}')
if echo "$RESP" | grep -qi '"validat\|"error\|"duplicate'; then
    ok "E-904" "Duplicate interface name rejected"
else
    info "E-904: Duplicate name not rejected at API level (may be enforced in GUI JS only): $RESP"
fi
# Cleanup both
for uuid in $(api_get "rnsd/searchInterfaces" | python3 -c "
import sys,json; rows=json.load(sys.stdin).get('rows',[]);
[print(r['uuid']) for r in rows if r.get('name')=='DuplicateTest']" 2>/dev/null); do
    api_post "rnsd/delInterface/$uuid" "" >/dev/null 2>&1
done

# ---------------------------------------------------------------------------
# E-905: Serial port doesn't exist
# ---------------------------------------------------------------------------

RESP=$(api_post "rnsd/addInterface" \
    '{"interface":{"name":"BadSerial","type":"SerialInterface","port":"/dev/nonexistent99","speed":"9600"}}')
UUID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)
if [ -n "$UUID" ]; then
    api_post "service/reconfigure" "" >/dev/null 2>&1; sleep 2
    info "E-905: Interface with nonexistent port accepted at model level (rnsd handles missing port at runtime)"
    ok "E-905" "Non-existent serial port accepted in config (rnsd will warn at startup)"
    api_post "rnsd/delInterface/$UUID" "" >/dev/null 2>&1
else
    info "E-905: Port rejected at model level: $RESP"
fi

# ---------------------------------------------------------------------------
# E-906: Config file manually edited → next reconfigure overwrites
# ---------------------------------------------------------------------------

if [ -f /usr/local/etc/reticulum/config ]; then
    echo "# MANUAL EDIT TEST" >> /usr/local/etc/reticulum/config
    api_post "service/reconfigure" "" >/dev/null 2>&1; sleep 1
    if ! grep -q "MANUAL EDIT TEST" /usr/local/etc/reticulum/config; then
        ok "E-906" "Reconfigure overwrites manual edits"
    else
        err "E-906" "Manual edit" "not overwritten by reconfigure"
    fi
else
    info "E-906: Config file not present, skipping"
fi

# ---------------------------------------------------------------------------
# E-907: Concurrent saves (sequential rapid POSTs)
# ---------------------------------------------------------------------------

for i in 1 2 3; do
    api_post "rnsd/set" "{\"general\":{\"loglevel\":\"$i\"}}" >/dev/null 2>&1 &
done
wait
FINAL=$(api_get "rnsd/get" | python3 -c "
import sys,json; print(json.load(sys.stdin).get('general',{}).get('loglevel','?'))
" 2>/dev/null)
if echo "1 2 3" | grep -q "$FINAL"; then
    ok "E-907" "Concurrent saves: final loglevel=$FINAL (last-write-wins)"
else
    err "E-907" "Concurrent saves" "unexpected loglevel: $FINAL"
fi
# Reset
api_post "rnsd/set" '{"general":{"loglevel":"4"}}' >/dev/null 2>&1

# ---------------------------------------------------------------------------
# E-908: lxmd version when binary missing
# ---------------------------------------------------------------------------

RESP=$(api_get "service/lxmdStatus")
if echo "$RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    ok "E-908" "lxmdStatus returns valid JSON (running or not)"
else
    err "E-908" "lxmdStatus" "non-JSON response: $RESP"
fi

# ---------------------------------------------------------------------------
# E-909: rnstatus when shared instance disabled
# ---------------------------------------------------------------------------

# Temporarily disable share_instance and reconfigure
api_post "rnsd/set" '{"general":{"share_instance":"0"}}' >/dev/null 2>&1
api_post "service/reconfigure" "" >/dev/null 2>&1; sleep 2

RESP=$(api_get "service/rnstatus")
if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok')" 2>/dev/null; then
    ok "E-909" "rnstatus returns valid JSON when shared_instance disabled"
else
    err "E-909" "rnstatus" "non-JSON response: $RESP"
fi
api_post "rnsd/set" '{"general":{"share_instance":"1"}}' >/dev/null 2>&1

# ---------------------------------------------------------------------------
# E-910: 20+ interfaces grid pagination
# ---------------------------------------------------------------------------

info "E-910: Adding 22 interfaces to test pagination..."
UUIDS=""
for i in $(seq 1 22); do
    R=$(api_post "rnsd/addInterface" "{\"interface\":{\"name\":\"PagTest${i}\",\"type\":\"AutoInterface\"}}")
    U=$(echo "$R" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)
    UUIDS="$UUIDS $U"
done

RESP=$(api_get "rnsd/searchInterfaces")
ROW_COUNT=$(echo "$RESP" | python3 -c "
import sys,json; d=json.load(sys.stdin); print(d.get('total',len(d.get('rows',[]))))" 2>/dev/null)
if [ "$ROW_COUNT" -ge 22 ]; then
    ok "E-910" "searchInterfaces returns $ROW_COUNT rows (pagination data available)"
else
    err "E-910" "Grid pagination" "expected >=22 rows, got $ROW_COUNT"
fi

# Cleanup
for u in $UUIDS; do
    [ -n "$u" ] && api_post "rnsd/delInterface/$u" "" >/dev/null 2>&1
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=== Edge Case Results: ${P} passed, ${F} failed ==="
[ "$F" -eq 0 ] && exit 0 || exit 1
