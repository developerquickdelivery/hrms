#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

cp -a "${SRC}/qd_hrms/public/css/qd_hrms.css" "${DEST}/qd_hrms/public/css/qd_hrms.css"
cp -a "${SRC}/qd_hrms/public/js/qd_hrms.js" "${DEST}/qd_hrms/public/js/qd_hrms.js"
cp -a "${SRC}/qd_hrms/setup/branding.py" "${DEST}/qd_hrms/setup/branding.py"
cp -a "${SRC}/qd_hrms/hooks.py" "${DEST}/qd_hrms/hooks.py"

if [[ ! -f "${DEST}/qd_hrms/public/images/qd-logo.png" ]]; then
  if [[ -f "${DEST}/qd_hrms/public/images/qd-splash.png" ]]; then
    cp "${DEST}/qd_hrms/public/images/qd-splash.png" "${DEST}/qd_hrms/public/images/qd-logo.png"
  fi
fi

ls -la "${DEST}/qd_hrms/public/images/"
ls -la sites/assets/qd_hrms/images/ 2>/dev/null || true

if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
fi

bench --site qd.local execute qd_hrms.setup.branding.run
bench --site qd.local clear-cache
echo DONE
