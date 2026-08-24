#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "${HOME}/frappe-bench"
bench --site qd.local execute qd_hrms.setup.branding.run
python3 - <<'PY'
import os
base = "sites/assets/qd_hrms"
for p in [
    "css/qd_hrms.css",
    "css/qd_login.css",
    "js/qd_hrms.js",
    "js/qd_login.js",
    "images/qd-splash.png",
    "images/qd-mark.svg",
    "images/qd-favicon.png",
]:
    fp = os.path.join(base, p)
    print(("OK " if os.path.exists(fp) else "MISSING "), fp)
PY
bench --site qd.local mariadb -e "select field, value from tabSingles where doctype='Website Settings' and field in ('app_name','app_logo','favicon','splash_image');"
bench --site qd.local mariadb -e "select name, is_default from \`tabLetter Head\` where name='Quick Delivery';"
