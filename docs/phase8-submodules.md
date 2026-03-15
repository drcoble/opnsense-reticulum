# Phase 8 — Git Submodule Version Pinning for RNS and LXMF

## Overview

Refactor RNS and LXMF dependency management from unpinned PyPI installs
(`pip install --upgrade rns lxmf`) to version-pinned git submodules. The
submodules act as the canonical version record in git history. `pkg-install`
and the integration test CI both install from those pinned sources rather than
pulling whatever PyPI serves at run time.

---

## Current State (Problems)

| Item | Current behaviour | Problem |
|---|---|---|
| `pkg-install` | `pip install --upgrade rns lxmf` | Installs latest PyPI version — non-deterministic, breaks on upstream release |
| `integration-test.yml` deploy step | `pip install --quiet rns lxmf` | Same — unpinned PyPI pull at CI time |
| `.gitmodules` | Paths `net/reticulum/src/lib/rns-src` and `net/reticulum/src/lib/lxmf-src` | Paths match a FreeBSD ports layout, not the `os-reticulum` plugin structure; directories do not exist; submodules were never initialized |
| `ci.yml` static-analysis job | `submodules: false` | Correct (linting doesn't need source) |
| `ci.yml` unit-tests job | No explicit submodule flag | Safe (unit tests don't import RNS/LXMF) but should be explicit |

---

## Target State

```
<repo root>/
├── reticulum_project/
│   ├── rns-src/          ← git submodule, pinned to RNS release tag
│   └── lxmf-src/         ← git submodule, pinned to LXMF release tag
├── reticulum_project/versions.env   ← human-readable version record (auto-updated by pin script)
├── os-reticulum/
│   ├── pkg-install       ← installs from /usr/local/reticulum-src/ (cloned at pin tag)
│   └── ...
└── .gitmodules           ← updated paths: reticulum_project/rns-src, reticulum_project/lxmf-src
```

**Install-time flow (OPNsense target)**

```
pkg install os-reticulum
  → pkg-install runs
    → reads RNS_TAG / LXMF_TAG from embedded versions.env
    → git clone --depth 1 --branch $RNS_TAG  markqvist/Reticulum  /usr/local/reticulum-src/reticulum
    → git clone --depth 1 --branch $LXMF_TAG markqvist/LXMF       /usr/local/reticulum-src/lxmf
    → pip install /usr/local/reticulum-src/reticulum
    → pip install /usr/local/reticulum-src/lxmf
    → records git describe output in /var/db/reticulum/.pkg-versions
```

**CI flow (integration test)**

```
git clone --recurse-submodules  (already done)
  reticulum_project/rns-src  and  reticulum_project/lxmf-src  are populated at pinned commit
  → pip install /path/to/reticulum_project/rns-src
  → pip install /path/to/reticulum_project/lxmf-src
  (no PyPI network call needed)
```

---

## Prerequisites / Compatibility

### git version

`pkg-install` uses `git clone --branch <tag>`. The `--branch` flag accepts tag
names (not just branch names) reliably as of **git 2.0**. Git 1.7.10 introduced
`--branch` but behavior with tag names was inconsistent before 2.0.

**Minimum required: git >= 2.0.**

OPNsense runs on FreeBSD 13.x or later. FreeBSD 13+ ships git 2.33+ from the
package repository. `PLUGIN_DEPENDS` ensures `pkg install git` resolves a 2.x
release. If running a custom build pinned to FreeBSD 12.x, verify `pkg install
git` resolves to 2.x before using this plugin.

---

## Step-by-Step Plan

### Step 1 — Fix `.gitmodules`

**File:** `.gitmodules`

Replace the current invalid paths with the `reticulum_project/` layout.

```ini
[submodule "reticulum_project/rns-src"]
    path = reticulum_project/rns-src
    url = https://github.com/markqvist/Reticulum.git
    branch = master

[submodule "reticulum_project/lxmf-src"]
    path = reticulum_project/lxmf-src
    url = https://github.com/markqvist/LXMF.git
    branch = master
```

> `branch = master` records the upstream tracking branch.  The actual pinned
> commit is stored in git's object store (the submodule pointer in the tree).
> These are independent: you track master but the submodule pointer is pinned to
> the specific release commit until you explicitly advance it.

---

### Step 2 — Initialize submodules and pin to release tags

Run locally (one-time setup, then commit the result):

```sh
# Remove stale submodule registration from git config if present
git submodule deinit -f net/reticulum/src/lib/rns-src  2>/dev/null || true
git submodule deinit -f net/reticulum/src/lib/lxmf-src 2>/dev/null || true
git rm --cached net/reticulum/src/lib/rns-src  2>/dev/null || true
git rm --cached net/reticulum/src/lib/lxmf-src 2>/dev/null || true
# Remove the stale FreeBSD ports path stub only if it exists and is tracked by git.
# git rm -r is safe: it fails loudly if the path contains unexpected content
# and records the removal in the index so it appears in the commit diff.
if git ls-files --error-unmatch net/ > /dev/null 2>&1; then
    # Directory or files are tracked — remove via git so the deletion is staged
    git rm -r --cached net/ 2>/dev/null || true
    rm -rf net/
elif [ -d net/ ]; then
    # Directory exists but is not tracked — fail loudly rather than silently destroy
    echo "WARNING: net/ exists but is not tracked by git."
    echo "Contents:"
    find net/ -maxdepth 3
    echo "Remove manually if safe, then re-run from the next step."
    exit 1
fi
# If net/ does not exist at all, no action needed.

# Add the submodules at the correct paths
git submodule add https://github.com/markqvist/Reticulum.git reticulum_project/rns-src
git submodule add https://github.com/markqvist/LXMF.git      reticulum_project/lxmf-src

# Pin to specific release tags
# (Substitute the actual desired tags - check github.com/markqvist/Reticulum/releases)
RNS_TAG="0.8.9"   # example — verify current stable release
LXMF_TAG="0.6.2"  # example — verify current stable release

git -C reticulum_project/rns-src  fetch --tags
git -C reticulum_project/rns-src  checkout "$RNS_TAG"

git -C reticulum_project/lxmf-src fetch --tags
git -C reticulum_project/lxmf-src checkout "$LXMF_TAG"

# Stage the submodule pointers and write versions.env
git add reticulum_project/rns-src reticulum_project/lxmf-src .gitmodules
```

---

### Step 3 — Add `reticulum_project/versions.env`

**File:** `reticulum_project/versions.env` (new file, committed to repo)

```sh
# Pinned upstream dependency versions.
# Update this file together with advancing the submodule pointer.
# Used by pkg-install to clone at the exact same tag on the OPNsense target.
RNS_TAG="0.8.9"
LXMF_TAG="0.6.2"
```

No special git attributes are needed for this file. It is a plain shell-sourceable
text file. Do not add an `export-subst` entry to `.gitattributes`; that attribute
only affects `git archive` output and only when the file contains `$Format:` tokens,
which this file does not.

**Why this file?**

`pkg-install` runs on the OPNsense target where the git repo is not present.
The submodule commit hash is in git's object store, not in any deployed file.
`versions.env` bridges the gap: it is a plain text file that travels with the
package and tells `pkg-install` which tag to clone.

Whenever you advance the submodule pointer (Step 2), update `versions.env` in
the same commit.  Reviewers can see both changes in one diff.

---

### Step 4 — Update `os-reticulum/pkg-install`

**File:** `os-reticulum/pkg-install`

Replace the PyPI install block (lines 72–77) with a source-clone-and-install
block that reads tag versions from the installed `versions.env`.

**Remove:**
```sh
# Install rns and lxmf from PyPI
echo "[reticulum] Installing rns and lxmf from PyPI..."
if ! "${VENV_PATH}/bin/pip" install --upgrade rns lxmf; then
    echo "[reticulum] ERROR: pip install of rns/lxmf failed." >&2
    exit 1
fi
```

**Replace with:**
```sh
VERSIONS_ENV="/usr/local/share/os-reticulum/versions.env"
SRC_BASE="/usr/local/reticulum-src"

# Read pinned tags from versions.env (installed alongside this script)
if [ ! -f "${VERSIONS_ENV}" ]; then
    echo "[reticulum] ERROR: ${VERSIONS_ENV} not found — package may be corrupt." >&2
    exit 1
fi
# shellcheck source=/dev/null
. "${VERSIONS_ENV}"

if [ -z "${RNS_TAG}" ] || [ -z "${LXMF_TAG}" ]; then
    echo "[reticulum] ERROR: RNS_TAG or LXMF_TAG not set in ${VERSIONS_ENV}." >&2
    exit 1
fi

mkdir -p "${SRC_BASE}"

clone_at_tag() {
    _repo_url="$1"
    _dest_dir="$2"
    _tag="$3"
    _name="$4"

    if [ -d "${_dest_dir}/.git" ]; then
        echo "[reticulum] Updating ${_name} source to ${_tag}..."
        # Fetch only the specific tag needed. Using `fetch --tags` on a shallow
        # clone is unreliable: tags not reachable from the shallow history are
        # silently skipped, causing the subsequent checkout to fail.
        # The refspec below fetches exactly one tag and keeps the clone shallow.
        if ! git -C "${_dest_dir}" fetch --depth 1 origin \
                "refs/tags/${_tag}:refs/tags/${_tag}" --quiet; then
            echo "[reticulum] ERROR: git fetch failed for ${_name} at tag ${_tag}." >&2
            exit 1
        fi
        git -C "${_dest_dir}" checkout "${_tag}" --quiet
    else
        echo "[reticulum] Cloning ${_name} at ${_tag}..."
        rm -rf "${_dest_dir}"
        git clone --depth 1 --branch "${_tag}" "${_repo_url}" "${_dest_dir}" --quiet
        _git_exit=$?
        if [ ${_git_exit} -eq 128 ]; then
            echo "[reticulum] ERROR: Could not reach GitHub to clone ${_name}." \
                 "This package requires internet access during initial installation." >&2
            exit 1
        elif [ ${_git_exit} -ne 0 ]; then
            echo "[reticulum] ERROR: git clone failed for ${_name} at tag ${_tag}" \
                 "(exit code ${_git_exit})." >&2
            exit 1
        fi
    fi
}

clone_at_tag "https://github.com/markqvist/Reticulum.git" \
    "${SRC_BASE}/reticulum" "${RNS_TAG}" "Reticulum (rns)"

clone_at_tag "https://github.com/markqvist/LXMF.git" \
    "${SRC_BASE}/lxmf" "${LXMF_TAG}" "LXMF (lxmd)"

echo "[reticulum] Installing rns from source (${RNS_TAG})..."
if ! "${VENV_PATH}/bin/pip" install --quiet "${SRC_BASE}/reticulum"; then
    echo "[reticulum] ERROR: pip install failed for rns." >&2
    echo "[reticulum] Removing cloned source to allow clean retry on next install." >&2
    rm -rf "${SRC_BASE}/reticulum"
    exit 1
fi

echo "[reticulum] Installing lxmf from source (${LXMF_TAG})..."
if ! "${VENV_PATH}/bin/pip" install --quiet "${SRC_BASE}/lxmf"; then
    echo "[reticulum] ERROR: pip install failed for lxmf." >&2
    echo "[reticulum] Removing cloned source to allow clean retry on next install." >&2
    rm -rf "${SRC_BASE}/lxmf"
    exit 1
fi
```

**Also update** the version-recording block (replaces `importlib.metadata`):
```sh
# Record installed versions — use pinned tag from versions.env as the
# authoritative version string. git describe is unreliable on shallow clones
# and can produce extended formats like "0.8.9-3-gabcdef1" that look unexpected
# in the dashboard widget and info.sh output. versions.env is already the
# single source of truth; use it directly.
RNS_VER="${RNS_TAG}"
LXMF_VER="${LXMF_TAG}"
```

**Add `git` to the dependency checks** at the top of `pkg-install`:
```sh
# check_dep is defensive redundancy: PLUGIN_DEPENDS in the Makefile tells pkg
# to install git before pkg-install runs under normal `pkg install` flow.
# However, pkg-install can also be invoked directly (e.g. during development,
# OPNsense plugin testing, or a manual `sh pkg-install`) without pkg resolving
# dependencies first. check_dep catches that case and prints an actionable
# error rather than a confusing "git: command not found" from inside
# clone_at_tag().
check_dep git "Install with: pkg install git"
```

---

### Step 5 — Add `versions.env` to `pkg-plist` and source tree

**File:** `os-reticulum/pkg-plist` — add two lines:
```
/usr/local/share/os-reticulum/versions.env
@dir /usr/local/share/os-reticulum
```

The `@dir` entry is required because `/usr/local/share/os-reticulum/` is a
new directory not created by any other plist entry. FreeBSD `pkg` does not
auto-create unlisted directories. Without `@dir`, installation fails (directory
missing) and deinstallation leaves an orphaned empty directory. Place the `@dir`
line immediately after the file entry.

**File layout in source tree:**
```
os-reticulum/src/usr/local/share/os-reticulum/versions.env
```

This file **must be a regular file copy** of `reticulum_project/versions.env`. Do not use
a symlink. `make install` / `plugins.mk` deploys the contents of
`os-reticulum/src/` to the OPNsense target; `reticulum_project/` is not deployed. A symlink
pointing outside `os-reticulum/src/` would arrive on the target as a dangling
symlink and `pkg-install` would immediately fail when sourcing `versions.env`.

Keep the two files in sync by always copying in the same commit that advances
the submodule pointer:

```sh
cp reticulum_project/versions.env os-reticulum/src/usr/local/share/os-reticulum/versions.env
```

Two files, one commit — reviewers see both change together.

---

### Step 6 — Update `Makefile` dependencies

**File:** `os-reticulum/Makefile`

Add `git` to `PLUGIN_DEPENDS` so the FreeBSD package manager installs it before
`pkg-install` runs:

```makefile
PLUGIN_DEPENDS=     python311 py311-cryptography py311-setuptools py311-wheel git
```

`git` is already referenced in `phase1-skeleton.md`'s original Makefile design
but was dropped in the current file.  This restores it.

---

### Step 7 — Update `integration-test.yml` deploy step

**File:** `.github/workflows/integration-test.yml`

The deploy-to-OPNsense SSH block currently does:
```sh
/usr/local/reticulum-venv/bin/pip install --quiet rns lxmf
/usr/local/reticulum-venv/bin/pip install --quiet --force-reinstall --no-deps rns lxmf
```

Replace with an install from the submodule source that was already cloned into
`/tmp/ci-reticulum` by `git clone --recurse-submodules`:

```sh
# Install from pinned submodule source (no PyPI pull)
REPO_ROOT="/tmp/ci-reticulum"
/usr/local/reticulum-venv/bin/pip install --quiet "${REPO_ROOT}/reticulum_project/rns-src"
/usr/local/reticulum-venv/bin/pip install --quiet "${REPO_ROOT}/reticulum_project/lxmf-src"
echo "Reticulum installed OK (rnsd: \$(/usr/local/reticulum-venv/bin/rnsd --version 2>&1 || echo NOT FOUND))"
```

The `git clone --recurse-submodules` call three lines earlier in the same block
already populates `reticulum_project/rns-src` and `reticulum_project/lxmf-src` at the pinned commit.
No additional changes needed to the checkout step.

---

### Step 8 — Explicit `submodules: false` across all workflows

Any workflow that does not install or import RNS/LXMF must set
`submodules: false` on every `actions/checkout` step. This prevents slow,
unnecessary submodule clones on ephemeral runners and documents intent.

**8a — `ci.yml`:**

```yaml
# static-analysis job — already set, no change needed
- uses: actions/checkout@v4
  with:
    submodules: false

# unit-tests job — ADD submodules: false
- uses: actions/checkout@v4
  with:
    submodules: false
```

**8b — `lint.yml`:**

Four parallel jobs (`php`, `xml`, `shell`, `python`), each with its own
checkout. Add `submodules: false` to all four. This is the highest-frequency
workflow (triggers on every PR); an accidental submodule pull would be most
expensive here.

**8c — `test-unit.yml`:**

One job (`pytest`). Add `submodules: false`. Mirrors `ci.yml` unit-tests.

**8d — `release.yml`:**

Add `submodules: false` alongside existing `fetch-depth: 0`. The `tar` command
archives only `os-reticulum/`, so `reticulum_project/rns-src` and `reticulum_project/lxmf-src` are
structurally excluded regardless. `versions.env` travels inside
`os-reticulum/src/`; submodule source is cloned at install time on the target.

**8e — `auto-merge.yml`:** No change required — no `actions/checkout` step.

**8f — `claude-code-review.yml` and `claude.yml`:** No change required — source
review only, no submodule dependency.

**8g — Add `versions.env` sync check to `ci.yml`:**

Add a step to the `static-analysis` job that fails CI if the two `versions.env`
copies diverge:

```yaml
- name: Check versions.env sync
  run: |
    if ! diff -q reticulum_project/versions.env \
        os-reticulum/src/usr/local/share/os-reticulum/versions.env > /dev/null 2>&1; then
      echo "ERROR: versions.env files are out of sync." >&2
      echo "Fix: cp reticulum_project/versions.env os-reticulum/src/usr/local/share/os-reticulum/versions.env" >&2
      exit 1
    fi
```

**Complete workflow audit table:**

| Workflow | Has checkout? | Current `submodules:` | Required action |
|---|---|---|---|
| `ci.yml` static-analysis | Yes | `false` (explicit) | Add versions.env sync check |
| `ci.yml` unit-tests | Yes | None | Add `submodules: false` |
| `lint.yml` (4 jobs) | Yes (×4) | None | Add `submodules: false` to all |
| `test-unit.yml` | Yes | None | Add `submodules: false` |
| `release.yml` | Yes | None | Add `submodules: false` |
| `integration-test.yml` | Yes (SSH) | `--recurse-submodules` | No change — submodules required |
| `auto-merge.yml` | No | N/A | No change |
| `claude-code-review.yml` | Yes | None | No change (review only) |
| `claude.yml` | Yes | None | No change (review only) |

---

### Step 9 — Update `pkg-deinstall` (no change required)

**File:** `os-reticulum/pkg-deinstall`

The existing `rm -rf /usr/local/reticulum-src` already handles cleanup of the
cloned source directories.  No modification needed.

---

## Files Changed Summary

| File | Change |
|---|---|
| `.gitmodules` | Fix paths: `net/reticulum/...` → `reticulum_project/rns-src`, `reticulum_project/lxmf-src` |
| `reticulum_project/rns-src/` | New submodule (markqvist/Reticulum, pinned to RNS release tag) |
| `reticulum_project/lxmf-src/` | New submodule (markqvist/LXMF, pinned to LXMF release tag) |
| `reticulum_project/versions.env` | New file — machine-readable `RNS_TAG` / `LXMF_TAG` |
| `os-reticulum/src/usr/local/share/os-reticulum/versions.env` | New deployed copy of versions.env |
| `os-reticulum/pkg-install` | Replace PyPI install with tag-pinned git clone + pip install from source |
| `os-reticulum/pkg-plist` | Add `/usr/local/share/os-reticulum/versions.env` |
| `os-reticulum/Makefile` | Add `git` to `PLUGIN_DEPENDS` |
| `.github/workflows/integration-test.yml` | Install from submodule source, not PyPI |
| `.github/workflows/ci.yml` | Explicit `submodules: false` on unit-tests; add versions.env sync check |
| `.github/workflows/lint.yml` | Add `submodules: false` to all four job checkouts |
| `.github/workflows/test-unit.yml` | Add `submodules: false` to pytest job checkout |
| `.github/workflows/release.yml` | Add `submodules: false` to release job checkout |
| `os-reticulum/pkg-deinstall` | No change |

---

## Upgrading RNS or LXMF (Ongoing Workflow)

When a new upstream release is available:

```sh
# 1. Advance the submodule pointer
git -C reticulum_project/rns-src  fetch --tags
git -C reticulum_project/rns-src  checkout 0.9.0   # new tag

# 2. Update versions.env (both copies)
sed -i '' 's/RNS_TAG=.*/RNS_TAG="0.9.0"/' reticulum_project/versions.env
cp reticulum_project/versions.env os-reticulum/src/usr/local/share/os-reticulum/versions.env

# 3. Commit everything together
git add reticulum_project/rns-src reticulum_project/versions.env \
    os-reticulum/src/usr/local/share/os-reticulum/versions.env
git commit -m "chore: bump RNS to 0.9.0"
```

Reviewers see the submodule pointer advance and the `versions.env` change in
one diff.  There is a single source of truth for what version is running.

---

## Migration from PyPI Installs

Operators who installed `os-reticulum` under the previous PyPI-based flow
upgrade via the normal mechanism:

```sh
pkg upgrade os-reticulum
```

This triggers `pkg-install` for the new version. No manual intervention needed.

| Condition on upgrade | Outcome |
|---|---|
| `/usr/local/reticulum-src` absent (PyPI install) | Fresh clone runs; venv updated in-place |
| `/usr/local/reticulum-src` present (prior Phase 8) | Fetch + checkout to new tag |
| `/usr/local/reticulum-venv` present | Kept; packages overwritten by `pip install` from source |
| `/var/db/reticulum/.pkg-versions` present | Overwritten with tag values from `versions.env` |

The `clone_at_tag` function handles the "no directory" case with a fresh clone.
The venv guard (`if [ ! -d "${VENV_PATH}" ]`) skips re-creation, and pip
install from source overwrites the previously PyPI-installed packages. The old
`.pkg-versions` file (written by `importlib.metadata`) is overwritten in full.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Submodules at `reticulum_project/`, not inside `os-reticulum/` | Keeps plugin source (`os-reticulum/src/`) clean; `reticulum_project/` is a standard location for third-party source |
| `versions.env` as a separate file, not inlined into `pkg-install` | Allows the deployed file to be inspected on the target (`cat /usr/local/share/os-reticulum/versions.env`) without reading shell scripts; easy to diff in PRs |
| Clone at `pkg-install` time (not bundle in package) | Avoids committing large upstream source trees or binary wheels; OPNsense systems have internet access at install time; `--depth 1` keeps clone fast |
| `--depth 1 --branch $TAG` clone | Fetches only the tag commit, not full history — minimizes network and disk use on OPNsense target |
| Shallow clone preserved on reinstall (`--depth 1` fetch) | OPNsense targets are embedded systems; full upstream history has no operational value. Fetching only the required tag refspec keeps cost identical to a fresh install |
| Record versions from `versions.env` tags, not `git describe` | `--depth 1 --branch $TAG` clones always have a clean tag at HEAD, but relying on `git describe` is fragile if clone logic changes. `versions.env` is already the authoritative version record; use it directly |
| `check_dep git` kept alongside `PLUGIN_DEPENDS` | Defensive: `PLUGIN_DEPENDS` only applies when pkg resolves dependencies. Direct `sh pkg-install` invocation bypasses pkg and would produce a cryptic error inside `clone_at_tag()` |
| `versions.env` must be a regular file copy, never a symlink | A symlink into `reticulum_project/` would dangle on the deployed target where `reticulum_project/` doesn't exist |
| No change to `pkg-deinstall` | Existing `rm -rf /usr/local/reticulum-src` already covers the new clone paths |

---

## Implementation Checklist

- [ ] Remove stale `.gitmodules` paths (`net/reticulum/...`) — use safe conditional removal for `net/`
- [ ] `git submodule add` for `reticulum_project/rns-src` and `reticulum_project/lxmf-src`
- [ ] Identify and verify current stable release tags for RNS and LXMF
- [ ] Checkout pinned tags in both submodules
- [ ] Create `reticulum_project/versions.env` with `RNS_TAG` and `LXMF_TAG` (no `.gitattributes` needed)
- [ ] Create `os-reticulum/src/usr/local/share/os-reticulum/` directory
- [ ] Add `versions.env` deployed copy to source tree (regular file, not symlink)
- [ ] Update `pkg-install`: add `git` dep check, replace PyPI block, update version recording
- [ ] Update `pkg-plist`: add `versions.env` file entry and `@dir /usr/local/share/os-reticulum` entry
- [ ] Update `Makefile`: add `git` to `PLUGIN_DEPENDS`
- [ ] Update `integration-test.yml`: install from `reticulum_project/rns-src` and `reticulum_project/lxmf-src`
- [ ] Update `ci.yml`: explicit `submodules: false` on unit-tests job; add versions.env sync check
- [ ] Update `lint.yml`: add `submodules: false` to all four job checkouts
- [ ] Update `test-unit.yml`: add `submodules: false` to pytest job checkout
- [ ] Update `release.yml`: add `submodules: false` to release job checkout
- [ ] Verify `auto-merge.yml` has no checkout step — no change needed
- [ ] Verify `claude-code-review.yml` and `claude.yml` have no submodule dependency — no change needed
- [ ] Verify `git submodule status` shows correct pinned commit
- [ ] Test: `pkg-install` on OPNsense VM with `git` present — confirm correct version in `.pkg-versions`
- [ ] Test: `rnsd --version` and `lxmd --version` output matches pinned tags
- [ ] Test: integration CI passes with submodule source install
- [ ] Test: `pkg upgrade` (re-run pkg-install) successfully updates to new pin after bumping tags
- [ ] Test: upgrade from non-adjacent tag (e.g. 0.8.9 → 0.9.1) confirms targeted fetch succeeds
- [ ] Test: fresh install on system without git fails with clear error message
- [ ] Test: network-isolated install fails with actionable `[reticulum]` error message
- [ ] Test: pip failure cleans up cloned source for clean retry
