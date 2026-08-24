#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "${HOME}/frappe-bench"
python3 - <<'PY'
import frappe
from frappe.utils.bench_helper import get_app_groups  # noqa: F401
PY
bench --site qd.local execute frappe.db.sql --kwargs '{"query": "select dt, fieldname, label, fieldtype from `tabCustom Field` where fieldname like \\\"custom_qd_%\\\" order by dt, fieldname", "as_dict": 1}'
