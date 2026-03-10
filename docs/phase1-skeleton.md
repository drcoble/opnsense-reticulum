# Phase 1 — Plugin Skeleton

## Overview
Create the foundational plugin infrastructure: packaging, service scripts, configd actions, navigation, permissions, and log rotation.

---

## 1. Directory Structure

```
os-reticulum/
├── Makefile
├── pkg-install
├── pkg-deinstall
├── pkg-plist
├── src/
│   └── opnsense/
│       ├── mvc/app/
│       │   ├── controllers/OPNsense/Reticulum/
│       │   │   └── (Phase 4)
│       │   ├── models/OPNsense/Reticulum/
│       │   │   ├── ACL/ACL.xml
│       │   │   └── Menu/Menu.xml
│       │   └── views/OPNsense/Reticulum/
│       │       └── (Phase 5)
│       ├── scripts/OPNsense/Reticulum/
│       │   └── reconfigure.sh
│       ├── service/
│       │   ├── conf/actions.d/
│       │   │   └── actions_reticulum.conf
│       │   └── templates/OPNsense/Reticulum/
│       │       └── (Phase 3)
│       └── www/js/widgets/
│           └── (Phase 6)
├── src/etc/
│   ├── rc.d/
│   │   ├── rnsd
│   │   └── lxmd
│   ├── rc.syshook.d/start/
│   │   └── 50-reticulum
│   └── newsyslog.conf.d/
│       └── reticulum.conf
```

**Runtime source directory** (created at install time by `pkg-install`):

```
/usr/local/reticulum-src/               # created at install time
├── reticulum/   # git clone of markqvist/Reticulum
└── lxmf/        # git clone of markqvist/LXMF
```

---

## 2. Makefile

**Path:** `os-reticulum/Makefile`

```makefile
PLUGIN_NAME=        reticulum
PLUGIN_VERSION=     1.0
PLUGIN_REVISION=    0
PLUGIN_COMMENT=     Reticulum Network Stack and LXMF Propagation Node
PLUGIN_MAINTAINER=  your-email@example.com
PLUGIN_WWW=         https://reticulum.network
PLUGIN_DEPENDS=     python311 py311-cryptography py311-setuptools py311-wheel git

.include "../../Mk/plugins.mk"
```

**Notes:**
- `PLUGIN_NAME` becomes `os-reticulum` when packaged (OPNsense prepends `os-`)
- `PLUGIN_DEPENDS` lists FreeBSD pkg dependencies installed automatically
- `py311-pip` is omitted — it is bundled with the `python311` package
- `git` is required to clone upstream source repos for rns and lxmf
- `py311-setuptools` and `py311-wheel` are required to build Python packages from source
- The `.include` references OPNsense's standard plugin build system
- Python version (3.11) must match the target OPNsense release — verify before build

---

## 3. pkg-install Script

**Path:** `os-reticulum/pkg-install`

**Purpose:** Runs after package installation. Validates build dependencies, creates user, virtualenv, directories, and builds rns/lxmf from source.

```sh
#!/bin/sh

set -e

VENV_PATH="/usr/local/reticulum-venv"
SVC_USER="reticulum"
SVC_HOME="/var/db/reticulum"
SRC_BASE="/usr/local/reticulum-src"

RNS_REPO="https://github.com/markqvist/Reticulum"
LXMF_REPO="https://github.com/markqvist/LXMF"
RNS_SRC="${SRC_BASE}/reticulum"
LXMF_SRC="${SRC_BASE}/lxmf"

# --- Dependency check (must pass before any work) ---

check_dep() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[reticulum] ERROR: $1 not found. $2" >&2
        exit 1
    fi
}

check_pkg() {
    _pkg="$1"
    if ! pkg info -e "${_pkg}" 2>/dev/null; then
        echo "[reticulum] ERROR: package ${_pkg} is not installed. Install with: pkg install ${_pkg}" >&2
        exit 1
    fi
}

check_dep python3.11  "Install with: pkg install python311"
check_dep git         "Install with: pkg install git"
check_dep gcc         "gcc is expected in FreeBSD base. Verify base system integrity."
check_pkg py311-setuptools

# --- Create service user if not exists ---

if ! pw usershow ${SVC_USER} >/dev/null 2>&1; then
    pw useradd ${SVC_USER} \
        -d ${SVC_HOME} \
        -s /usr/sbin/nologin \
        -c "Reticulum Network Stack" \
        -m
fi

# Add user to dialer group (serial/USB device access)
pw groupmod dialer -m ${SVC_USER} 2>/dev/null || true

# --- Create directories ---

mkdir -p /usr/local/etc/reticulum
mkdir -p /usr/local/etc/lxmf
mkdir -p ${SVC_HOME}
mkdir -p /var/db/lxmf
mkdir -p /var/log/reticulum
mkdir -p ${SRC_BASE}

# Set ownership and permissions
chown -R ${SVC_USER}:${SVC_USER} /usr/local/etc/reticulum
chown -R ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf
chown -R ${SVC_USER}:${SVC_USER} ${SVC_HOME}
chown -R ${SVC_USER}:${SVC_USER} /var/db/lxmf
chown -R ${SVC_USER}:${SVC_USER} /var/log/reticulum

chmod 700 /usr/local/etc/reticulum
chmod 700 /usr/local/etc/lxmf
chmod 700 ${SVC_HOME}
chmod 700 /var/db/lxmf
chmod 750 /var/log/reticulum

# --- Create or update virtualenv ---

if [ ! -d "${VENV_PATH}" ]; then
    python3.11 -m venv ${VENV_PATH}
fi

# --- Clone or update source repos ---

fetch_source() {
    _repo_url="$1"
    _dest_dir="$2"
    _name="$3"

    if [ -d "${_dest_dir}/.git" ]; then
        echo "Updating ${_name} source..."
        if ! git -C "${_dest_dir}" pull; then
            echo "[reticulum] ERROR: git pull failed for ${_name}" >&2
            exit 1
        fi
    else
        echo "Cloning ${_name} source..."
        rm -rf "${_dest_dir}"
        if ! git clone "${_repo_url}" "${_dest_dir}"; then
            echo "[reticulum] ERROR: git clone failed for ${_name}" >&2
            exit 1
        fi
    fi
}

fetch_source "${RNS_REPO}" "${RNS_SRC}" "Reticulum"
fetch_source "${LXMF_REPO}" "${LXMF_SRC}" "LXMF"

# --- Build and install from source into venv ---

install_from_source() {
    _src_dir="$1"
    _name="$2"

    echo "Installing ${_name} from source..."
    if ! (cd "${_src_dir}" && ${VENV_PATH}/bin/pip install --upgrade . 2>&1); then
        echo "[reticulum] ERROR: pip install failed for ${_name}" >&2
        exit 1
    fi
}

install_from_source "${RNS_SRC}" "Reticulum (rns)"
install_from_source "${LXMF_SRC}" "LXMF"

# --- Clean pip cache ---

${VENV_PATH}/bin/pip cache purge 2>/dev/null || true

# --- Record installed versions (git describe) ---

RNS_VER=$(git -C "${RNS_SRC}" describe --tags --always 2>/dev/null)
LXMF_VER=$(git -C "${LXMF_SRC}" describe --tags --always 2>/dev/null)

printf "rns=%s\n" "${RNS_VER:-unknown}" > ${SVC_HOME}/.pkg-versions
printf "lxmf=%s\n" "${LXMF_VER:-unknown}" >> ${SVC_HOME}/.pkg-versions
chown ${SVC_USER}:${SVC_USER} ${SVC_HOME}/.pkg-versions

echo "Reticulum installed: rns=${RNS_VER:-unknown}, lxmf=${LXMF_VER:-unknown}"

exit 0
```

**Key considerations:**
- **Source vs pip:** Building from source ensures access to the latest fixes from upstream. The git short hash or tag in `.pkg-versions` provides exact traceability to the commit running on the node.
- **Idempotency pattern:** Safe on both fresh install and upgrade. Dep checks run first before any filesystem changes. `fetch_source` uses `git pull` on existing repos and `git clone` on new ones, with a defensive `rm -rf` before clone to handle corrupt partial state.
- **Build isolation via venv:** All Python packages install into `/usr/local/reticulum-venv/`, isolated from OPNsense's system Python. Prevents version conflicts with the firewall's own dependencies.
- **Error handling:** `set -e` plus explicit `if ! ...; then exit 1` guards on each critical operation. A build failure aborts with a non-zero exit code and a descriptive error to stderr.

---

## 3b. Dependency Verification

**Path:** `os-reticulum/pkg-install` (integrated at the top, before user creation)

**Purpose:** Fail fast with actionable error messages if required build or runtime dependencies are missing. Runs before any filesystem changes so a failed install leaves no partial state.

### Helper functions

```sh
check_dep() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[reticulum] ERROR: $1 not found. $2" >&2
        exit 1
    fi
}

check_pkg() {
    _pkg="$1"
    if ! pkg info -e "${_pkg}" 2>/dev/null; then
        echo "[reticulum] ERROR: package ${_pkg} is not installed. Install with: pkg install ${_pkg}" >&2
        exit 1
    fi
}
```

### Dependencies checked

| Dependency | Check method | Why required |
|---|---|---|
| `python3.11` | `command -v` | Runtime interpreter and virtualenv creation |
| `git` | `command -v` | Cloning upstream rns/lxmf source repos |
| `gcc` | `command -v` | FreeBSD base compiler; required for C extensions in rns dependencies |
| `py311-setuptools` | `pkg info -e` | No unique binary; required for `setup.py`-based source builds |

### Example error output

```
[reticulum] ERROR: git not found. Install with: pkg install git
[reticulum] ERROR: package py311-setuptools is not installed. Install with: pkg install py311-setuptools
```

**Key considerations:**
- `command -v` is POSIX and works in all `/bin/sh` implementations on FreeBSD 13/14
- `pkg info -e` returns 0 if installed, non-zero otherwise — no output parsing needed
- All errors go to stderr with consistent `[reticulum] ERROR:` prefix for grep-ability
- Script exits on the first missing dependency — no partial setup occurs

---

## 4. pkg-deinstall Script

**Path:** `os-reticulum/pkg-deinstall`

```sh
#!/bin/sh

# Stop services
service lxmd stop 2>/dev/null || true
service rnsd stop 2>/dev/null || true

# Disable services
sysrc -f /etc/rc.conf.d/rnsd rnsd_enable="NO" 2>/dev/null || true
sysrc -f /etc/rc.conf.d/lxmd lxmd_enable="NO" 2>/dev/null || true

# Remove generated config files (preserve user data dirs)
rm -f /usr/local/etc/reticulum/config
rm -f /usr/local/etc/lxmf/config
rm -f /usr/local/etc/lxmf/allowed
rm -f /usr/local/etc/lxmf/ignored
rm -f /etc/rc.conf.d/rnsd
rm -f /etc/rc.conf.d/lxmd

# Remove cloned source directories. These are build artifacts created during
# pkg-install to compile rns/lxmf into the virtualenv. They contain no user
# data and can be safely recreated by reinstalling the plugin.
rm -rf /usr/local/reticulum-src

# NOTE: Preserving the following for user data safety:
#   /usr/local/etc/reticulum/  (identity keys, path tables)
#   /usr/local/etc/lxmf/       (identity, stored messages)
#   /var/db/reticulum/          (runtime data)
#   /var/db/lxmf/               (message storage)
#   /var/log/reticulum/         (logs)
#   /usr/local/reticulum-venv/  (virtualenv)
# Administrator may remove these manually if desired.

exit 0
```

**Key considerations:**
- Services stopped before removal
- Generated configs removed, but identity keys and message storage preserved
- Cloned source directories (`/usr/local/reticulum-src/`) removed as build artifacts — they contain no user data
- Virtualenv preserved (low risk, can be removed manually)

---

## 5. rc.d Service Scripts

### 5a. rnsd rc.d script

**Path:** `src/etc/rc.d/rnsd` → installs to `/usr/local/etc/rc.d/rnsd`

```sh
#!/bin/sh

# PROVIDE: rnsd
# REQUIRE: NETWORKING
# KEYWORD: shutdown

. /etc/rc.subr

name="rnsd"
rcvar="rnsd_enable"

load_rc_config $name

: ${rnsd_enable:="NO"}
: ${rnsd_user:="reticulum"}
: ${rnsd_config:="/usr/local/etc/reticulum"}

pidfile="/var/run/${name}.pid"
command="/usr/local/reticulum-venv/bin/rnsd"
command_args="--service -s --config ${rnsd_config}"

# Use daemon(8) to background the process and create pidfile
command_interpreter="/usr/local/reticulum-venv/bin/python3.11"
rnsd_flags=""

start_precmd="${name}_prestart"
stop_postcmd="${name}_poststop"

rnsd_prestart()
{
    # Ensure config directory exists and is owned correctly
    if [ ! -d "${rnsd_config}" ]; then
        mkdir -p "${rnsd_config}"
        chown ${rnsd_user}:${rnsd_user} "${rnsd_config}"
    fi

    # Ensure log directory exists
    if [ ! -d "/var/log/reticulum" ]; then
        mkdir -p /var/log/reticulum
        chown ${rnsd_user}:${rnsd_user} /var/log/reticulum
    fi
}

rnsd_poststop()
{
    rm -f ${pidfile}
}

run_rc_command "$1"
```

**Notes:**
- `PROVIDE: rnsd` — makes this available as a dependency
- `REQUIRE: NETWORKING` — waits for network stack
- `command_interpreter` helps `rc.subr` find the process (Python scripts)
- The `--service` flag tells rnsd to run in foreground (daemon(8) handles backgrounding)
- `-s` enables shared instance mode

### 5b. lxmd rc.d script

**Path:** `src/etc/rc.d/lxmd` → installs to `/usr/local/etc/rc.d/lxmd`

```sh
#!/bin/sh

# PROVIDE: lxmd
# REQUIRE: rnsd
# KEYWORD: shutdown

. /etc/rc.subr

name="lxmd"
rcvar="lxmd_enable"

load_rc_config $name

: ${lxmd_enable:="NO"}
: ${lxmd_user:="reticulum"}
: ${lxmd_config:="/usr/local/etc/lxmf"}
: ${lxmd_rnsconfig:="/usr/local/etc/reticulum"}
: ${lxmd_propagation:="YES"}

pidfile="/var/run/${name}.pid"
command="/usr/local/reticulum-venv/bin/lxmd"

# Build command args
lxmd_flags=""
if checkyesno lxmd_propagation; then
    lxmd_flags="-p"
fi
command_args="--service -s ${lxmd_flags} --config ${lxmd_config} --rnsconfig ${lxmd_rnsconfig}"

command_interpreter="/usr/local/reticulum-venv/bin/python3.11"

start_precmd="${name}_prestart"
stop_postcmd="${name}_poststop"

lxmd_prestart()
{
    # Check that rnsd is running
    if ! service rnsd status >/dev/null 2>&1; then
        echo "rnsd is not running. lxmd requires rnsd to be started first."
        return 1
    fi

    # Ensure config directory exists
    if [ ! -d "${lxmd_config}" ]; then
        mkdir -p "${lxmd_config}"
        chown ${lxmd_user}:${lxmd_user} "${lxmd_config}"
    fi
}

lxmd_poststop()
{
    rm -f ${pidfile}
}

run_rc_command "$1"
```

**Notes:**
- `REQUIRE: rnsd` — ensures rnsd starts first at boot
- `start_precmd` checks rnsd is actually running before allowing lxmd to start
- `-p` flag enables propagation node mode (controlled by rc.conf.d variable)

---

## 6. configd Actions File

**Path:** `src/opnsense/service/conf/actions.d/actions_reticulum.conf`

```ini
[start.rnsd]
command:service rnsd start
type:script
message:Starting Reticulum rnsd

[stop.rnsd]
command:service rnsd stop
type:script
message:Stopping Reticulum rnsd

[restart.rnsd]
command:service rnsd restart
type:script
message:Restarting Reticulum rnsd

[status.rnsd]
command:/usr/local/opnsense/scripts/OPNsense/Reticulum/rnsd_status.sh
type:script_output
message:Checking rnsd status

[start.lxmd]
command:service lxmd start
type:script
message:Starting LXMF lxmd

[stop.lxmd]
command:service lxmd stop
type:script
message:Stopping LXMF lxmd

[restart.lxmd]
command:service lxmd restart
type:script
message:Restarting LXMF lxmd

[status.lxmd]
command:/usr/local/opnsense/scripts/OPNsense/Reticulum/lxmd_status.sh
type:script_output
message:Checking lxmd status

[reconfigure]
command:/usr/local/opnsense/scripts/OPNsense/Reticulum/reconfigure.sh
type:script
message:Reconfiguring Reticulum services

[rnstatus]
command:/usr/local/opnsense/scripts/OPNsense/Reticulum/rnstatus.sh
type:script_output
message:Fetching Reticulum network status

[info]
command:/usr/local/opnsense/scripts/OPNsense/Reticulum/info.sh
type:script_output
message:Fetching Reticulum version info

[logs.rnsd]
command:tail -n %s /var/log/reticulum/rnsd.log
type:script_output
message:Fetching rnsd logs
parameters:%s

[logs.lxmd]
command:tail -n %s /var/log/reticulum/lxmd.log
type:script_output
message:Fetching lxmd logs
parameters:%s
```

**Configd action naming:**
- Actions are invoked via `configctl reticulum <action>` (e.g., `configctl reticulum start.rnsd`)
- `type:script` — fire and forget, returns exit code
- `type:script_output` — captures stdout and returns it to the caller

---

## 7. Helper Scripts

### 7a. reconfigure.sh

**Path:** `src/opnsense/scripts/OPNsense/Reticulum/reconfigure.sh`

```sh
#!/bin/sh

SVC_USER="reticulum"

# Regenerate config files from templates
configctl template reload OPNsense/Reticulum

# Fix ownership of generated config files (template reload runs as root)
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/reticulum/config 2>/dev/null || true
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf/config 2>/dev/null || true
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf/allowed 2>/dev/null || true
chown ${SVC_USER}:${SVC_USER} /usr/local/etc/lxmf/ignored 2>/dev/null || true

# Conditionally restart rnsd if enabled and running
if service rnsd enabled 2>/dev/null; then
    if service rnsd status >/dev/null 2>&1; then
        service rnsd restart
    fi
fi

# Conditionally restart lxmd if enabled and running
if service lxmd enabled 2>/dev/null; then
    if service lxmd status >/dev/null 2>&1; then
        service lxmd restart
    fi
fi

exit 0
```

### 7b. rnsd_status.sh

**Path:** `src/opnsense/scripts/OPNsense/Reticulum/rnsd_status.sh`

```sh
#!/bin/sh

if service rnsd status >/dev/null 2>&1; then
    echo '{"status":"running"}'
else
    echo '{"status":"stopped"}'
fi
```

### 7c. lxmd_status.sh

**Path:** `src/opnsense/scripts/OPNsense/Reticulum/lxmd_status.sh`

```sh
#!/bin/sh

if service lxmd status >/dev/null 2>&1; then
    echo '{"status":"running"}'
else
    echo '{"status":"stopped"}'
fi
```

### 7d. rnstatus.sh

**Path:** `src/opnsense/scripts/OPNsense/Reticulum/rnstatus.sh`

```sh
#!/bin/sh

VENV="/usr/local/reticulum-venv"
CONFIG="/usr/local/etc/reticulum"

# 5 second timeout
timeout 5 ${VENV}/bin/rnstatus --config ${CONFIG} --json 2>/dev/null || echo '{"error":"rnsd not reachable","interfaces":[]}'
```

### 7e. info.sh

**Path:** `src/opnsense/scripts/OPNsense/Reticulum/info.sh`

```sh
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
RNSTATUS=$(timeout 5 ${VENV}/bin/rnstatus --config /usr/local/etc/reticulum --json 2>/dev/null)
if [ $? -eq 0 ] && [ -n "${RNSTATUS}" ]; then
    NODE_ID=$(echo "${RNSTATUS}" | ${VENV}/bin/python3.11 -c "import sys,json; d=json.load(sys.stdin); print(d.get('identity',''))" 2>/dev/null)
fi

printf '{"rns_version":"%s","lxmf_version":"%s","node_identity":"%s"}\n' "${RNS_VER}" "${LXMF_VER}" "${NODE_ID}"
```

---

## 8. Menu.xml

**Path:** `src/opnsense/mvc/app/models/OPNsense/Reticulum/Menu/Menu.xml`

```xml
<menu>
    <Services>
        <Reticulum VisibleName="Reticulum" cssClass="fa fa-broadcast-tower" order="500">
            <General VisibleName="General Settings"
                     url="/ui/reticulum/general"
                     order="100" />
            <Interfaces VisibleName="Interfaces"
                        url="/ui/reticulum/interfaces"
                        order="200" />
            <Lxmf VisibleName="LXMF / Propagation Node"
                   url="/ui/reticulum/lxmf"
                   order="300" />
            <Logs VisibleName="Log Viewer"
                  url="/ui/reticulum/logs"
                  order="400" />
        </Reticulum>
    </Services>
</menu>
```

**Notes:**
- `cssClass` uses a Font Awesome icon — `fa-broadcast-tower` fits the radio/network theme
- `order` values control sort position within the Services menu
- URLs match the IndexController action routing (Phase 4)

---

## 9. ACL.xml

**Path:** `src/opnsense/mvc/app/models/OPNsense/Reticulum/ACL/ACL.xml`

```xml
<acl>
    <page-services-reticulum>
        <name>WebCfg - Services: Reticulum</name>
        <description>Allow access to Reticulum configuration and service management</description>
        <patterns>
            <pattern>ui/reticulum/*</pattern>
            <pattern>api/reticulum/*</pattern>
        </patterns>
    </page-services-reticulum>
    <page-services-reticulum-readonly>
        <name>WebCfg - Services: Reticulum (Read-Only)</name>
        <description>Allow read-only access to Reticulum status and configuration</description>
        <patterns>
            <pattern>ui/reticulum/*</pattern>
            <pattern>api/reticulum/rnsd/get</pattern>
            <pattern>api/reticulum/rnsd/searchInterfaces</pattern>
            <pattern>api/reticulum/rnsd/getInterface/*</pattern>
            <pattern>api/reticulum/lxmd/get</pattern>
            <pattern>api/reticulum/service/rnsdStatus</pattern>
            <pattern>api/reticulum/service/lxmdStatus</pattern>
            <pattern>api/reticulum/service/rnstatus</pattern>
            <pattern>api/reticulum/service/info</pattern>
            <pattern>api/reticulum/service/rnsdInfo</pattern>
            <pattern>api/reticulum/service/lxmdInfo</pattern>
            <pattern>api/reticulum/service/rnsdLogs</pattern>
            <pattern>api/reticulum/service/lxmdLogs</pattern>
        </patterns>
    </page-services-reticulum-readonly>
</acl>
```

---

## 10. newsyslog Configuration

**Path:** `src/etc/newsyslog.conf.d/reticulum.conf` → installs to `/usr/local/etc/newsyslog.conf.d/reticulum.conf`

```
# logfilename                          [owner:group]  mode  count  size  when  flags
/var/log/reticulum/rnsd.log            reticulum:reticulum  640  5  10240  *  C
/var/log/reticulum/lxmd.log            reticulum:reticulum  640  5  10240  *  C
```

**Notes:**
- Rotates at 10MB (`10240` KB), keeps 5 archives
- `C` flag = create new log file after rotation
- `*` for when = rotate at any time when size exceeds limit

---

## 11. Syshook Script

**Path:** `src/etc/rc.syshook.d/start/50-reticulum` → installs to `/usr/local/etc/rc.syshook.d/start/50-reticulum`

```sh
#!/bin/sh

# Regenerate Reticulum config files from OPNsense config.xml on boot
/usr/local/bin/configctl template reload OPNsense/Reticulum 2>/dev/null || true
```

**Notes:**
- Runs at system start before rc.d services
- Ensures generated config files are current before rnsd/lxmd attempt to start
- `50-` prefix controls execution order relative to other syshook scripts

---

## 12. pkg-plist

**Path:** `os-reticulum/pkg-plist`

Lists every file installed by the package (ensures clean uninstall):

```
/usr/local/etc/rc.d/rnsd
/usr/local/etc/rc.d/lxmd
/usr/local/etc/rc.syshook.d/start/50-reticulum
/usr/local/etc/newsyslog.conf.d/reticulum.conf
/usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/ACL/ACL.xml
/usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Menu/Menu.xml
/usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.xml
/usr/local/opnsense/mvc/app/models/OPNsense/Reticulum/Reticulum.php
/usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/IndexController.php
/usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/Api/RnsdController.php
/usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/Api/LxmdController.php
/usr/local/opnsense/mvc/app/controllers/OPNsense/Reticulum/Api/ServiceController.php
/usr/local/opnsense/mvc/app/views/OPNsense/Reticulum/general.volt
/usr/local/opnsense/mvc/app/views/OPNsense/Reticulum/interfaces.volt
/usr/local/opnsense/mvc/app/views/OPNsense/Reticulum/lxmf.volt
/usr/local/opnsense/mvc/app/views/OPNsense/Reticulum/logs.volt
/usr/local/opnsense/scripts/OPNsense/Reticulum/reconfigure.sh
/usr/local/opnsense/scripts/OPNsense/Reticulum/rnsd_status.sh
/usr/local/opnsense/scripts/OPNsense/Reticulum/lxmd_status.sh
/usr/local/opnsense/scripts/OPNsense/Reticulum/rnstatus.sh
/usr/local/opnsense/scripts/OPNsense/Reticulum/info.sh
/usr/local/opnsense/service/conf/actions.d/actions_reticulum.conf
/usr/local/opnsense/service/templates/OPNsense/Reticulum/+TARGETS
/usr/local/opnsense/service/templates/OPNsense/Reticulum/reticulum_config.j2
/usr/local/opnsense/service/templates/OPNsense/Reticulum/lxmf_config.j2
/usr/local/opnsense/service/templates/OPNsense/Reticulum/rc.conf.d_rnsd.j2
/usr/local/opnsense/service/templates/OPNsense/Reticulum/rc.conf.d_lxmd.j2
/usr/local/opnsense/service/templates/OPNsense/Reticulum/lxmf_allowed.j2
/usr/local/opnsense/service/templates/OPNsense/Reticulum/lxmf_ignored.j2
/usr/local/opnsense/www/js/widgets/Reticulum.js
```

---

## 13. File Permissions Summary

| File | Mode | Owner |
|------|------|-------|
| rc.d/rnsd, rc.d/lxmd | 755 | root:wheel |
| rc.syshook.d/start/50-reticulum | 755 | root:wheel |
| scripts/*.sh | 755 | root:wheel |
| actions_reticulum.conf | 644 | root:wheel |
| Menu.xml, ACL.xml | 644 | root:wheel |
| newsyslog.conf.d/reticulum.conf | 644 | root:wheel |
| /usr/local/etc/reticulum/ | 700 | reticulum:reticulum |
| /usr/local/etc/lxmf/ | 700 | reticulum:reticulum |
| /var/db/reticulum/ | 700 | reticulum:reticulum |
| /var/log/reticulum/ | 750 | reticulum:reticulum |

---

## 14. Implementation Checklist

- [ ] Create Makefile with correct PLUGIN_DEPENDS
- [ ] Write pkg-install (user creation, virtualenv, directories, source clone and build)
- [ ] Verify build deps present: python3.11, git, gcc in pkg-install
- [ ] Clone Reticulum from source into /usr/local/reticulum-src/reticulum/
- [ ] Clone LXMF from source into /usr/local/reticulum-src/lxmf/
- [ ] Build and install rns into virtualenv from source
- [ ] Build and install lxmf into virtualenv from source
- [ ] Record git hash/tag versions in .pkg-versions
- [ ] Write pkg-deinstall (service stop, generated file cleanup)
- [ ] Verify pkg-deinstall removes /usr/local/reticulum-src/
- [ ] Write rc.d/rnsd (with PROVIDE/REQUIRE, daemon management)
- [ ] Write rc.d/lxmd (with REQUIRE: rnsd, pre-start check)
- [ ] Write actions_reticulum.conf (all configd actions)
- [ ] Write helper scripts (reconfigure, status, rnstatus, info)
- [ ] Write Menu.xml (4 navigation entries)
- [ ] Write ACL.xml (full + read-only privilege sets)
- [ ] Write newsyslog.conf.d/reticulum.conf
- [ ] Write syshook 50-reticulum
- [ ] Write pkg-plist
- [ ] Test: `make package` builds without errors
- [ ] Test: `pkg install` on OPNsense VM creates user and virtualenv
- [ ] Test: `service rnsd start/stop/status` works
- [ ] Test: `configctl reticulum start.rnsd` works through configd
- [ ] Test: Menu appears in OPNsense navigation (pages will 404 until Phase 4-5)
