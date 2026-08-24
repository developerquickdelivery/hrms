#!/usr/bin/env bash
# Reset WSL frappe-bench to a clean ERPNext-only site.
# Removes hrms + qd_hrms and recreates qd.local with no customizations.
# Does NOT touch git remotes or the Windows QD-HRMS repo remote status.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

BENCH_DIR="${HOME}/frappe-bench"
SITE_NAME="${SITE_NAME:-qd.local}"
ADMIN_PASS="${ADMIN_PASS:-admin}"
MYSQL_ROOT_PASS="${MYSQL_ROOT_PASS:-admin}"

echo "==> PATH: ${PATH}"
echo "==> which bench: $(command -v bench || true)"
cd "${BENCH_DIR}"

echo "==> [1] Stopping bench-related processes..."
pkill -f 'honcho' 2>/dev/null || true
pkill -f 'frappe serve' 2>/dev/null || true
pkill -f 'socketio' 2>/dev/null || true
sleep 2

echo "==> [2] Ensuring Redis (no sudo; MariaDB assumed already running)..."
# Avoid interactive sudo prompts when called from non-TTY automation.
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
  redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
fi
# System redis is optional; bench uses ports from common_site_config.json
sleep 1
if ! pgrep -x mariadbd >/dev/null 2>&1 && ! pgrep -x mysqld >/dev/null 2>&1; then
  echo "ERROR: MariaDB is not running. In your WSL terminal run: sudo service mariadb start"
  exit 1
fi

echo "==> [3] Dropping site ${SITE_NAME} (no backup)..."
if [[ -d "sites/${SITE_NAME}" ]]; then
  if ! bench drop-site "${SITE_NAME}" --force --db-root-password "${MYSQL_ROOT_PASS}" --no-backup; then
    if ! bench drop-site "${SITE_NAME}" --force --root-password "${MYSQL_ROOT_PASS}" --no-backup; then
      echo "bench drop-site failed; forcing directory removal"
      rm -rf "sites/${SITE_NAME}"
    fi
  fi
else
  echo "Site directory already gone"
fi

echo "==> [4] Removing qd_hrms and hrms apps from bench..."
if [[ -d apps/qd_hrms ]]; then
  bench remove-app qd_hrms --no-backup 2>/dev/null || {
    echo "Manual remove qd_hrms"
    rm -rf apps/qd_hrms
  }
fi
if [[ -d apps/hrms ]]; then
  bench remove-app hrms --no-backup 2>/dev/null || {
    echo "Manual remove hrms"
    rm -rf apps/hrms
  }
fi

# Ensure apps.txt / apps.json only list frappe + erpnext
python3 - <<'PY'
import json
import pathlib

sites = pathlib.Path("sites")
apps_txt = sites / "apps.txt"
existing = []
if apps_txt.exists():
    existing = [line.strip() for line in apps_txt.read_text().splitlines() if line.strip()]

ordered = []
for app in ("frappe", "erpnext"):
    if app in existing or (sites.parent / "apps" / app).exists():
        ordered.append(app)
for app in existing:
    if app not in ordered and app not in ("hrms", "qd_hrms") and (sites.parent / "apps" / app).exists():
        ordered.append(app)

apps_txt.write_text("\n".join(ordered) + "\n")
print("apps.txt =>", ordered)

apps_json = sites / "apps.json"
if apps_json.exists():
    data = json.loads(apps_json.read_text())
    for key in list(data.keys()):
        if key in ("hrms", "qd_hrms") or not (sites.parent / "apps" / key).exists():
            data.pop(key, None)
    apps_json.write_text(json.dumps(data, indent=4))
    print("apps.json keys =>", list(data.keys()))
PY

echo "==> [5] Skipping sudo DB listing (no interactive sudo)..."

echo "==> [6] Creating fresh site ${SITE_NAME}..."
if ! bench new-site "${SITE_NAME}" \
  --mariadb-root-password "${MYSQL_ROOT_PASS}" \
  --admin-password "${ADMIN_PASS}" \
  --no-mariadb-socket; then
  bench new-site "${SITE_NAME}" \
    --db-root-password "${MYSQL_ROOT_PASS}" \
    --admin-password "${ADMIN_PASS}"
fi

bench use "${SITE_NAME}"

echo "==> [7] Installing ERPNext only (no HRMS, no qd_hrms)..."
bench --site "${SITE_NAME}" install-app erpnext

echo "==> [8] Developer mode + clear cache + build..."
bench --site "${SITE_NAME}" set-config developer_mode 1
bench --site "${SITE_NAME}" clear-cache
bench build --app frappe --app erpnext

echo "==> [9] Final verification..."
echo "--- apps ---"
ls apps
echo "--- apps.txt ---"
cat sites/apps.txt
echo "--- installed apps ---"
bench --site "${SITE_NAME}" list-apps
echo "--- site config ---"
cat "sites/${SITE_NAME}/site_config.json"

echo ""
echo "============================================================"
echo " CLEAN ERPNext SETUP COMPLETE (no customizations)"
echo "============================================================"
echo " URL:  http://127.0.0.1:8000"
echo " Site: ${SITE_NAME}"
echo " User: Administrator / ${ADMIN_PASS}"
echo " Apps: frappe + erpnext only"
echo " Start: cd ~/frappe-bench && bench start"
echo "============================================================"
