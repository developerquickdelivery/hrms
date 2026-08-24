#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

# Keep logos already on the bench copy
cp -a "${SRC}/qd_hrms/setup/people.py" "${DEST}/qd_hrms/setup/people.py"
cp -a "${SRC}/qd_hrms/setup/install.py" "${DEST}/qd_hrms/setup/install.py"
cp -a "${SRC}/qd_hrms/employee.py" "${DEST}/qd_hrms/employee.py"
cp -a "${SRC}/qd_hrms/hooks.py" "${DEST}/qd_hrms/hooks.py"
mkdir -p "${DEST}/qd_hrms/public/js"
cp -a "${SRC}/qd_hrms/public/js/employee.js" "${DEST}/qd_hrms/public/js/employee.js"
cp -a "${SRC}/qd_hrms/public/js/designation.js" "${DEST}/qd_hrms/public/js/designation.js"
cp -a "${SRC}/qd_hrms/public/js/salary_structure_assignment.js" "${DEST}/qd_hrms/public/js/salary_structure_assignment.js"

if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
fi
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
fi

bench --site qd.local execute qd_hrms.setup.people.run
bench --site qd.local clear-cache
bench --site qd.local mariadb -e "select dt, fieldname, label, fieldtype from tabCustom Field where fieldname like 'custom_qd_%' order by dt, idx;"
echo DONE
