#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "${HOME}/frappe-bench"

# Ensure Redis is up
redis-server config/redis_cache.conf --daemonize yes 2>/dev/null || true
redis-server config/redis_queue.conf --daemonize yes 2>/dev/null || true
sleep 1

echo "==> migrate"
bench --site qd.local migrate

echo "==> complete hrms after_install (idempotent / remaining patches)"
bench --site qd.local execute hrms.install.after_install

echo "==> clear-cache"
bench --site qd.local clear-cache

echo "==> list-apps"
bench --site qd.local list-apps

echo "DONE"
