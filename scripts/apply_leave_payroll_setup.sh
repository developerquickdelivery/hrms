#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

rsync -a --exclude public/images "${SRC}/qd_hrms/" "${DEST}/qd_hrms/"

bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.leave_payroll.run
bench --site qd.local clear-cache
echo DONE
