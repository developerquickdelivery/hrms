#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench

bench --site qd.local mariadb -N -e "SELECT name FROM tabWorkspace WHERE name LIKE 'QD%' ORDER BY name;"
bench --site qd.local mariadb -N -e "SELECT name FROM tabDocType WHERE name IN ('QD Background Check');"
bench --site qd.local mariadb -N -e "SELECT name FROM tabRole WHERE name LIKE 'QD%';"
bench --site qd.local mariadb -N -e 'SELECT name FROM `tabNumber Card` WHERE name LIKE "QD Pending%";'
