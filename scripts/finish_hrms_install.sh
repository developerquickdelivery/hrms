#!/usr/bin/env bash
# Finish HRMS install on qd.local after Redis dropped.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

BENCH_DIR="${HOME}/frappe-bench"
SITE_NAME="${SITE_NAME:-qd.local}"

cd "${BENCH_DIR}"

echo "==> Starting bench Redis (cache + queue)..."
if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes
fi
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes
fi
sleep 1
ss -ltn | grep -E '13000|11000' || true

echo "==> Current installed apps:"
bench --site "${SITE_NAME}" list-apps || true

echo "==> Installing / completing hrms on ${SITE_NAME}..."
if bench --site "${SITE_NAME}" install-app hrms; then
  echo "==> install-app succeeded"
else
  echo "==> install-app reported failure or already installed; running migrate + after_install"
  bench --site "${SITE_NAME}" migrate
  bench --site "${SITE_NAME}" execute hrms.install.after_install || true
fi

echo "==> Building HRMS assets (if needed)..."
bench build --app hrms || true
bench --site "${SITE_NAME}" clear-cache

echo "==> Verification:"
echo "--- apps dir ---"
ls apps
echo "--- apps.txt ---"
cat sites/apps.txt
echo "--- installed ---"
bench --site "${SITE_NAME}" list-apps

echo ""
echo "============================================================"
echo " HRMS READY (standard, no customizations)"
echo "============================================================"
echo " Restart: cd ~/frappe-bench && bench start"
echo " URL: http://127.0.0.1:8000"
echo "============================================================"
