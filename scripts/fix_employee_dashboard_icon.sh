#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench
bench --site qd.local execute qd_hrms.setup.dashboards.run
bench --site qd.local clear-cache
bench --site qd.local mariadb -N -e "SELECT name, icon FROM tabWorkspace WHERE name IN ('Employee Dashboard','HR Dashboard','Manager Dashboard','Executive Dashboard') ORDER BY name;"
