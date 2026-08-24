#!/usr/bin/env bash
set -euo pipefail
echo "=== processes on 11000 / 13000 ==="
ss -ltnp 2>/dev/null | grep -E ':11000|:13000' || true
fuser -v 11000/tcp 13000/tcp 2>&1 || true
echo "=== redis / honcho / bench leftovers ==="
pgrep -af 'redis-server|honcho|frappe|socketio' || true
echo "=== freeing ports ==="
# Kill whatever holds the bench Redis ports (safe for local bench only)
for port in 11000 13000; do
  pids=$(ss -ltnp 2>/dev/null | awk -v p=":$port" '$4 ~ p {print}' | grep -oP 'pid=\K[0-9]+' || true)
  if [ -n "${pids:-}" ]; then
    echo "Killing PIDs on $port: $pids"
    kill $pids 2>/dev/null || true
    sleep 1
    kill -9 $pids 2>/dev/null || true
  fi
done
# Also stop orphan redis-server started by prior bench
pkill -f 'redis-server .*config/redis' 2>/dev/null || true
sleep 1
echo "=== after ==="
ss -ltnp 2>/dev/null | grep -E ':11000|:13000' || echo "ports free"
