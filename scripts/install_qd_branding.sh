#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
LOGO_SRC="/mnt/c/Users/User/.cursor/projects/c-anw-work-QD-HRMS/assets/c__Users_User_AppData_Roaming_Cursor_User_workspaceStorage_d6d771f62f03e1fff76eaf1d63b366d0_images_image-57573245-8f40-47e9-834d-d881182b7b17.png"
DEST="${BENCH}/apps/qd_hrms"

cd "${BENCH}"

echo "==> Copy app into bench"
rm -rf "${DEST}"
mkdir -p "${DEST}"
cp -a "${SRC}/." "${DEST}/"

echo "==> Copy splash logo"
mkdir -p "${DEST}/qd_hrms/public/images"
if [[ -f "${LOGO_SRC}" ]]; then
  cp "${LOGO_SRC}" "${DEST}/qd_hrms/public/images/qd-splash.png"
  cp "${LOGO_SRC}" "${DEST}/qd_hrms/public/images/qd-logo.png"
else
  echo "WARNING: splash source not found at ${LOGO_SRC}"
fi

echo "==> Install python package"
./env/bin/pip install -e "${DEST}" --quiet

echo "==> Ensure Redis"
if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
fi
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
fi
sleep 1

echo "==> Install app on site"
bench --site qd.local install-app qd_hrms || true

echo "==> Apply branding"
bench --site qd.local execute qd_hrms.setup.branding.run

echo "==> Build assets"
bench build --app qd_hrms
bench --site qd.local clear-cache

echo "==> Verify"
bench --site qd.local list-apps
ls -la "${DEST}/qd_hrms/public/images"

echo "DONE"
