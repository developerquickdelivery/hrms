#!/usr/bin/env bash
# Apply Quick Delivery Organizational Setup (Departments, Grades, Designations, Positions, Leave Workflow)
# Usage:
#   bash scripts/apply_qd_organization.sh [site_name]
# Example:
#   bash scripts/apply_qd_organization.sh hrms.quickdelivery6484.com

set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"
BENCH_DIR="${BENCH_DIR:-${HOME}/frappe-bench}"
SITE_NAME="${1:-${SITE_NAME:-hrms.quickdelivery6484.com}}"

cd "${BENCH_DIR}"

echo "========================================================"
echo "Applying Quick Delivery Organizational Setup to: ${SITE_NAME}"
echo "========================================================"

# 1. Run migrations to ensure custom fields and DocTypes are in place
bench --site "${SITE_NAME}" migrate

# 2. Run the org_data setup module (Departments, Grades, Designations, Positions)
echo "Setting up Departments, Grades, Designations, and Positions..."
bench --site "${SITE_NAME}" execute qd_hrms.setup.org_data.run

# 3. Run the leave setup module (Leave Policy, Leave Types, 2-Level Workflow)
echo "Setting up Leave Workflows and Policies..."
bench --site "${SITE_NAME}" execute qd_hrms.setup.leave.run

# 4. Clear cache to refresh Desk & metadata
echo "Clearing cache..."
bench --site "${SITE_NAME}" clear-cache

echo "========================================================"
echo "Quick Delivery Organizational Setup completed successfully!"
echo "========================================================"
