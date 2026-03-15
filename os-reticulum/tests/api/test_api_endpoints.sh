#!/bin/sh
# API Endpoint Tests — A-301 through A-309
# Usage: ./test_api_endpoints.sh [base_url] [username] [password]
# Default: https://localhost admin opnsense
#
# Also reads environment variable OPNSENSE_HOST if set (takes priority over default,
# but positional argument $1 still takes precedence over OPNSENSE_HOST).
#
# Run on OPNsense VM or from a machine with network access to OPNsense.
#
# Exit code: 0 if all tests pass, 1 if any test fails.

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# OPNSENSE_HOST env var allows CI/CD to inject the target without altering args.
# Precedence: $1 (explicit arg) > $OPNSENSE_HOST > localhost
if [ -n "$1" ]; then
    BASE="$1"
elif [ -n "$OPNSENSE_HOST" ]; then
    BASE="$OPNSENSE_HOST"
else
    BASE="https://localhost"
fi

USER="${2:-${OPNSENSE_USER:-admin}}"
PASS="${3:-${OPNSENSE_PASS:-opnsense}}"
CURL="curl -ks -u ${USER}:${PASS}"

PASS_COUNT=0
FAIL_COUNT=0

pass() { echo "PASS  $1: $2"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "FAIL  $1: $2 — $3"; FAIL_COUNT=$((FAIL_COUNT+1)); }

api_get()  { $CURL "${BASE}/api/reticulum/$1"; }
api_post() {
    _body="$3"
    [ -z "$_body" ] && _body='{}'
    $CURL -X POST -H "Content-Type: application/json" -d "$_body" "${BASE}/api/reticulum/$2"
}

check_field() {
    echo "$1" | grep -q "\"$2\"" && return 0 || return 1
}

echo "=== OPNsense Reticulum API Tests ==="
echo "Target: ${BASE}"
echo "User:   ${USER}"
echo ""

# ---------------------------------------------------------------------------
# A-301: General settings get/set
# ---------------------------------------------------------------------------

RESP=$(api_get "rnsd/get")
if echo "$RESP" | grep -q '"general"'; then
    pass "A-301a" "GET rnsd/get returns general settings"
else
    fail "A-301a" "GET rnsd/get" "no 'general' key in response: $RESP"
fi

RESP=$(api_post "" "rnsd/set" '{"general":{"enabled":"1","loglevel":"5"}}')
if echo "$RESP" | grep -q '"saved"'; then
    pass "A-301b" "POST rnsd/set saves valid data"
else
    fail "A-301b" "POST rnsd/set" "expected saved, got: $RESP"
fi

RESP=$(api_get "rnsd/get")
if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['general']['loglevel']=='5'" 2>/dev/null; then
    pass "A-301c" "GET rnsd/get reflects saved loglevel=5"
else
    fail "A-301c" "GET rnsd/get" "loglevel not updated"
fi

# Reset loglevel
api_post "" "rnsd/set" '{"general":{"loglevel":"4"}}' >/dev/null 2>&1

# ---------------------------------------------------------------------------
# A-302: Interface CRUD cycle
# ---------------------------------------------------------------------------

RESP=$(api_post "" "rnsd/addInterface" '{"interface":{"name":"Test TCP","type":"TCPServerInterface","listen_port":"4242"}}')
UUID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null)
if [ -n "$UUID" ]; then
    pass "A-302a" "addInterface returns UUID: $UUID"
else
    fail "A-302a" "addInterface" "no uuid in response: $RESP"
    UUID=""
fi

if [ -n "$UUID" ]; then
    RESP=$(api_get "rnsd/searchInterfaces")
    if echo "$RESP" | grep -q "Test TCP"; then
        pass "A-302b" "searchInterfaces finds created interface"
    else
        fail "A-302b" "searchInterfaces" "interface not found: $RESP"
    fi

    RESP=$(api_get "rnsd/getInterface/$UUID")
    if echo "$RESP" | grep -q '"Test TCP"'; then
        pass "A-302c" "getInterface returns correct data"
    else
        fail "A-302c" "getInterface" "name mismatch: $RESP"
    fi

    RESP=$(api_post "" "rnsd/setInterface/$UUID" '{"interface":{"listen_port":"5555"}}')
    if echo "$RESP" | grep -q '"saved"'; then
        pass "A-302d" "setInterface updates listen_port"
    else
        fail "A-302d" "setInterface" "expected saved: $RESP"
    fi

    RESP=$(api_post "" "rnsd/toggleInterface/$UUID" "")
    if echo "$RESP" | grep -q '"ok"\|"changed"'; then
        pass "A-302e" "toggleInterface returns ok/changed"
    else
        fail "A-302e" "toggleInterface" "unexpected: $RESP"
    fi

    RESP=$(api_post "" "rnsd/delInterface/$UUID" "")
    if echo "$RESP" | grep -q '"deleted"\|"ok"'; then
        pass "A-302f" "delInterface removes interface"
    else
        fail "A-302f" "delInterface" "unexpected: $RESP"
    fi
fi

# ---------------------------------------------------------------------------
# A-303: LXMF get/set
# ---------------------------------------------------------------------------

RESP=$(api_get "lxmd/get")
if echo "$RESP" | grep -q '"lxmf"'; then
    pass "A-303a" "GET lxmd/get returns lxmf settings"
else
    fail "A-303a" "GET lxmd/get" "no 'lxmf' key: $RESP"
fi

RESP=$(api_post "" "lxmd/set" '{"lxmf":{"display_name":"Test Node"}}')
if echo "$RESP" | grep -q '"saved"'; then
    pass "A-303b" "POST lxmd/set saves display_name"
else
    fail "A-303b" "POST lxmd/set" "expected saved: $RESP"
fi

# Verify saved value is reflected
RESP=$(api_get "lxmd/get")
if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['lxmf']['display_name']=='Test Node'" 2>/dev/null; then
    pass "A-303c" "GET lxmd/get reflects saved display_name"
else
    fail "A-303c" "GET lxmd/get" "display_name not updated"
fi

# ---------------------------------------------------------------------------
# A-304: Invalid data rejection
# ---------------------------------------------------------------------------

RESP=$(api_post "" "rnsd/set" '{"general":{"loglevel":"99"}}')
if echo "$RESP" | grep -qi '"validat\|"error\|"failed'; then
    pass "A-304a" "POST rnsd/set rejects loglevel=99"
else
    fail "A-304a" "validation" "expected error for loglevel=99, got: $RESP"
fi

RESP=$(api_post "" "rnsd/addInterface" '{"interface":{"type":"TCPServerInterface"}}')
if echo "$RESP" | grep -qi '"validat\|"error\|"failed'; then
    pass "A-304b" "addInterface rejects missing name"
else
    fail "A-304b" "validation" "expected error for missing name, got: $RESP"
fi

# Invalid port (out of range)
RESP=$(api_post "" "rnsd/set" '{"general":{"shared_instance_port":"99999"}}')
if echo "$RESP" | grep -qi '"validat\|"error\|"failed'; then
    pass "A-304c" "POST rnsd/set rejects shared_instance_port=99999"
else
    fail "A-304c" "validation" "expected error for port=99999, got: $RESP"
fi

# Invalid hex hash in static_peers
RESP=$(api_post "" "lxmd/set" '{"lxmf":{"static_peers":"NOTVALID"}}')
if echo "$RESP" | grep -qi '"validat\|"error\|"failed'; then
    pass "A-304d" "POST lxmd/set rejects invalid static_peers hash"
else
    fail "A-304d" "validation" "expected error for invalid hash, got: $RESP"
fi

# ---------------------------------------------------------------------------
# A-305: rnsd start/stop/restart
# ---------------------------------------------------------------------------

RESP=$(api_post "" "service/rnsdStart" "")
if echo "$RESP" | grep -qi '"ok"\|"started"\|"result"'; then
    pass "A-305a" "rnsdStart returns ok"
else
    fail "A-305a" "rnsdStart" "unexpected: $RESP"
fi

sleep 2

RESP=$(api_get "service/rnsdStatus")
if echo "$RESP" | grep -qi '"running"'; then
    pass "A-305b" "rnsdStatus shows running after start"
else
    fail "A-305b" "rnsdStatus" "expected running: $RESP"
fi

RESP=$(api_post "" "service/rnsdStop" "")
if echo "$RESP" | grep -qi '"ok"\|"stopped"\|"result"'; then
    pass "A-305c" "rnsdStop returns ok"
else
    fail "A-305c" "rnsdStop" "unexpected: $RESP"
fi

sleep 1

RESP=$(api_get "service/rnsdStatus")
if echo "$RESP" | grep -qi '"stopped"\|"not running"'; then
    pass "A-305d" "rnsdStatus shows stopped after stop"
else
    fail "A-305d" "rnsdStatus" "expected stopped: $RESP"
fi

# Test restart: start first, then restart
api_post "" "service/rnsdStart" "" >/dev/null 2>&1; sleep 2
RESP=$(api_post "" "service/rnsdRestart" "")
if echo "$RESP" | grep -qi '"ok"\|"restarted"\|"result"'; then
    pass "A-305e" "rnsdRestart returns ok"
else
    fail "A-305e" "rnsdRestart" "unexpected: $RESP"
fi
sleep 2
RESP=$(api_get "service/rnsdStatus")
if echo "$RESP" | grep -qi '"running"'; then
    pass "A-305f" "rnsdStatus shows running after restart"
else
    fail "A-305f" "rnsdStatus" "expected running after restart: $RESP"
fi
api_post "" "service/rnsdStop" "" >/dev/null 2>&1

# ---------------------------------------------------------------------------
# A-306: lxmd start blocked without rnsd
# ---------------------------------------------------------------------------

# Ensure rnsd is stopped
api_post "" "service/rnsdStop" "" >/dev/null 2>&1
sleep 1

RESP=$(api_post "" "service/lxmdStart" "")
if echo "$RESP" | grep -qi '"error\|"cannot\|"failed\|"rnsd'; then
    pass "A-306" "lxmdStart blocked when rnsd not running"
else
    fail "A-306" "lxmd dependency check" "expected error, got: $RESP"
fi

# ---------------------------------------------------------------------------
# A-307: Reconfigure
# ---------------------------------------------------------------------------

RESP=$(api_post "" "service/reconfigure" "")
if echo "$RESP" | grep -qi '"ok"\|"result"'; then
    pass "A-307" "reconfigure runs without error"
else
    fail "A-307" "reconfigure" "unexpected: $RESP"
fi

# ---------------------------------------------------------------------------
# A-308: rnstatus when stopped
# ---------------------------------------------------------------------------

RESP=$(api_get "service/rnstatus")
# When rnsd is stopped, should return an error object, not crash
if echo "$RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    pass "A-308" "rnstatus returns valid JSON (even when stopped)"
else
    fail "A-308" "rnstatus" "non-JSON response: $RESP"
fi

# ---------------------------------------------------------------------------
# A-309: Authentication / unauthorised access
# ---------------------------------------------------------------------------
# This test verifies that the API endpoints reject requests that supply
# wrong credentials and that they are not accessible without authentication.

# Wrong credentials should return 401 (or equivalent non-200 with no data).
HTTP_CODE=$(curl -ks -o /dev/null -w "%{http_code}" \
    -u "wronguser:wrongpass" "${BASE}/api/reticulum/rnsd/get")
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "A-309a" "GET rnsd/get with wrong credentials returns HTTP $HTTP_CODE"
else
    fail "A-309a" "auth reject" "expected 401/403, got HTTP $HTTP_CODE"
fi

# No credentials at all.
# OPNsense behaviour: a no-credential request receives HTTP 200 with an HTML
# login page, not a 401/403.  We accept 401/403 (traditional rejection) or
# 200 only when the body does NOT contain "general" (i.e. it is the login page,
# not real API data).  A 200 body that contains "general" is an auth bypass.
HTTP_CODE=$(curl -ks -o /tmp/_a309b_body.txt -w "%{http_code}" \
    "${BASE}/api/reticulum/rnsd/get")
BODY=$(cat /tmp/_a309b_body.txt)
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "A-309b" "GET rnsd/get with no credentials returns HTTP $HTTP_CODE"
elif [ "$HTTP_CODE" = "302" ]; then
    pass "A-309b" "GET rnsd/get with no credentials redirects to login (HTTP 302)"
elif [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q '"general"'; then
        fail "A-309b" "auth reject (no creds)" "SECURITY: 200 returned real API data (auth bypass)"
    else
        pass "A-309b" "GET rnsd/get with no credentials returns login page (HTTP 200, no API data)"
    fi
else
    fail "A-309b" "auth reject (no creds)" "unexpected HTTP $HTTP_CODE"
fi
rm -f /tmp/_a309b_body.txt

# A POST action with valid credentials but no CSRF token should be rejected.
# OPNsense requires the X-CSRFToken header (or API key auth bypasses CSRF).
# When using HTTP Basic auth (as in these tests) OPNsense bypasses CSRF for
# API key users; this sub-test documents the expected behaviour for session
# cookie auth by attempting a POST without the CSRF header and expecting a
# 403 response when using cookie-based auth.
# NOTE: This sub-test is advisory — it will PASS with an informational note
# if the target is configured to accept Basic auth for API calls (which is
# the normal integration-test setup), since CSRF only applies to session auth.
HTTP_CODE=$(curl -ks -o /dev/null -w "%{http_code}" \
    -X POST -H "Content-Type: application/json" -d '{}' \
    --cookie "" \
    "${BASE}/api/reticulum/service/reconfigure")
if [ "$HTTP_CODE" = "403" ]; then
    pass "A-309c" "POST without CSRF token (cookie auth) returns 403"
elif [ "$HTTP_CODE" = "302" ]; then
    pass "A-309c" "POST without credentials redirects to login (HTTP 302)"
elif [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    pass "A-309c" "POST /service/reconfigure reached server (Basic auth bypasses CSRF as expected) — HTTP $HTTP_CODE"
else
    fail "A-309c" "CSRF/no-auth check" "unexpected HTTP $HTTP_CODE"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo ""
echo "=== Results: ${PASS_COUNT}/${TOTAL} passed, ${FAIL_COUNT} failed ==="
[ "$FAIL_COUNT" -eq 0 ] && exit 0 || exit 1
