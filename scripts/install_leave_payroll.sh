#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench

bench --site qd.local migrate
bench build --app qd_hrms
bench --site qd.local execute qd_hrms.setup.leave.run
bench --site qd.local execute qd_hrms.setup.payroll.run
bench --site qd.local execute qd_hrms.setup.dashboards.run
bench --site qd.local clear-cache

echo "=== Leave types ==="
bench --site qd.local mariadb -N -e "SELECT name FROM \`tabLeave Type\` WHERE name IN ('Annual Leave','Sick Leave','Unpaid Leave','Emergency Leave') ORDER BY name;"
echo "=== Salary components ==="
bench --site qd.local mariadb -N -e "SELECT name FROM \`tabSalary Component\` WHERE name IN ('Basic','Transport Allowance','Overtime','Income Tax','Pension Employee','Pension Employer') ORDER BY name;"
echo "=== Role / profile ==="
bench --site qd.local mariadb -N -e "SELECT name FROM tabRole WHERE name='QD Payroll Officer';"
bench --site qd.local mariadb -N -e "SELECT name FROM \`tabRole Profile\` WHERE name='Payroll Officer';"
