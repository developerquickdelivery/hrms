#!/usr/bin/env bash
# Deploy qd_hrms to a production bench site.
# Run on the VPS as the frappe user (or: sudo -u frappe -E bash this-script).
#
# Required env:
#   SITE_NAME=hrms.example.com
#   QD_HRMS_SRC=/path/to/qd_hrms_app   (or set QD_HRMS_GIT_URL)
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"
BENCH_DIR="${BENCH_DIR:-/home/frappe/frappe-bench}"
SITE_NAME="${SITE_NAME:-}"
QD_HRMS_SRC="${QD_HRMS_SRC:-}"
QD_HRMS_GIT_URL="${QD_HRMS_GIT_URL:-}"
QD_HRMS_BRANCH="${QD_HRMS_BRANCH:-main}"

if [[ "$(id -un)" != "frappe" && -z "${ALLOW_NON_FRAPPE_DEPLOY:-}" ]]; then
	echo "Run as user frappe (sudo -u frappe -E bash $0)"
	exit 1
fi

if [[ -z "${SITE_NAME}" ]]; then
	echo "Set SITE_NAME (e.g. hrms.example.com)"
	exit 1
fi

cd "${BENCH_DIR}"

if [[ -n "${QD_HRMS_GIT_URL}" ]]; then
	if [[ ! -d apps/qd_hrms ]]; then
		bench get-app qd_hrms "${QD_HRMS_GIT_URL}" --branch "${QD_HRMS_BRANCH}"
	else
		cd apps/qd_hrms
		git fetch --all --prune
		git checkout "${QD_HRMS_BRANCH}"
		git pull --ff-only origin "${QD_HRMS_BRANCH}" || true
		cd "${BENCH_DIR}"
	fi
elif [[ -n "${QD_HRMS_SRC}" ]]; then
	# QD_HRMS_SRC = repo folder qd_hrms_app/ (contains pyproject.toml + qd_hrms/)
	# Target must be apps/qd_hrms/qd_hrms so hooks.py lands at apps/qd_hrms/qd_hrms/hooks.py
	mkdir -p apps/qd_hrms/qd_hrms
	rsync -a --delete \
		--exclude __pycache__ \
		--exclude '*.pyc' \
		--exclude .git \
		"${QD_HRMS_SRC}/qd_hrms/" "apps/qd_hrms/qd_hrms/"
	if [[ -f "${QD_HRMS_SRC}/pyproject.toml" ]]; then
		cp "${QD_HRMS_SRC}/pyproject.toml" apps/qd_hrms/pyproject.toml
	fi
	# Ensure Python can import qd_hrms (hooks/setup live at app root)
	./env/bin/pip uninstall -y qd_hrms >/dev/null 2>&1 || true
	./env/bin/pip install -e ./apps/qd_hrms
else
	echo "Set QD_HRMS_SRC or QD_HRMS_GIT_URL"
	exit 1
fi

bench --site "${SITE_NAME}" set-maintenance-mode on
bench --site "${SITE_NAME}" install-app qd_hrms 2>/dev/null || true
bench --site "${SITE_NAME}" migrate
bench --site "${SITE_NAME}" execute qd_hrms.setup.verify_org.run || true
# Asset build can OOM on 8GB; prefer app-only build with capped Node heap
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}"
if ! bench build --app qd_hrms; then
	echo "WARN: bench build failed; linking public assets as fallback"
	mkdir -p sites/assets/qd_hrms
	rsync -a apps/qd_hrms/public/ sites/assets/qd_hrms/ || true
fi
bench --site "${SITE_NAME}" clear-cache
sudo supervisorctl restart all
sudo systemctl reload nginx || true
bench --site "${SITE_NAME}" set-maintenance-mode off

echo "Deployed qd_hrms to ${SITE_NAME}"
