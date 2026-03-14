#!/bin/sh
# run_all.sh — Top-level test runner for os-reticulum
#
# Runs all automated test suites and prints a final pass/fail summary.
#
# Usage:
#   sh tests/run_all.sh              # from the repo root
#   cd tests && sh run_all.sh        # from the tests/ directory
#
# Environment variables:
#   OPNSENSE_HOST   If set, also runs smoke_test.sh against that host.
#                   Example: OPNSENSE_HOST=https://192.168.1.1 sh tests/run_all.sh
#   OPNSENSE_USER   OPNsense admin username (default: admin)
#   OPNSENSE_PASS          OPNsense admin password (default: opnsense)
#   OPNSENSE_SSH_KEY_PATH  Path to SSH private key for connecting to OPNsense VM.
#
# Exit code: 0 if all executed suites pass, 1 if any suite fails.

# ---------------------------------------------------------------------------
# Resolve paths regardless of where the script is invoked from
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TESTS_DIR="${SCRIPT_DIR}"

# ---------------------------------------------------------------------------
# Colour helpers (degrade gracefully if the terminal does not support colour)
# ---------------------------------------------------------------------------

if [ -t 1 ]; then
    RED='\033[0;31m'
    GRN='\033[0;32m'
    YEL='\033[0;33m'
    BLD='\033[1m'
    RST='\033[0m'
else
    RED=''; GRN=''; YEL=''; BLD=''; RST=''
fi

SUITE_PASS=0
SUITE_FAIL=0
SUITE_SKIP=0

suite_ok()   { printf "${GRN}PASS${RST}  suite: %s\n" "$1"; SUITE_PASS=$((SUITE_PASS+1)); }
suite_fail() { printf "${RED}FAIL${RST}  suite: %s\n" "$1"; SUITE_FAIL=$((SUITE_FAIL+1)); }
suite_skip() { printf "${YEL}SKIP${RST}  suite: %s — %s\n" "$1" "$2"; SUITE_SKIP=$((SUITE_SKIP+1)); }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

run_pytest() {
    # run_pytest SUITE_LABEL PATH [extra pytest args...]
    LABEL="$1"; shift
    TARGET="$1"; shift
    printf "\n${BLD}--- pytest: %s ---${RST}\n" "$LABEL"
    if command -v pytest >/dev/null 2>&1; then
        pytest "$TARGET" "$@"
        if [ $? -eq 0 ]; then
            suite_ok "$LABEL"
        else
            suite_fail "$LABEL"
        fi
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m pytest "$TARGET" "$@"
        if [ $? -eq 0 ]; then
            suite_ok "$LABEL"
        else
            suite_fail "$LABEL"
        fi
    else
        suite_skip "$LABEL" "pytest not found (install with: pip install pytest jinja2)"
    fi
}

run_shell() {
    # run_shell SUITE_LABEL SCRIPT [args...]
    LABEL="$1"; shift
    SCRIPT="$1"; shift
    printf "\n${BLD}--- shell: %s ---${RST}\n" "$LABEL"
    if [ -f "$SCRIPT" ]; then
        sh "$SCRIPT" "$@"
        if [ $? -eq 0 ]; then
            suite_ok "$LABEL"
        else
            suite_fail "$LABEL"
        fi
    else
        suite_skip "$LABEL" "script not found: $SCRIPT"
    fi
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

echo ""
printf "${BLD}========================================${RST}\n"
printf "${BLD}  os-reticulum test suite${RST}\n"
printf "${BLD}========================================${RST}\n"
echo "Repo root : ${REPO_ROOT}"
echo "Tests dir : ${TESTS_DIR}"
if [ -n "$OPNSENSE_HOST" ]; then
    echo "Live host : ${OPNSENSE_HOST}"
else
    echo "Live host : (not set — smoke test will be skipped)"
fi
echo ""

# ---------------------------------------------------------------------------
# Suite 1: Model validation (M-201–M-209)
# ---------------------------------------------------------------------------

run_pytest "model validation (M-201–209)" \
    "${TESTS_DIR}/model" \
    -v

# ---------------------------------------------------------------------------
# Suite 2: Template output (T-101–T-112)
# ---------------------------------------------------------------------------

run_pytest "template output (T-101–112)" \
    "${TESTS_DIR}/template" \
    -v

# ---------------------------------------------------------------------------
# Suite 3: Security / injection (X-701–X-710)
# ---------------------------------------------------------------------------

run_pytest "config injection security (X-701–710)" \
    "${TESTS_DIR}/security" \
    -v

# ---------------------------------------------------------------------------
# Suite 4: Smoke test (S-401) — only if OPNSENSE_HOST is set
# ---------------------------------------------------------------------------

if [ -n "$OPNSENSE_HOST" ]; then
    run_shell "smoke test (S-401)" \
        "${TESTS_DIR}/service/smoke_test.sh"
else
    suite_skip "smoke test (S-401)" "set OPNSENSE_HOST to run against a live OPNsense instance"
fi

# ---------------------------------------------------------------------------
# Suite 5: API endpoint tests (A-301–A-309) — only if OPNSENSE_HOST is set
# ---------------------------------------------------------------------------

if [ -n "$OPNSENSE_HOST" ]; then
    run_shell "API endpoint tests (A-301–309)" \
        "${TESTS_DIR}/api/test_api_endpoints.sh" \
        "$OPNSENSE_HOST" \
        "${OPNSENSE_USER:-admin}" \
        "${OPNSENSE_PASS:-opnsense}"
else
    suite_skip "API endpoint tests (A-301–309)" "set OPNSENSE_HOST to run against a live OPNsense instance"
fi

# ---------------------------------------------------------------------------
# Suite 6: Service lifecycle tests (S-402–S-406) — only if OPNSENSE_HOST is set and SSH access available
# ---------------------------------------------------------------------------

if [ -n "$OPNSENSE_HOST" ] && [ -n "$OPNSENSE_SSH_KEY_PATH" ]; then
    run_shell "service lifecycle tests (S-402–406)" \
        "${TESTS_DIR}/service/test_service_lifecycle.sh"
else
    suite_skip "service lifecycle tests (S-402–406)" "set OPNSENSE_HOST and OPNSENSE_SSH_KEY_PATH to run"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

SUITE_TOTAL=$((SUITE_PASS + SUITE_FAIL + SUITE_SKIP))

echo ""
printf "${BLD}========================================${RST}\n"
printf "${BLD}  Final summary${RST}\n"
printf "${BLD}========================================${RST}\n"
printf "  Suites run   : %d / %d\n" "$((SUITE_PASS + SUITE_FAIL))" "$SUITE_TOTAL"
printf "  ${GRN}Passed${RST}       : %d\n" "$SUITE_PASS"
printf "  ${RED}Failed${RST}       : %d\n" "$SUITE_FAIL"
printf "  ${YEL}Skipped${RST}      : %d\n" "$SUITE_SKIP"
echo ""

if [ "$SUITE_FAIL" -gt 0 ]; then
    printf "${RED}RESULT: FAIL — %d suite(s) did not pass${RST}\n\n" "$SUITE_FAIL"
    exit 1
else
    printf "${GRN}RESULT: PASS — all executed suites passed${RST}\n\n"
    exit 0
fi
