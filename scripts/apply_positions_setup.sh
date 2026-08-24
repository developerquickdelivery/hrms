#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

rsync -a \
	--exclude public/images \
	--exclude __pycache__ \
	--exclude '*.pyc' \
	"${SRC}/qd_hrms/" "${DEST}/qd_hrms/"

bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.positions.run
bench --site qd.local clear-cache
echo "Position setup applied."

