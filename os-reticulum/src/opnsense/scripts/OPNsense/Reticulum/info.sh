#!/bin/sh

VENV="/usr/local/reticulum-venv"
PKG_VERSIONS="/var/db/reticulum/.pkg-versions"

# Read versions (values are git tags or commit hashes recorded at install time)
RNS_VER="unknown"
LXMF_VER="unknown"
if [ -f "${PKG_VERSIONS}" ]; then
    RNS_VER=$(grep "^rns=" "${PKG_VERSIONS}" | cut -d= -f2)
    LXMF_VER=$(grep "^lxmf=" "${PKG_VERSIONS}" | cut -d= -f2)
fi

# Get node identity from rnstatus (if running)
NODE_ID=""
if RNSTATUS=$(timeout 5 "${VENV}/bin/rnstatus" --config /usr/local/etc/reticulum --json 2>/dev/null) && [ -n "${RNSTATUS}" ]; then
    NODE_ID=$(echo "${RNSTATUS}" | "${VENV}/bin/python3.11" -c "import sys,json; d=json.load(sys.stdin); print(d.get('identity',''))" 2>/dev/null)
fi

printf '{"rns_version":"%s","lxmf_version":"%s","node_identity":"%s"}\n' "${RNS_VER}" "${LXMF_VER}" "${NODE_ID}"
