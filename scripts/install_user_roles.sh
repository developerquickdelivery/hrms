#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench
bench --site qd.local migrate
bench build --app qd_hrms
bench --site qd.local execute qd_hrms.setup.users.run
bench --site qd.local clear-cache
bench --site qd.local mariadb -N -e "SELECT name FROM \`tabRole Profile\` ORDER BY name;"
