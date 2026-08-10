#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench

# Remove any workspaces created from title rename
bench --site qd.local mariadb -e "DELETE FROM tabWorkspace WHERE name LIKE 'Quick Delivery%';"

bench --site qd.local execute qd_hrms.setup.dashboards.run
bench --site qd.local execute qd_hrms.setup.navigation.run
bench --site qd.local clear-cache

bench --site qd.local mariadb -N -e "SELECT name FROM tabWorkspace WHERE name LIKE 'QD%' OR name LIKE 'Quick%' ORDER BY name;"
