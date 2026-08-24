#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
cd "${BENCH}"

# SCSS bundle must contain the CSS itself — esbuild @import of a sibling CSS 404s in /tmp.
mkdir -p "${SRC}/qd_hrms/public/scss" "${SRC}/qd_hrms/public/js"
cp -a "${SRC}/qd_hrms/public/css/qd_hrms.css" "${SRC}/qd_hrms/public/scss/qd_hrms.bundle.scss"
cp -a "${SRC}/qd_hrms/public/js/qd_hrms.js" "${SRC}/qd_hrms/public/js/qd_hrms.bundle.js"

rsync -a --exclude public/images "${SRC}/qd_hrms/" "${DEST}/qd_hrms/"

bench build --app qd_hrms
bench --site qd.local clear-cache
echo DONE
