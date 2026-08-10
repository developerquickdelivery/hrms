#!/usr/bin/env bash
# Ensure MariaDB is up, then start bench (daily use)
set -euo pipefail
export HOME=/home/qd
export PATH=/home/qd/.local/bin:/usr/local/bin:/usr/bin:/bin

sudo service mariadb start 2>/dev/null || sudo service mysql start 2>/dev/null || true
for i in 1 2 3 4 5 6 7 8 9 10; do
  if ss -ltn 2>/dev/null | grep -q ':3306'; then
    echo "MariaDB OK on 3306"
    break
  fi
  echo "Waiting for MariaDB... ($i)"
  sleep 2
done

fuser -k 8000/tcp 9000/tcp 11000/tcp 13000/tcp 2>/dev/null || true
sleep 1
cd /home/qd/frappe-bench
echo "Open http://127.0.0.1:8000  (Administrator / admin)"
echo "Dashboards: search QD Executive / QD HR / QD Manager / QD Employee"
exec bench start
