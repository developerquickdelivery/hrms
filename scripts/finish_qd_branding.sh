#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "${HOME}/frappe-bench"

if ! grep -qx "qd_hrms" sites/apps.txt; then
  printf '\nqd_hrms\n' >> sites/apps.txt
fi
python3 - <<'PY'
from pathlib import Path
p = Path("sites/apps.txt")
lines = [ln.strip() for ln in p.read_text().splitlines() if ln.strip()]
if "qd_hrms" not in lines:
    lines.append("qd_hrms")
p.write_text("\n".join(lines) + "\n")
print("apps.txt", lines)
PY

if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
fi
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
fi

echo "==> install-app"
bench --site qd.local install-app qd_hrms

echo "==> branding"
bench --site qd.local execute qd_hrms.setup.branding.run

echo "==> build"
bench build --app qd_hrms
bench --site qd.local clear-cache

echo "==> list-apps"
bench --site qd.local list-apps
ls -la apps/qd_hrms/qd_hrms/public/images
echo DONE
