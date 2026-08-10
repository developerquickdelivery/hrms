#!/usr/bin/env bash
# Finish QD HRMS install after partial setup (Redis was down / new-app aborted).
# Run inside WSL as user qd:
#   bash /mnt/c/anw/work/QD-HRMS/scripts/03_finish_install.sh
set -euo pipefail

export HOME="${HOME:-/home/qd}"
export PATH="${HOME}/.local/bin:${PATH}"
BENCH_DIR="${HOME}/frappe-bench"
SITE_NAME="${SITE_NAME:-qd.local}"
APP_NAME="qd_hrms"

cd "${BENCH_DIR}"

echo "==> Starting Redis (queue + cache) for install..."
# Stop any stale redis on bench ports, then start from bench config
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes || true
fi
if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes || true
fi
sleep 2
redis-cli -p 11000 ping || { echo "Redis queue not on 11000"; exit 1; }
redis-cli -p 13000 ping 2>/dev/null || redis-cli -p 11000 ping

echo "==> Ensuring MariaDB is up..."
sudo service mariadb start || sudo service mysql start || true

echo "==> Installed apps now:"
bench --site "${SITE_NAME}" list-apps || true

echo "==> Installing / repairing erpnext..."
bench --site "${SITE_NAME}" install-app erpnext || true

echo "==> Installing / repairing hrms..."
bench --site "${SITE_NAME}" install-app hrms || true

echo "==> Creating custom app ${APP_NAME} (if missing)..."
if [[ ! -d "apps/${APP_NAME}" ]]; then
  # Prompts: title, description, publisher, email, license, create GitHub workflow
  printf '%s\n' \
    "Quick Delivery HRMS" \
    "HRMS customizations for Quick Delivery Service" \
    "Quick Delivery Service" \
    "qd@quickdelivery.local" \
    "mit" \
    "N" | bench new-app "${APP_NAME}"
fi

bench --site "${SITE_NAME}" install-app "${APP_NAME}" || true

echo "==> Enabling developer mode..."
bench --site "${SITE_NAME}" set-config developer_mode 1
bench --site "${SITE_NAME}" clear-cache
bench use "${SITE_NAME}"

echo ""
echo "============================================================"
echo " FINISH COMPLETE"
echo " Installed apps:"
bench --site "${SITE_NAME}" list-apps
echo ""
echo " Start the stack (keep this terminal open):"
echo "   cd ${BENCH_DIR} && bench start"
echo " Then open http://127.0.0.1:8000"
echo "   User: Administrator"
echo "   Pass: admin"
echo "============================================================"
