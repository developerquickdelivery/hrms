#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench
bench --site qd.local mariadb -N -e "SELECT name FROM tabWorkspace ORDER BY name;" | head -80
