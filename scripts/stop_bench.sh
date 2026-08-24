#!/usr/bin/env bash
# Stop a running `bench start` (honcho) and release its Redis ports.
set -uo pipefail

# Bracketed patterns keep pgrep/pkill from matching this script's own cmdline.
MASTER=$(pgrep -f 'honch[o] start' | head -1 || true)

if [ -n "${MASTER:-}" ]; then
  PGID=$(ps -o pgid= -p "${MASTER}" 2>/dev/null | tr -d ' ')
  echo "Stopping bench (honcho pid ${MASTER}, pgid ${PGID:-unknown})"
  if [ -n "${PGID:-}" ]; then
    kill -TERM "-${PGID}" 2>/dev/null || true
    sleep 6
    kill -KILL "-${PGID}" 2>/dev/null || true
  else
    kill -TERM "${MASTER}" 2>/dev/null || true
    sleep 6
    kill -KILL "${MASTER}" 2>/dev/null || true
  fi
else
  echo "No running bench found."
fi

sleep 1
bash "$(dirname "$0")/free_bench_redis.sh" || true

# honcho children can outlive the group kill; clear the orphans it leaves behind.
for pattern in 'bench_helpe[r] frappe serve' 'bench_helpe[r] frappe schedule' \
  'bench_helpe[r] frappe worker' 'bench_helpe[r] frappe watch' \
  'apps/frappe/socketi[o].js' 'esbuil[d] --service'; do
  pids=$(pgrep -f "${pattern}" || true)
  if [ -n "${pids:-}" ]; then
    echo "Killing orphans (${pattern}): ${pids}"
    kill ${pids} 2>/dev/null || true
    sleep 1
    kill -9 ${pids} 2>/dev/null || true
  fi
done

sleep 1
echo "=== remaining bench processes ==="
pgrep -af 'honch[o]|bench_helpe[r]|redis-serve[r]|socketi[o].js' || echo "none"
echo "=== bench ports ==="
ss -ltn 2>/dev/null | grep -E ':11000|:13000|:8000|:9000' || echo "11000/13000/8000/9000 free"
