#!/usr/bin/env bash
# Install standard ERPNext HRMS on the existing qd.local site.
# No customizations. Does not touch Windows git remotes.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

BENCH_DIR="${HOME}/frappe-bench"
SITE_NAME="${SITE_NAME:-qd.local}"
HRMS_BRANCH="${HRMS_BRANCH:-version-15}"

cd "${BENCH_DIR}"

echo "==> Current apps directory:"
ls apps
echo "==> Installed apps:"
bench --site "${SITE_NAME}" list-apps || true

if [[ ! -d apps/hrms ]]; then
  echo "==> Getting HRMS app (${HRMS_BRANCH})..."
  bench get-app hrms --branch "${HRMS_BRANCH}"
else
  echo "==> apps/hrms already present, skipping get-app"
fi

echo "==> Installing hrms on site ${SITE_NAME}..."
bench --site "${SITE_NAME}" install-app hrms

echo "==> Building HRMS assets..."
bench build --app hrms

echo "==> Clearing cache..."
bench --site "${SITE_NAME}" clear-cache

echo "==> Verification:"
echo "--- apps dir ---"
ls apps
echo "--- apps.txt ---"
cat sites/apps.txt
echo "--- installed ---"
bench --site "${SITE_NAME}" list-apps

echo ""
echo "============================================================"
echo " HRMS INSTALLED (standard, no customizations)"
echo "============================================================"
echo " Site: ${SITE_NAME}"
echo " Restart the running stack if needed (Ctrl+C, then bench start)"
echo "============================================================"
