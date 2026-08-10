#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench

echo "=== QD Workspaces ==="
bench --site qd.local mariadb -N -e "SELECT name FROM tabWorkspace WHERE name LIKE 'QD%' ORDER BY name;"

echo "=== Attendance DocTypes ==="
bench --site qd.local mariadb -N -e "SELECT name FROM tabDocType WHERE name IN ('QD Biometric Device');"

echo "=== QD Shifts ==="
bench --site qd.local mariadb -N -e "SELECT name FROM \`tabShift Type\` WHERE name LIKE 'QD%';"
