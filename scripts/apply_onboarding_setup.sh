#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

rsync -a --exclude public/images "${SRC}/qd_hrms/" "${DEST}/qd_hrms/"

if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
fi
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
fi

bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.onboarding.run
bench --site qd.local clear-cache
echo DONE
