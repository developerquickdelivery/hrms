#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

cp -a "${SRC}/qd_hrms/setup/requisition.py" "${DEST}/qd_hrms/setup/requisition.py"
cp -a "${SRC}/qd_hrms/setup/install.py" "${DEST}/qd_hrms/setup/install.py"
cp -a "${SRC}/qd_hrms/hooks.py" "${DEST}/qd_hrms/hooks.py"
mkdir -p "${DEST}/qd_hrms/public/js"
cp -a "${SRC}/qd_hrms/public/js/job_requisition.js" "${DEST}/qd_hrms/public/js/job_requisition.js"

if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
fi
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
fi

bench --site qd.local execute qd_hrms.setup.requisition.run
bench --site qd.local clear-cache
echo DONE
