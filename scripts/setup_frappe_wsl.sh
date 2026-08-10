#!/usr/bin/env bash
# Quick Delivery HRMS — Frappe/ERPNext + qd_hrms setup for WSL (Ubuntu 22.04/24.04)
# Run inside WSL as your normal user (NOT root):  bash setup_frappe_wsl.sh
set -euo pipefail

APP_NAME="qd_hrms"
BENCH_DIR="${HOME}/frappe-bench"
SITE_NAME="${SITE_NAME:-qd.local}"
ADMIN_PASS="${ADMIN_PASS:-admin}"
MYSQL_ROOT_PASS="${MYSQL_ROOT_PASS:-admin}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-version-15}"
HRMS_BRANCH="${HRMS_BRANCH:-version-15}"

echo "==> QD HRMS environment setup"
echo "    Bench: ${BENCH_DIR}"
echo "    Site:  ${SITE_NAME}"
echo "    Branch: ${FRAPPE_BRANCH}"

# ---------------------------------------------------------------------------
# 1) System packages
# ---------------------------------------------------------------------------
echo "==> [1/8] Installing system packages (needs sudo)..."
# WSL clocks are often skewed; avoid apt "Release file is not valid yet" failures
APT_OPTS=(-o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false)
sudo apt-get "${APT_OPTS[@]}" update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get "${APT_OPTS[@]}" install -y \
  git curl wget build-essential \
  python3-dev python3-pip python3-venv python3-setuptools \
  redis-server \
  software-properties-common \
  libffi-dev libssl-dev \
  libmariadb-dev mariadb-client \
  pkg-config \
  xvfb libfontconfig \
  cron

# Node 18 + npm + yarn (Frappe v15)
# Ubuntu's `nodejs` package does NOT always ship `npm` — install both.
echo "==> Ensuring Node.js >= 18, npm, and yarn..."
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v 2>/dev/null | cut -d. -f1 | tr -d v)" -lt 18 ]]; then
  echo "==> Installing Node.js 18 (NodeSource, fallback to Ubuntu packages)..."
  if curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -; then
    sudo apt-get "${APT_OPTS[@]}" install -y nodejs
  else
    sudo apt-get "${APT_OPTS[@]}" install -y nodejs npm
  fi
fi
if ! command -v npm >/dev/null 2>&1; then
  sudo apt-get "${APT_OPTS[@]}" install -y npm
fi
if ! command -v yarn >/dev/null 2>&1; then
  sudo npm install -g yarn || sudo apt-get "${APT_OPTS[@]}" install -y yarn
fi
node -v
npm -v
yarn -v

# MariaDB server
if ! command -v mysqld >/dev/null 2>&1 && ! command -v mariadbd >/dev/null 2>&1; then
  echo "==> Installing MariaDB..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get "${APT_OPTS[@]}" install -y mariadb-server
fi

# Ensure MariaDB is running
sudo service mariadb start || sudo service mysql start || true
sudo service redis-server start || true

# MariaDB root auth for local bench (dev-friendly)
echo "==> Configuring MariaDB for local development..."
sudo mysql -u root <<SQL || true
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL

# If socket auth still required:
sudo mysql -u root <<SQL || true
ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('${MYSQL_ROOT_PASS}');
FLUSH PRIVILEGES;
SQL

# wkhtmltopdf (optional, for PDFs)
if ! command -v wkhtmltopdf >/dev/null 2>&1; then
  echo "==> Installing wkhtmltopdf (best-effort)..."
  sudo apt-get "${APT_OPTS[@]}" install -y wkhtmltopdf || true
fi

# ---------------------------------------------------------------------------
# 2) Bench CLI
# ---------------------------------------------------------------------------
echo "==> [2/8] Installing frappe-bench CLI..."
pip3 install --user frappe-bench --break-system-packages 2>/dev/null \
  || pip3 install --user frappe-bench

export PATH="${HOME}/.local/bin:${PATH}"
grep -q 'HOME/.local/bin' "${HOME}/.bashrc" 2>/dev/null || \
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"

# ---------------------------------------------------------------------------
# 3) Init bench
# ---------------------------------------------------------------------------
if [[ ! -d "${BENCH_DIR}" ]]; then
  echo "==> [3/8] Creating bench at ${BENCH_DIR}..."
  bench init "${BENCH_DIR}" --frappe-branch "${FRAPPE_BRANCH}" --python python3
else
  echo "==> [3/8] Bench already exists at ${BENCH_DIR}, skipping init."
fi

cd "${BENCH_DIR}"

# ---------------------------------------------------------------------------
# 4) Get ERPNext + HRMS
# ---------------------------------------------------------------------------
echo "==> [4/8] Getting ERPNext and HRMS apps..."
if [[ ! -d "apps/erpnext" ]]; then
  bench get-app erpnext --branch "${ERPNEXT_BRANCH}"
fi
if [[ ! -d "apps/hrms" ]]; then
  bench get-app hrms --branch "${HRMS_BRANCH}"
fi

# ---------------------------------------------------------------------------
# 5) Create site
# ---------------------------------------------------------------------------
echo "==> [5/8] Creating site ${SITE_NAME}..."
if [[ ! -d "sites/${SITE_NAME}" ]]; then
  bench new-site "${SITE_NAME}" \
    --mariadb-root-password "${MYSQL_ROOT_PASS}" \
    --admin-password "${ADMIN_PASS}" \
    --no-mariadb-socket || \
  bench new-site "${SITE_NAME}" \
    --db-root-password "${MYSQL_ROOT_PASS}" \
    --admin-password "${ADMIN_PASS}"
fi

bench use "${SITE_NAME}"

# ---------------------------------------------------------------------------
# 6) Install apps on site (needs Redis queue running)
# ---------------------------------------------------------------------------
echo "==> [6/8] Starting Redis for app install..."
if [[ -f config/redis_queue.conf ]]; then
  redis-server config/redis_queue.conf --daemonize yes || true
fi
if [[ -f config/redis_cache.conf ]]; then
  redis-server config/redis_cache.conf --daemonize yes || true
fi
sleep 2

echo "==> Installing erpnext + hrms on site..."
bench --site "${SITE_NAME}" install-app erpnext || true
bench --site "${SITE_NAME}" install-app hrms || true

# ---------------------------------------------------------------------------
# 7) Create custom app qd_hrms
# ---------------------------------------------------------------------------
echo "==> [7/8] Creating custom app ${APP_NAME}..."
if [[ ! -d "apps/${APP_NAME}" ]]; then
  # Prompts: title, description, publisher, email, license, GitHub workflow y/N
  printf '%s\n' \
    "Quick Delivery HRMS" \
    "HRMS customizations for Quick Delivery Service" \
    "Quick Delivery Service" \
    "qd@quickdelivery.local" \
    "mit" \
    "N" | bench new-app "${APP_NAME}"
fi

bench --site "${SITE_NAME}" install-app "${APP_NAME}" || true

# ---------------------------------------------------------------------------
# 8) Developer mode + hosts hint
# ---------------------------------------------------------------------------
echo "==> [8/8] Enabling developer mode..."
bench --site "${SITE_NAME}" set-config developer_mode 1
bench --site "${SITE_NAME}" clear-cache

# Allow access from Windows browser via localhost
bench set-config -g host_name "${SITE_NAME}" || true

echo ""
echo "============================================================"
echo " SETUP COMPLETE"
echo "============================================================"
echo " Site URL (after start):  http://127.0.0.1:8000"
echo " Site name:               ${SITE_NAME}"
echo " Administrator password:  ${ADMIN_PASS}"
echo " Bench path:              ${BENCH_DIR}"
echo " Custom app:              ${APP_NAME}"
echo ""
echo " Start the stack:"
echo "   cd ${BENCH_DIR}"
echo "   bench start"
echo ""
echo " Optional — map site name in Windows hosts:"
echo "   Add to C:\\Windows\\System32\\drivers\\etc\\hosts :"
echo "   127.0.0.1  ${SITE_NAME}"
echo " Then open http://${SITE_NAME}:8000"
echo "============================================================"
