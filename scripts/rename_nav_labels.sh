#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/frappe-bench

# Remove old workspace JSON folders that used QD prefix
rm -rf \
  apps/qd_hrms/qd_hrms/quick_delivery_hrms/workspace/qd_executive_dashboard \
  apps/qd_hrms/qd_hrms/quick_delivery_hrms/workspace/qd_hr_dashboard \
  apps/qd_hrms/qd_hrms/quick_delivery_hrms/workspace/qd_manager_dashboard \
  apps/qd_hrms/qd_hrms/quick_delivery_hrms/workspace/qd_employee_dashboard

bench --site qd.local execute qd_hrms.setup.dashboards.run
bench --site qd.local execute qd_hrms.setup.attendance.run
bench --site qd.local execute qd_hrms.setup.organization.run
bench --site qd.local execute qd_hrms.setup.employee_management.run
bench --site qd.local execute qd_hrms.setup.recruitment.run
bench --site qd.local execute qd_hrms.setup.onboarding.run
bench --site qd.local execute qd_hrms.setup.navigation.run
bench --site qd.local clear-cache

echo "=== Workspaces ==="
bench --site qd.local mariadb -N -e "SELECT name FROM tabWorkspace WHERE module='Quick Delivery HRMS' OR name LIKE '%Dashboard%' ORDER BY name;"
