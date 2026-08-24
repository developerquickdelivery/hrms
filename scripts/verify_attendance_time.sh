#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "${HOME}/frappe-bench"
bench --site qd.local execute qd_hrms.setup.attendance_time.verify
