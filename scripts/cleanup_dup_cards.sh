#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench
bench --site qd.local mariadb -e "SET SQL_SAFE_UPDATES=0; DELETE FROM \`tabNumber Card\` WHERE name LIKE '%-1'; SET SQL_SAFE_UPDATES=1;"
bench --site qd.local clear-cache
bench --site qd.local mariadb -N -e "SELECT name FROM \`tabNumber Card\` WHERE module='Quick Delivery HRMS' ORDER BY name;"
