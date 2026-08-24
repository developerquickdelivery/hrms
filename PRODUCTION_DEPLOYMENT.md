# Production deployment

## Decision: what to install first

**Deploy QD HRMS first. Do not install Coolify (or similar) on this droplet yet.**

| Order | What | Why |
|---|---|---|
| 1 | Harden VPS + Frappe HRMS (bench + Nginx) | You need HRMS live for development and production |
| 2 | GitHub CI/CD → SSH deploy to this server | Repeatable releases without manual `scp` |
| 3 | Later: Coolify/Dokku on a **second** droplet (or same VPS after careful proxy design) | Delivery team’s Node/React/PostgreSQL/WebSockets stack |

Coolify, CapRover, and Dokku all want to own **ports 80/443** with their own reverse proxy (Traefik/Caddy). Frappe production also owns 80/443 via Nginx. Putting both on one 8 GB droplet without a deliberate proxy design causes conflicts and brittle upgrades.

**Recommended app manager later (for Node apps):** [Coolify](https://coolify.io) on a **separate** DigitalOcean droplet (2–4 GB is enough to start). It is modern, open source, and better suited to Dockerized Node/React/Postgres than Frappe. Lighter alternatives: **Dokku** (Heroku-like, leaner) or **Portainer CE** (Docker UI only, you keep Nginx yourself).

Reserve ~2–3 GB RAM and disk headroom on this VPS for future containers if you later co-host carefully; for now, treat this droplet as **HRMS production**.

## Required platform (HRMS)

QD HRMS requires a Linux server that can continuously run:

- Frappe/ERPNext/HRMS version 15 and Python 3.10+
- MariaDB, Redis, Nginx, Node/Yarn, and Bench
- web, queue, scheduler, and Socket.IO processes
- TLS certificates, outbound email, scheduled backups, and monitoring

Shared cPanel hosting is suitable only when the provider explicitly supports
these persistent services, SSH access, process supervision, and the required
ports. Seeing Redis in cPanel alone is not sufficient. Vercel cannot host the
Frappe backend or database.

## DigitalOcean VPS — HRMS only (current droplet)

Target: Ubuntu 24.04 LTS, 4 vCPU / 8 GB RAM (`159.89.92.149`).

### Layout

| Service | Domain / path | Stack |
|---|---|---|
| **HRMS (now)** | `hrms.yourdomain.com` | Frappe bench: erpnext + hrms + qd_hrms, MariaDB, Redis, Nginx |
| **Delivery (later)** | Separate droplet + Coolify preferred | Node, React, PostgreSQL, WebSockets — external team |

Do **not** create a second Frappe site for the delivery system.

### Before bootstrap

1. SSH as `serveradmin` (not root for day-to-day).
2. DNS A record: `hrms.yourdomain.com` → `159.89.92.149` (or use `hrms.159.89.92.149.nip.io` temporarily).
3. Enable **Automated Backups** in the DigitalOcean panel.
4. Copy this repo to the server (prefer tar/rsync; avoid huge `.git` via `scp -r`).

### First-time HRMS setup

As `serveradmin`:

```bash
cd ~/QD-HRMS

export HRMS_DOMAIN=hrms.yourdomain.com
# Leave DELIVERY_DOMAIN unset — HRMS only
export ADMIN_EMAIL=you@yourdomain.com
export MYSQL_ROOT_PASS='generate-a-long-random-password'
export ADMIN_PASS='generate-another-strong-password'

# Run inside tmux so SSH drops do not kill a 30–60 minute install
sudo apt install -y tmux
tmux new -s hrms-provision
bash scripts/provision_production_server.sh
```

Then deploy the custom app:

```bash
sudo -u frappe -i
export SITE_NAME=hrms.yourdomain.com
export QD_HRMS_SRC=/home/serveradmin/QD-HRMS/qd_hrms_app
bash /home/serveradmin/QD-HRMS/scripts/deploy_qd_hrms_production.sh
```

### GitHub CI/CD (after first successful manual deploy)

1. Push this repository to GitHub.
2. On the VPS, create a deploy key or use the `serveradmin`/`frappe` SSH key for GitHub Actions.
3. Add repository secrets:
   - `PRODUCTION_HOST` = `159.89.92.149`
   - `PRODUCTION_USER` = `frappe` (or `serveradmin` with sudo)
   - `PRODUCTION_SSH_KEY` = private key with access to the VPS
   - `PRODUCTION_SITE` = `hrms.yourdomain.com`
4. Workflows:
   - `.github/workflows/quality.yml` — lint/validate on every PR
   - `.github/workflows/deploy-production.yml` — on push to `main` (or release tags), SSH deploy + migrate

Manual one-shot from CI is documented in that workflow file. Refine SMTP, roles, and monitoring after the first green deploy.

### If HTTPS shows the default Nginx page (615 bytes)

`bench setup production` needs **root**. From `serveradmin` (do not `cd` into `/home/frappe` as yourself):

```bash
export HRMS_DOMAIN=hrms.159.89.92.149.nip.io

sudo env "PATH=/home/frappe/.local/bin:/home/frappe/.cargo/bin:$PATH" \
  bash -lc 'cd /home/frappe/frappe-bench && bench setup production frappe --yes'

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
sudo nginx -t && sudo systemctl reload nginx
curl -Ik "https://${HRMS_DOMAIN}"
```

Expect supervisor jobs named like `frappe-bench-web`, `frappe-bench-workers`, etc., and a Frappe response (not `Content-Length: 615`).

### Post-bootstrap checklist

- [ ] HTTPS loads for the HRMS domain
- [ ] `sudo supervisorctl status` shows web, workers, scheduler, redis
- [ ] `bench --site <site> doctor` is clean
- [ ] Scheduler enabled; SMTP tested
- [ ] Non-Administrator users created
- [ ] DigitalOcean backups on; restore drill documented
- [ ] GitHub Actions deploy succeeds once
- [ ] Coolify **not** installed on this droplet yet

## Release checklist (ongoing)

1. Use a staging site restored from a recent production backup.
2. Check out an immutable release tag for `qd_hrms`.
3. Run `python scripts/validate_app.py` in this repository.
4. Back up production:

   ```bash
   bench --site <site> backup --with-files
   ```

5. Deploy during a maintenance window:

   ```bash
   cd ~/frappe-bench
   bench --site <site> set-maintenance-mode on
   bench update --reset
   bench --site <site> migrate
   bench build --app qd_hrms
   bench --site <site> clear-cache
   sudo supervisorctl restart all
   sudo systemctl reload nginx
   bench --site <site> set-maintenance-mode off
   ```

6. Confirm the site, workers, scheduler, email queue, error log, and critical HR
   flows. Run tests on staging, not against live employee/payroll data:

   ```bash
   bench --site <staging-site> run-tests --app qd_hrms
   ```

## Configuration

- Keep secrets out of Git and store integration credentials in Frappe Password
  fields.
- Keep SSL verification enabled for outbound integrations.
- Give biometric devices unique, high-entropy secrets and rotate them.
- Enable the scheduler and workers; notifications, retries, certification
  expiry, goal metrics, biometric polling, and overdue asset processing depend
  on them.
- Configure off-server encrypted backups and test restoration regularly.
- Restrict Administrator/System Manager access and use least-privilege HR roles.
- Configure SMTP/SMS providers and verify delivery logs before go-live.

## Rollback

Application code can be rolled back to the previous release tag only when its
schema remains compatible. If a migration changed data or schema incompatibly,
restore the pre-deployment database and files backup instead:

```bash
bench --site <site> restore <database-backup> \
  --with-public-files <public-files-backup> \
  --with-private-files <private-files-backup>
bench --site <site> migrate
```

Practice this procedure on staging before the first production release.

## Later: delivery system + Coolify

When the external team is ready:

1. Create a **second** DigitalOcean droplet (recommended).
2. Install Coolify there for Node/React/PostgreSQL/WebSockets apps.
3. Point `api.` / `app.` domains to that droplet.
4. Scale that droplet independently; keep HRMS stable on this one.

If you must co-host on one VPS later, put Coolify’s proxy **in front** of everything and reverse-proxy to Frappe’s local ports — plan that as a migration project, not day-one setup.
