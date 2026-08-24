#!/usr/bin/env bash
# Bootstrap a fresh Ubuntu 24.04 VPS (DigitalOcean) for Frappe/ERPNext HRMS production.
# Run as a sudo-capable user (not root). Creates user "frappe" if missing.
#
# HRMS first — do not install Coolify on this droplet yet (port 80/443 conflict with Nginx).
# Leave DELIVERY_DOMAIN empty. Delivery (Node/React/Postgres) goes on a later droplet + Coolify.
#
# Example:
#   export HRMS_DOMAIN=hrms.example.com
#   export ADMIN_EMAIL=admin@example.com
#   export MYSQL_ROOT_PASS='...'
#   export ADMIN_PASS='...'
#   bash provision_production_server.sh
set -euo pipefail

FRAPPE_USER="${FRAPPE_USER:-frappe}"
BENCH_DIR="${BENCH_DIR:-/home/${FRAPPE_USER}/frappe-bench}"
HRMS_DOMAIN="${HRMS_DOMAIN:-}"
DELIVERY_DOMAIN="${DELIVERY_DOMAIN:-}"
ADMIN_EMAIL="${ADMIN_EMAIL:-}"
MYSQL_ROOT_PASS="${MYSQL_ROOT_PASS:-}"
ADMIN_PASS="${ADMIN_PASS:-}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-version-15}"
HRMS_BRANCH="${HRMS_BRANCH:-version-15}"
SWAP_GB="${SWAP_GB:-4}"

if [[ "$(id -u)" -eq 0 ]]; then
	echo "Run this script as a normal sudo user, not root."
	exit 1
fi

if [[ -z "${HRMS_DOMAIN}" || -z "${ADMIN_EMAIL}" ]]; then
	echo "Set HRMS_DOMAIN and ADMIN_EMAIL before running."
	echo "Leave DELIVERY_DOMAIN empty for HRMS-only install."
	exit 1
fi

if [[ -z "${MYSQL_ROOT_PASS}" || -z "${ADMIN_PASS}" ]]; then
	echo "Set MYSQL_ROOT_PASS and ADMIN_PASS (strong random values)."
	exit 1
fi

if [[ -n "${DELIVERY_DOMAIN}" ]]; then
	echo "NOTE: DELIVERY_DOMAIN is set. Prefer leaving it empty; delivery apps should use Coolify on another droplet."
fi

echo "==> [1/12] System update and base packages"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
	git curl wget build-essential \
	python3-dev python3-pip python3-venv python3-setuptools \
	redis-server \
	software-properties-common \
	libffi-dev libssl-dev \
	libmariadb-dev mariadb-server mariadb-client \
	pkg-config \
	xvfb libfontconfig \
	cron nginx certbot python3-certbot-nginx \
	supervisor fail2ban ufw \
	wkhtmltopdf

echo "==> [2/12] Swap (${SWAP_GB}G) for 8GB droplets"
if ! swapon --show | grep -q '/swapfile'; then
	sudo fallocate -l "${SWAP_GB}G" /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_GB * 1024))
	sudo chmod 600 /swapfile
	sudo mkswap /swapfile
	sudo swapon /swapfile
	grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "==> [3/12] Firewall"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "==> [4/12] MariaDB hardening and tuning"
sudo systemctl enable mariadb
sudo systemctl start mariadb
sudo mysql -u root <<SQL || true
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASS}';
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
FLUSH PRIVILEGES;
SQL

sudo tee /etc/mysql/mariadb.conf.d/99-qd-production.cnf >/dev/null <<'CNF'
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
max_connections = 200
CNF
sudo systemctl restart mariadb

echo "==> [5/12] Node.js 18 + yarn"
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -d. -f1 | tr -d v)" -lt 18 ]]; then
	curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
	sudo apt-get install -y nodejs
fi
sudo npm install -g yarn

echo "==> [6/12] Frappe system user"
if ! id "${FRAPPE_USER}" >/dev/null 2>&1; then
	sudo adduser --disabled-password --gecos "" "${FRAPPE_USER}"
	sudo usermod -aG sudo "${FRAPPE_USER}"
fi

echo "==> [7/12] Bench CLI for ${FRAPPE_USER} (pipx + uv — required on Ubuntu 24.04)"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y pipx curl
sudo -u "${FRAPPE_USER}" bash -lc '
set -euo pipefail
pipx ensurepath
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if ! command -v bench >/dev/null 2>&1; then
	pipx install frappe-bench
fi
grep -q ".local/bin" ~/.bashrc || echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc
grep -q ".cargo/bin" ~/.bashrc || echo "export PATH=\"\$HOME/.cargo/bin:\$PATH\"" >> ~/.bashrc
bench --version
uv --version
'

if [[ ! -d "${BENCH_DIR}" ]]; then
	echo "==> [8/12] Initialize bench"
	sudo -u "${FRAPPE_USER}" bash -lc "
set -euo pipefail
export PATH=\"\$HOME/.local/bin:\$HOME/.cargo/bin:\$PATH\"
bench init ${BENCH_DIR} --frappe-branch ${FRAPPE_BRANCH} --python python3
cd ${BENCH_DIR}
bench get-app erpnext --branch ${ERPNEXT_BRANCH}
bench get-app hrms --branch ${HRMS_BRANCH}
"
else
	echo "==> [8/12] Bench already exists at ${BENCH_DIR}"
fi

echo "==> [9/12] Create production sites"
sudo -u "${FRAPPE_USER}" bash -lc "
set -euo pipefail
export PATH=\"\$HOME/.local/bin:\$PATH\"
cd ${BENCH_DIR}
if [[ ! -d sites/${HRMS_DOMAIN} ]]; then
	bench new-site ${HRMS_DOMAIN} \
		--mariadb-root-password '${MYSQL_ROOT_PASS}' \
		--admin-password '${ADMIN_PASS}' \
		--no-mariadb-socket
	bench --site ${HRMS_DOMAIN} install-app erpnext
	bench --site ${HRMS_DOMAIN} install-app hrms
fi
if [[ -n '${DELIVERY_DOMAIN}' && ! -d sites/${DELIVERY_DOMAIN} ]]; then
	bench new-site ${DELIVERY_DOMAIN} \
		--mariadb-root-password '${MYSQL_ROOT_PASS}' \
		--admin-password '${ADMIN_PASS}' \
		--no-mariadb-socket
	bench --site ${DELIVERY_DOMAIN} install-app erpnext
fi
bench set-config -g developer_mode 0
bench set-config -g server_script_enabled 0
"

echo "==> [10/12] Production process manager (supervisor + nginx)"
# Must run with real root: bench writes /etc/supervisor and /etc/nginx.
# Running only as frappe prints "WARN: superuser privileges required" and skips setup.
sudo env "PATH=/home/${FRAPPE_USER}/.local/bin:/home/${FRAPPE_USER}/.cargo/bin:${PATH}" \
	bash -lc "cd ${BENCH_DIR} && bench setup production ${FRAPPE_USER} --yes"

echo "==> [11/12] TLS certificates"
for domain in "${HRMS_DOMAIN}" "${DELIVERY_DOMAIN}"; do
	[[ -z "${domain}" ]] && continue
	sudo certbot --nginx -d "${domain}" --non-interactive --agree-tos -m "${ADMIN_EMAIL}" || true
done

echo "==> [12/12] Scheduled backups (daily 02:30 server time)"
sudo tee /etc/cron.d/qd-bench-backup >/dev/null <<CRON
30 2 * * * ${FRAPPE_USER} cd ${BENCH_DIR} && /usr/bin/bench --site all backup --with-files >> /home/${FRAPPE_USER}/backup.log 2>&1
CRON

cat <<DONE

============================================================
 PRODUCTION SERVER BOOTSTRAP COMPLETE
============================================================
 Bench:     ${BENCH_DIR}
 HRMS site: https://${HRMS_DOMAIN}
 Delivery:  ${DELIVERY_DOMAIN:+https://${DELIVERY_DOMAIN}}
 Admin:     Administrator / (password you set in ADMIN_PASS)

 Next steps:
 1. Point DNS A record for ${HRMS_DOMAIN} to this server's public IP (if not using nip.io).
 2. Enable DigitalOcean automated backups in the control panel.
 3. Deploy qd_hrms: bash scripts/deploy_qd_hrms_production.sh
 4. Configure SMTP in HR Settings and test email delivery.
 5. Wire GitHub Actions secrets and run deploy-production.yml once.
 6. Do NOT install Coolify on this droplet yet — use a second droplet later for Node apps.

 Useful commands (as ${FRAPPE_USER}):
   sudo supervisorctl status
   cd ${BENCH_DIR} && bench --site ${HRMS_DOMAIN} doctor
   cd ${BENCH_DIR} && bench --site ${HRMS_DOMAIN} migrate
============================================================
DONE
