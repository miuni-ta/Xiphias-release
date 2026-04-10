#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"

if [[ -d "$(cd "${BASE_DIR}/.." && pwd)/release/gamehub-console" ]]; then
  WORKSPACE_ROOT="$(cd "${BASE_DIR}/.." && pwd)"
elif [[ -d "$(cd "${BASE_DIR}/../.." && pwd)/release/gamehub-console" ]]; then
  WORKSPACE_ROOT="$(cd "${BASE_DIR}/../.." && pwd)"
else
  printf '[ota] Error: Could not resolve the Xiphias workspace root from %s\n' "${BASE_DIR}" >&2
  exit 1
fi

RELEASE_ROOT="${WORKSPACE_ROOT}/release"
LIVE_ROOT="${RELEASE_ROOT}"
GIT_ROOT="${WORKSPACE_ROOT}"

APPLY_SYSTEM_FILES=0
SKIP_BACKUP=0
RESTART_KIOSK=1
CHECK_ONLY=0
TMP_DIR=""

log() {
  printf '[ota] %s\n' "$*"
}

fail() {
  printf '[ota] Error: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${TMP_DIR}" && -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR}"
  fi
}

usage() {
  cat <<EOF
Usage: bash ${BASE_DIR}/ota_git_update.sh [options]

Pull the kiosk release from GitHub into ${RELEASE_ROOT} and deploy the
managed kiosk paths into ${LIVE_ROOT}.

Options:
  --check-only         Check GitHub for changes without deploying anything.
  --apply-system-files  Install the service, user env generator, cron, and sudoers files to /etc.
  --skip-backup         Skip the pre-deploy rollback zip.
  --no-restart          Do not restart kiosk processes after deploy.
  --help                Show this help text.

Environment:
  console.env is loaded from ${LIVE_ROOT}/gamehub-console/console.env first,
  then from ${BASE_DIR}/console.env if the live copy is missing.

Required variables:
  OTA_REPO              GitHub repo in owner/name format.

Optional variables:
  OTA_BRANCH            Branch to deploy. Defaults to master.
  OTA_TOKEN             Token for private-repo access.
  OTA_PATH_IN_REPO      Relative path to the deploy root in the repo.
                        When omitted, the script auto-detects a root that
                        contains gamehub-console/.

Notes:
  - --check-only exits 10 when an update is available, 0 when already current.
  - When ${GIT_ROOT} is a clean git worktree on OTA_BRANCH, OTA pulls there
    first and uses its tracked release/ subtree directly as the live tree.
  - Non-git deployments fall back to a temporary GitHub clone.
  - console.env, logs, and __pycache__ stay local on the device.
  - Use --apply-system-files only when files under gamehub-console/files/ or
    .xinitrc changed and need to be reinstalled.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=1
      RESTART_KIOSK=0
      ;;
    --apply-system-files)
      APPLY_SYSTEM_FILES=1
      ;;
    --skip-backup)
      SKIP_BACKUP=1
      ;;
    --no-restart)
      RESTART_KIOSK=0
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      fail "Unknown option: $1"
      ;;
  esac
  shift
done

trap cleanup EXIT

ENV_FILE=""
for candidate in \
  "${LIVE_ROOT}/gamehub-console/console.env" \
  "${BASE_DIR}/console.env"
do
  if [[ -f "${candidate}" ]]; then
    ENV_FILE="${candidate}"
    break
  fi
done

[[ -n "${ENV_FILE}" ]] || fail "Could not find console.env in the live or release kiosk tree."

# shellcheck disable=SC1090
source "${ENV_FILE}"

OTA_REPO="${OTA_REPO:-}"
OTA_BRANCH="${OTA_BRANCH:-master}"
OTA_TOKEN="${OTA_TOKEN:-}"
OTA_PATH_IN_REPO="${OTA_PATH_IN_REPO:-}"

[[ -n "${OTA_REPO}" ]] || fail "OTA_REPO is missing from ${ENV_FILE}."

TMP_DIR="$(mktemp -d)"
CLONE_DIR="${TMP_DIR}/repo"
CLONE_URL="https://github.com/${OTA_REPO}.git"
OTA_STATE_FILE="${LIVE_ROOT}/backup/ota_state.env"

worktree_repo_root() {
  git -C "${GIT_ROOT}" rev-parse --show-toplevel 2>/dev/null || true
}

read_version_file() {
  local path="$1"
  local value=""

  if [[ -f "${path}" ]]; then
    value="$(sed -n '1{s/[[:space:]]*$//;p;q;}' "${path}" 2>/dev/null || true)"
  fi

  if [[ -z "${value}" ]]; then
    value="Unknown"
  fi

  printf '%s\n' "${value}"
}

emit_check_result() {
  local status="$1"
  local current_version="$2"
  local remote_version="$3"

  printf 'CHECK_STATUS=%s\n' "${status}"
  printf 'CHECK_CURRENT_VERSION=%s\n' "${current_version}"
  printf 'CHECK_REMOTE_VERSION=%s\n' "${remote_version}"
}

emit_deploy_result() {
  local status="$1"
  local current_version="$2"
  local remote_version="$3"

  printf 'OTA_STATUS=%s\n' "${status}"
  printf 'OTA_CURRENT_VERSION=%s\n' "${current_version}"
  printf 'OTA_REMOTE_VERSION=%s\n' "${remote_version}"
}

worktree_is_clean() {
  git -C "${GIT_ROOT}" diff --quiet --ignore-submodules -- &&
    git -C "${GIT_ROOT}" diff --cached --quiet --ignore-submodules --
}

worktree_is_shallow() {
  [[ "$(git -C "${GIT_ROOT}" rev-parse --is-shallow-repository 2>/dev/null || true)" == "true" ]]
}

repo_head() {
  local repo_root="$1"

  git -C "${repo_root}" rev-parse HEAD 2>/dev/null || true
}

read_state_commit() {
  if [[ -f "${OTA_STATE_FILE}" ]]; then
    sed -n 's/^COMMIT=//p' "${OTA_STATE_FILE}" 2>/dev/null | sed -n '1p'
  fi
}

write_state_commit() {
  local commit="$1"
  local version="$2"

  [[ -n "${commit}" ]] || return 0

  mkdir -p "$(dirname "${OTA_STATE_FILE}")"
  cat > "${OTA_STATE_FILE}" <<EOF
COMMIT=${commit}
VERSION=${version}
UPDATED_AT=$(date '+%Y-%m-%d %H:%M:%S %z')
EOF
}

effective_local_ref() {
  local repo_root current_branch local_head state_commit

  repo_root="$(worktree_repo_root)"
  if [[ -n "${repo_root}" && "${repo_root}" == "${GIT_ROOT}" ]]; then
    local_head="$(repo_head "${GIT_ROOT}")"
    current_branch="$(git -C "${GIT_ROOT}" branch --show-current 2>/dev/null || true)"
    if [[ -n "${local_head}" && "${current_branch}" == "${OTA_BRANCH}" ]] && worktree_is_clean; then
      printf '%s\n' "${local_head}"
      return 0
    fi
  fi

  state_commit="$(read_state_commit)"
  if [[ -n "${state_commit}" ]]; then
    printf '%s\n' "${state_commit}"
    return 0
  fi

  if [[ -n "${repo_root}" && "${repo_root}" == "${GIT_ROOT}" ]]; then
    local_head="$(repo_head "${GIT_ROOT}")"
    if [[ -n "${local_head}" ]]; then
      printf '%s\n' "${local_head}"
      return 0
    fi
  fi

  return 1
}

prepare_worktree_source_root() {
  local repo_root current_branch

  repo_root="$(worktree_repo_root)"
  [[ -n "${repo_root}" ]] || return 1
  if [[ "${repo_root}" != "${GIT_ROOT}" ]]; then
    log "Skipping local git worktree ${repo_root}; expected ${GIT_ROOT}"
    return 1
  fi

  current_branch="$(git -C "${GIT_ROOT}" branch --show-current 2>/dev/null || true)"
  if [[ -z "${current_branch}" ]]; then
    log "Skipping local git worktree; could not determine the current branch"
    return 1
  fi
  if [[ "${current_branch}" != "${OTA_BRANCH}" ]]; then
    log "Skipping local git worktree on ${current_branch}; expected ${OTA_BRANCH}"
    return 1
  fi

  if ! worktree_is_clean; then
    log "Local git worktree has tracked changes; cannot pull latest changes directly"
    return 1
  fi

  if worktree_is_shallow; then
    log "Expanding shallow git worktree history before pull"
    if ! git -C "${GIT_ROOT}" fetch --unshallow origin "${OTA_BRANCH}"; then
      log "git fetch --unshallow failed for ${GIT_ROOT}"
      return 1
    fi
  fi

  log "Fetching ${OTA_BRANCH} from origin in local git worktree ${GIT_ROOT}"
  if ! git -C "${GIT_ROOT}" fetch origin "${OTA_BRANCH}"; then
    log "git fetch failed for ${GIT_ROOT}"
    return 1
  fi

  log "Pulling ${OTA_BRANCH} into local git worktree ${GIT_ROOT}"
  if ! git -C "${GIT_ROOT}" pull --ff-only origin "${OTA_BRANCH}"; then
    log "git pull --ff-only failed for ${GIT_ROOT}"
    return 1
  fi

  if [[ ! -d "${GIT_ROOT}/release/gamehub-console" ]]; then
    log "Local git worktree is missing ${GIT_ROOT}/release/gamehub-console after pull"
    return 1
  fi
  printf '%s\n' "${GIT_ROOT}/release"
}

check_worktree_updates() {
  local repo_root current_branch local_head remote_head current_ref current_version remote_version

  repo_root="$(worktree_repo_root)"
  [[ -n "${repo_root}" ]] || return 2
  [[ "${repo_root}" == "${GIT_ROOT}" ]] || return 2

  current_branch="$(git -C "${GIT_ROOT}" branch --show-current 2>/dev/null || true)"
  [[ -n "${current_branch}" ]] || return 2
  [[ "${current_branch}" == "${OTA_BRANCH}" ]] || return 2

  log "Fetching ${OTA_BRANCH} metadata for update check"
  git -C "${GIT_ROOT}" fetch --depth 1 origin "${OTA_BRANCH}" || fail "git fetch failed for ${GIT_ROOT}."

  local_head="$(git -C "${GIT_ROOT}" rev-parse HEAD)"
  remote_head="$(git -C "${GIT_ROOT}" rev-parse FETCH_HEAD)"
  current_ref="$(effective_local_ref || true)"
  [[ -n "${current_ref}" ]] || current_ref="${local_head}"
  current_version="$(read_version_file "${GIT_ROOT}/version.txt")"
  remote_version="$(git -C "${GIT_ROOT}" show FETCH_HEAD:version.txt 2>/dev/null | sed -n '1{s/[[:space:]]*$//;p;q;}' || true)"
  [[ -n "${remote_version}" ]] || remote_version="${current_version}"

  if [[ "${current_ref}" == "${remote_head}" ]]; then
    emit_check_result "up-to-date" "${current_version}" "${remote_version}"
    return 1
  fi

  emit_check_result "update-available" "${current_version}" "${remote_version}"
  return 0
}

clone_repo() {
  if [[ -n "${OTA_TOKEN}" ]]; then
    local owner auth_header
    owner="${OTA_REPO%%/*}"
    auth_header="$(printf '%s:%s' "${owner}" "${OTA_TOKEN}" | base64 | tr -d '\n')"
    if ! git -c "http.extraHeader=AUTHORIZATION: basic ${auth_header}" \
      clone --depth 1 --branch "${OTA_BRANCH}" "${CLONE_URL}" "${CLONE_DIR}"
    then
      fail "GitHub clone failed. Verify OTA_REPO, OTA_BRANCH, and that OTA_TOKEN has private-repo read access."
    fi
    return
  fi

  if ! git clone --depth 1 --branch "${OTA_BRANCH}" "${CLONE_URL}" "${CLONE_DIR}"; then
    fail "GitHub clone failed. Set OTA_TOKEN for a private repo or verify OTA_REPO and OTA_BRANCH."
  fi
}

detect_source_root() {
  local candidate
  local -a candidates=()

  if [[ -n "${OTA_PATH_IN_REPO}" ]]; then
    candidates+=("${CLONE_DIR}/${OTA_PATH_IN_REPO}")
  fi

  candidates+=(
    "${CLONE_DIR}/release"
    "${CLONE_DIR}/Xiphias/release"
    "${CLONE_DIR}"
    "${CLONE_DIR}/Xiphias"
  )

  for candidate in "${candidates[@]}"; do
    if [[ -d "${candidate}/gamehub-console" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

dir_changed() {
  local src="$1"
  local dst="$2"
  shift 2

  if [[ ! -d "${src}" ]]; then
    return 1
  fi

  if [[ ! -d "${dst}" ]]; then
    return 0
  fi

  rsync -ain --delete "$@" "${src}/" "${dst}/" | grep -q .
}

file_changed() {
  local src="$1"
  local dst="$2"

  if [[ ! -f "${src}" ]]; then
    return 1
  fi

  if [[ ! -f "${dst}" ]]; then
    return 0
  fi

  ! cmp -s "${src}" "${dst}"
}

managed_paths_changed() {
  local src_root="$1"
  local dst_root="$2"

  dir_changed "${src_root}/gamehub-console" "${dst_root}/gamehub-console" \
    --exclude '/console.env' \
    --exclude '/logs/' \
    --exclude '/__pycache__/' \
    --exclude '*.pyc' && return 0
  dir_changed "${src_root}/.icons" "${dst_root}/.icons" && return 0
  dir_changed "${src_root}/.config/openbox" "${dst_root}/.config/openbox" && return 0
  dir_changed "${src_root}/.config/autostart" "${dst_root}/.config/autostart" && return 0
  dir_changed "${src_root}/.config/onboard" "${dst_root}/.config/onboard" && return 0
  dir_changed "${src_root}/.local/share/onboard" "${dst_root}/.local/share/onboard" && return 0
  file_changed "${src_root}/.xinitrc" "${dst_root}/.xinitrc" && return 0

  return 1
}

path_requires_live_deploy() {
  local path="$1"

  case "${path}" in
    release/gamehub-console/*|release/.icons/*|release/.config/openbox/*|release/.config/autostart/*|release/.config/onboard/*|release/.local/share/onboard/*|release/.xinitrc|version.txt)
      return 0
      ;;
  esac

  return 1
}

remote_repo_changes_require_deploy() {
  local repo_root remote_head merge_base changed_path is_shallow

  repo_root="$(worktree_repo_root)"
  [[ -n "${repo_root}" ]] || return 2
  [[ "${repo_root}" == "${GIT_ROOT}" ]] || return 2

  log "Fetching ${OTA_BRANCH} metadata for deploy safety check"
  git -C "${GIT_ROOT}" fetch origin "${OTA_BRANCH}" >/dev/null 2>&1 || return 2

  remote_head="$(git -C "${GIT_ROOT}" rev-parse FETCH_HEAD 2>/dev/null || true)"
  [[ -n "${remote_head}" ]] || return 2

  is_shallow="$(git -C "${GIT_ROOT}" rev-parse --is-shallow-repository 2>/dev/null || true)"
  if [[ "${is_shallow}" == "true" ]]; then
    git -C "${GIT_ROOT}" fetch --unshallow origin "${OTA_BRANCH}" >/dev/null 2>&1 || return 2
    remote_head="$(git -C "${GIT_ROOT}" rev-parse FETCH_HEAD 2>/dev/null || true)"
    [[ -n "${remote_head}" ]] || return 2
  fi

  merge_base="$(git -C "${GIT_ROOT}" merge-base HEAD FETCH_HEAD 2>/dev/null || true)"
  [[ -n "${merge_base}" ]] || return 2

  while IFS= read -r changed_path; do
    [[ -n "${changed_path}" ]] || continue
    if path_requires_live_deploy "${changed_path}"; then
      return 0
    fi
  done < <(git -C "${GIT_ROOT}" diff --name-only "${merge_base}" FETCH_HEAD)

  return 1
}

check_cloned_updates() {
  local src_root="$1"
  local repo_root="$2"
  local current_ref remote_head current_version remote_version

  current_version="$(read_version_file "${GIT_ROOT}/version.txt")"
  remote_version="$(read_version_file "${repo_root}/version.txt")"
  current_ref="$(effective_local_ref || true)"
  remote_head="$(repo_head "${repo_root}")"

  if [[ -n "${current_ref}" && -n "${remote_head}" ]]; then
    if [[ "${current_ref}" == "${remote_head}" ]]; then
      emit_check_result "up-to-date" "${current_version}" "${remote_version}"
      return 1
    fi

    emit_check_result "update-available" "${current_version}" "${remote_version}"
    return 0
  fi

  if managed_paths_changed "${src_root}" "${LIVE_ROOT}" || file_changed "${repo_root}/version.txt" "${GIT_ROOT}/version.txt"; then
    emit_check_result "update-available" "${current_version}" "${remote_version}"
    return 0
  fi

  emit_check_result "up-to-date" "${current_version}" "${remote_version}"
  return 1
}

sync_dir() {
  local src="$1"
  local dst="$2"
  shift 2

  if [[ ! -d "${src}" ]]; then
    log "Skipping missing directory ${src}"
    return 0
  fi

  mkdir -p "${dst}"
  rsync -a --delete "$@" "${src}/" "${dst}/"
}

sync_file() {
  local src="$1"
  local dst="$2"

  if [[ ! -f "${src}" ]]; then
    log "Skipping missing file ${src}"
    return 0
  fi

  mkdir -p "$(dirname "${dst}")"
  rsync -a "${src}" "${dst}"
}

sync_managed_paths() {
  local src_root="$1"
  local dst_root="$2"

  sync_dir "${src_root}/gamehub-console" "${dst_root}/gamehub-console" \
    --exclude '/console.env' \
    --exclude '/logs/' \
    --exclude '/__pycache__/' \
    --exclude '*.pyc'
  sync_dir "${src_root}/.icons" "${dst_root}/.icons"
  sync_dir "${src_root}/.config/openbox" "${dst_root}/.config/openbox"
  sync_dir "${src_root}/.config/autostart" "${dst_root}/.config/autostart"
  sync_dir "${src_root}/.config/onboard" "${dst_root}/.config/onboard"
  sync_dir "${src_root}/.local/share/onboard" "${dst_root}/.local/share/onboard"
  sync_file "${src_root}/.xinitrc" "${dst_root}/.xinitrc"
}

sync_release_payload() {
  local src_root="$1"
  local dst_root="$2"

  sync_dir "${src_root}" "${dst_root}" \
    --exclude '/gamehub-console/console.env' \
    --exclude '/gamehub-console/logs/' \
    --exclude '/gamehub-console/__pycache__/' \
    --exclude '*.pyc'
}

apply_system_files() {
  log "Installing system files from ${LIVE_ROOT}/gamehub-console/files"
  sudo install -m 644 \
    "${LIVE_ROOT}/gamehub-console/files/knf-kiosk.service" \
    /etc/systemd/system/knf-kiosk.service
  sudo install -d -m 755 /etc/systemd/user-environment-generators
  sudo install -m 755 \
    "${LIVE_ROOT}/gamehub-console/files/90-xiphias-release-home" \
    /etc/systemd/user-environment-generators/90-xiphias-release-home
  sudo install -m 644 \
    "${LIVE_ROOT}/gamehub-console/files/gamehub-console-backup.cron" \
    /etc/cron.d/gamehub-console-backup
  sudo install -m 440 \
    "${LIVE_ROOT}/gamehub-console/files/gamehub-console-sudoers" \
    /etc/sudoers.d/gamehub-console
  sudo visudo -c -f /etc/sudoers.d/gamehub-console
  sudo systemctl daemon-reload
  if [[ -d "/run/user/$(id -u)" ]]; then
    sudo -u "$(id -un)" XDG_RUNTIME_DIR="/run/user/$(id -u)" systemctl --user daemon-reload || true
  fi
}

if (( CHECK_ONLY )); then
  CHECK_RESULT=0
  if check_worktree_updates; then
    CHECK_RESULT=0
  else
    CHECK_RESULT=$?
  fi

  if (( CHECK_RESULT == 0 )); then
    exit 10
  fi
  if (( CHECK_RESULT == 1 )); then
    exit 0
  fi

  clone_repo
  SOURCE_ROOT="$(detect_source_root)" || fail "Could not find a deploy root with gamehub-console in ${OTA_REPO}. Set OTA_PATH_IN_REPO if the repo layout is custom."
  if check_cloned_updates "${SOURCE_ROOT}" "${CLONE_DIR}"; then
    exit 10
  fi
  exit 0
fi

WORKTREE_REMOTE_STATUS=2
WORKTREE_REMOTE_HEAD=""
WORKTREE_HEAD_BEFORE=""
WORKTREE_HEAD_AFTER=""
WORKTREE_HEAD_CHANGED=0

if [[ "$(worktree_repo_root)" == "${GIT_ROOT}" ]]; then
  WORKTREE_HEAD_BEFORE="$(repo_head "${GIT_ROOT}")"
  if remote_repo_changes_require_deploy; then
    WORKTREE_REMOTE_STATUS=0
  else
    WORKTREE_REMOTE_STATUS=$?
  fi
  WORKTREE_REMOTE_HEAD="$(git -C "${GIT_ROOT}" rev-parse FETCH_HEAD 2>/dev/null || true)"
  if (( WORKTREE_REMOTE_STATUS == 0 )) && [[ -n "${WORKTREE_HEAD_BEFORE}" && -n "${WORKTREE_REMOTE_HEAD}" ]] && (( ! SKIP_BACKUP )) && [[ "${WORKTREE_HEAD_BEFORE}" != "${WORKTREE_REMOTE_HEAD}" ]]; then
    log "Building rollback backup from the live kiosk tree"
    bash "${LIVE_ROOT}/gamehub-console/backup_rollback_zip.sh"
  fi
fi

if SOURCE_ROOT="$(prepare_worktree_source_root)"; then
  SOURCE_REPO_ROOT="${GIT_ROOT}"
  SOURCE_FROM_WORKTREE=1
  WORKTREE_HEAD_AFTER="$(repo_head "${GIT_ROOT}")"
  if [[ -n "${WORKTREE_HEAD_BEFORE}" && -n "${WORKTREE_HEAD_AFTER}" && "${WORKTREE_HEAD_BEFORE}" != "${WORKTREE_HEAD_AFTER}" ]]; then
    WORKTREE_HEAD_CHANGED=1
  fi
else
  if [[ "$(worktree_repo_root)" == "${GIT_ROOT}" ]]; then
    fail "Install Update requires a clean ${GIT_ROOT} git worktree on ${OTA_BRANCH} so it can fetch origin and pull the latest changes first."
  fi
  clone_repo
  SOURCE_ROOT="$(detect_source_root)" || fail "Could not find a deploy root with gamehub-console in ${OTA_REPO}. Set OTA_PATH_IN_REPO if the repo layout is custom."
  SOURCE_REPO_ROOT="${CLONE_DIR}"
  SOURCE_FROM_WORKTREE=0
fi

log "Using source root ${SOURCE_ROOT}"

LOCAL_WORKTREE_PRESENT=0
if [[ "$(worktree_repo_root)" == "${GIT_ROOT}" ]]; then
  LOCAL_WORKTREE_PRESENT=1
fi

REMOTE_HEAD="$(repo_head "${SOURCE_REPO_ROOT}")"
CURRENT_VERSION="$(read_version_file "${GIT_ROOT}/version.txt")"
REMOTE_VERSION="$(read_version_file "${SOURCE_REPO_ROOT}/version.txt")"

RELEASE_SYNC_REQUIRED=0
if (( ! SOURCE_FROM_WORKTREE )) && (( ! LOCAL_WORKTREE_PRESENT )); then
  RELEASE_SYNC_REQUIRED=1
fi

if (( RELEASE_SYNC_REQUIRED )); then
  log "Syncing GitHub snapshot into ${RELEASE_ROOT}"
  sync_release_payload "${SOURCE_ROOT}" "${RELEASE_ROOT}"
fi

if (( LOCAL_WORKTREE_PRESENT )) && (( ! SOURCE_FROM_WORKTREE )); then
  REMOTE_DEPLOY_REQUIRED=2
  if remote_repo_changes_require_deploy; then
    REMOTE_DEPLOY_REQUIRED=0
  else
    REMOTE_DEPLOY_REQUIRED=$?
  fi

  if (( REMOTE_DEPLOY_REQUIRED == 1 )); then
    log "Remote repo changes do not touch managed kiosk paths"
    write_state_commit "${REMOTE_HEAD}" "${REMOTE_VERSION}"
    emit_deploy_result "no-live-change" "${CURRENT_VERSION}" "${REMOTE_VERSION}"
    exit 0
  fi

  if (( REMOTE_DEPLOY_REQUIRED == 0 )); then
    fail "Local git worktree cannot be fast-forwarded safely; commit, stash, or pull manually before installing software updates."
  fi

  fail "Could not evaluate remote changes safely; resolve the local git worktree before installing software updates."
fi

LIVE_CHANGE_REQUIRED=0
if (( SOURCE_FROM_WORKTREE )) && [[ "${LIVE_ROOT}" == "${RELEASE_ROOT}" ]]; then
  if (( WORKTREE_HEAD_CHANGED )) && (( WORKTREE_REMOTE_STATUS == 0 )); then
    LIVE_CHANGE_REQUIRED=1
  fi
elif managed_paths_changed "${SOURCE_ROOT}" "${LIVE_ROOT}" || file_changed "${SOURCE_REPO_ROOT}/version.txt" "${GIT_ROOT}/version.txt"; then
  LIVE_CHANGE_REQUIRED=1
fi

if (( ! LIVE_CHANGE_REQUIRED )); then
  log "No managed kiosk changes to deploy"
  write_state_commit "${REMOTE_HEAD}" "${REMOTE_VERSION}"
  emit_deploy_result "no-live-change" "${CURRENT_VERSION}" "${REMOTE_VERSION}"
  exit 0
fi

if (( ! SKIP_BACKUP )); then
  if (( ! SOURCE_FROM_WORKTREE )) || [[ "${LIVE_ROOT}" != "${RELEASE_ROOT}" ]]; then
    log "Building rollback backup from the live kiosk tree"
    bash "${LIVE_ROOT}/gamehub-console/backup_rollback_zip.sh"
  fi
fi

if (( ! SOURCE_FROM_WORKTREE )) && (( ! RELEASE_SYNC_REQUIRED )); then
  log "Syncing managed GitHub paths into ${RELEASE_ROOT}"
  sync_managed_paths "${SOURCE_ROOT}" "${RELEASE_ROOT}"
fi

if [[ "${LIVE_ROOT}" != "${RELEASE_ROOT}" ]]; then
  log "Deploying managed kiosk paths into ${LIVE_ROOT}"
  sync_managed_paths "${RELEASE_ROOT}" "${LIVE_ROOT}"
else
  log "Live kiosk tree is ${RELEASE_ROOT}; no separate deploy sync is required"
fi

if [[ "${SOURCE_REPO_ROOT}/version.txt" != "${GIT_ROOT}/version.txt" ]]; then
  sync_file "${SOURCE_REPO_ROOT}/version.txt" "${GIT_ROOT}/version.txt"
fi

if (( APPLY_SYSTEM_FILES )); then
  apply_system_files
fi

if (( RESTART_KIOSK )); then
  log "Restarting kiosk processes"
  bash "${LIVE_ROOT}/gamehub-console/restart_kiosk.sh"
fi

INSTALLED_VERSION="$(read_version_file "${GIT_ROOT}/version.txt")"
write_state_commit "${REMOTE_HEAD}" "${INSTALLED_VERSION}"
emit_deploy_result "deployed" "${INSTALLED_VERSION}" "${REMOTE_VERSION}"
log "OTA deploy finished"
