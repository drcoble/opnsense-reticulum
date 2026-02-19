#!/bin/sh
# update_upstream.sh — Update Reticulum and LXMF submodules to a new release
#
# Usage:
#   ./scripts/update_upstream.sh                   # list available tags
#   ./scripts/update_upstream.sh <rns-tag> <lxmf-tag>  # pin to specific tags
#   ./scripts/update_upstream.sh --latest          # pin to latest tag of each

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
RNS_SRC="${REPO_ROOT}/net/reticulum/src/usr/local/lib/rns-src"
LXMF_SRC="${REPO_ROOT}/net/reticulum/src/usr/local/lib/lxmf-src"
MAKEFILE="${REPO_ROOT}/net/reticulum/Makefile"

# Fetch latest tags from upstream
echo "==> Fetching latest tags from upstream..."
git -C "${RNS_SRC}" fetch --tags --quiet
git -C "${LXMF_SRC}" fetch --tags --quiet

if [ "$1" = "--latest" ]; then
    RNS_TAG=$(git -C "${RNS_SRC}" tag --sort=-version:refname | head -1)
    LXMF_TAG=$(git -C "${LXMF_SRC}" tag --sort=-version:refname | head -1)
elif [ $# -eq 2 ]; then
    RNS_TAG="$1"
    LXMF_TAG="$2"
else
    echo ""
    echo "Latest Reticulum (RNS) tags:"
    git -C "${RNS_SRC}" tag --sort=-version:refname | head -8 | sed 's/^/    /'
    echo ""
    echo "Latest LXMF tags:"
    git -C "${LXMF_SRC}" tag --sort=-version:refname | head -8 | sed 's/^/    /'
    echo ""
    echo "Current pinned versions:"
    grep -E '^RNS_VERSION|^LXMF_VERSION' "${MAKEFILE}" | sed 's/^/    /'
    echo ""
    echo "Usage:"
    echo "  $0 --latest             # pin to latest tag of each"
    echo "  $0 <rns-tag> <lxmf-tag> # pin to specific tags"
    exit 0
fi

CURRENT_RNS=$(grep '^RNS_VERSION' "${MAKEFILE}" | awk '{print $NF}')
CURRENT_LXMF=$(grep '^LXMF_VERSION' "${MAKEFILE}" | awk '{print $NF}')

echo ""
echo "==> Updating submodules:"
echo "    RNS:  ${CURRENT_RNS} -> ${RNS_TAG}"
echo "    LXMF: ${CURRENT_LXMF} -> ${LXMF_TAG}"
echo ""

# Checkout the requested tags
git -C "${RNS_SRC}" checkout "${RNS_TAG}" --quiet
git -C "${LXMF_SRC}" checkout "${LXMF_TAG}" --quiet

# Update version strings in Makefile
sed -i '' "s/^RNS_VERSION=.*/RNS_VERSION=\t\t${RNS_TAG}/" "${MAKEFILE}"
sed -i '' "s/^LXMF_VERSION=.*/LXMF_VERSION=\t\t${LXMF_TAG}/" "${MAKEFILE}"

# Bump PLUGIN_REVISION
CURRENT_REV=$(grep '^PLUGIN_REVISION=' "${MAKEFILE}" | awk -F= '{print $2}' | tr -d '[:space:]\t')
NEW_REV=$((CURRENT_REV + 1))
sed -i '' "s/^PLUGIN_REVISION=.*/PLUGIN_REVISION=\t${NEW_REV}/" "${MAKEFILE}"

echo "==> Updated Makefile:"
grep -E '^(PLUGIN_REVISION|RNS_VERSION|LXMF_VERSION)' "${MAKEFILE}" | sed 's/^/    /'

# Stage the changes
git add "${RNS_SRC}" "${LXMF_SRC}" "${MAKEFILE}"

echo ""
echo "==> Changes staged. Review with 'git diff --cached', then commit:"
echo "    git commit -m 'Update Reticulum to ${RNS_TAG}, LXMF to ${LXMF_TAG}'"
