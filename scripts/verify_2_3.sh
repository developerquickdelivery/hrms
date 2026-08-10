#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench

bench --site qd.local mariadb -N -e "SELECT name FROM tabWorkspace WHERE name LIKE 'QD%' ORDER BY name;"
bench --site qd.local mariadb -N -e "SELECT name FROM tabDocType WHERE name IN ('QD Employment Event','QD Employee Document');"
