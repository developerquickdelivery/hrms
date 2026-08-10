# QD HRMS — WSL Environment Setup

## Current status on this machine
- WSL 2 is available
- **Ubuntu-24.04 is installed** (first-time Linux user setup may still be needed)
- Docker is not installed (not required for this path)

## Step 1 — Finish Ubuntu first login (required once)

Open **Ubuntu 24.04 LTS** from the Windows Start menu (or run `wsl -d Ubuntu-24.04` in a real terminal window).

When prompted, create:
- Linux username (e.g. `qd`)
- Password (you will need this for `sudo`)

Then verify in that Ubuntu window:

```bash
whoami
uname -a
```

If Ubuntu is missing entirely, open **PowerShell as Administrator** and run:

```powershell
cd C:\anw\work\QD-HRMS\scripts
Set-ExecutionPolicy -Scope Process Bypass
.\01_install_ubuntu_wsl.ps1
```

## Clock / apt note
If apt fails with `Release file ... is not valid yet`, your Windows/WSL clock is behind.
Fix Windows time (Settings → Time → Sync now), or re-run the updated setup script
(which ignores apt date checks for local install).

## Step 2 — Copy setup script into WSL and run it

From **PowerShell** (normal user is fine):

```powershell
# Create folder in WSL home and copy script
wsl -d Ubuntu-24.04 -e bash -lc "mkdir -p ~/qd-hrms-setup"
wsl -d Ubuntu-24.04 -e bash -lc "cp /mnt/c/anw/work/QD-HRMS/scripts/setup_frappe_wsl.sh ~/qd-hrms-setup/ && chmod +x ~/qd-hrms-setup/setup_frappe_wsl.sh"
```

Enter Ubuntu:

```powershell
wsl -d Ubuntu-24.04
```

Then inside WSL:

```bash
cd ~/qd-hrms-setup
bash setup_frappe_wsl.sh
```

This installs:
- MariaDB + Redis + Node 18 + Yarn
- Frappe Bench (version-15)
- ERPNext + HRMS
- Custom app **qd_hrms**
- Site **qd.local** (Administrator / `admin`)

Takes 20–40 minutes depending on network.

## Step 3 — Start the server

```bash
cd ~/frappe-bench
bench start
```

Open in Windows browser: **http://127.0.0.1:8000**
- User: `Administrator`
- Password: `admin`

## Step 4 — Start customizing

In Desk:
1. Switch to company setup / create **Quick Delivery Service**
2. Open **Workspace** → create HR workspaces by role
3. **Customize Form** → Employee (add `custom_qd_*` fields)
4. **DocType List** → New → build `QD Employee Request`, etc. inside app `qd_hrms`

Or from terminal (developer mode already on):

```bash
cd ~/frappe-bench
bench --site qd.local console
# or edit files under:
# ~/frappe-bench/apps/qd_hrms/
```

Export customizations later:

```bash
bench --site qd.local export-fixtures
```

## Optional — map site name

Add to `C:\Windows\System32\drivers\etc\hosts` (Admin Notepad):

```
127.0.0.1  qd.local
```

Then use http://qd.local:8000

## Useful commands

| Action | Command |
|---|---|
| Start | `cd ~/frappe-bench && bench start` |
| Migrate | `bench --site qd.local migrate` |
| Clear cache | `bench --site qd.local clear-cache` |
| New DocType UI | Desk → DocType → New (Module: QD HRMS) |
| Build assets | `bench build --app qd_hrms` |

## Passwords (dev defaults — change later)

| Item | Value |
|---|---|
| Site | `qd.local` |
| Administrator | `admin` |
| MariaDB root | `admin` |

Override when running setup:

```bash
SITE_NAME=qd.local ADMIN_PASS='YourPass' MYSQL_ROOT_PASS='YourDbPass' bash setup_frappe_wsl.sh
```
