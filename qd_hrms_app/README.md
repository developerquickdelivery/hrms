# QD HRMS

Upgrade-safe HR management extensions for Quick Delivery Service, built on
Frappe Framework, ERPNext, and Frappe HR.

## Compatibility

- Frappe Framework 15
- ERPNext 15
- Frappe HR 15
- Python 3.10+

The app declares ERPNext and HRMS as required apps. Install those applications
before installing `qd_hrms`.

## Install

The distributable Frappe app is the `qd_hrms_app` directory in this repository.
Copy or publish that directory as the root of the app repository, then run:

```bash
cd ~/frappe-bench
bench get-app <qd-hrms-app-repository-url>
bench --site <site> install-app qd_hrms
bench --site <site> migrate
bench build --app qd_hrms
bench --site <site> clear-cache
```

Do not edit files in `frappe`, `erpnext`, or `hrms`. All custom DocTypes,
workflows, hooks, reports, permissions, and workspaces are maintained here.

## Validate

From the parent repository:

```bash
python scripts/validate_app.py
```

On a Bench with a test site:

```bash
bench --site <test-site> migrate
bench --site <test-site> run-tests --app qd_hrms
```

## Production operations

Run Frappe in production mode with HTTPS, MariaDB, Redis, background workers,
the scheduler, backups, and monitoring. Never deploy with `bench start`.
Credentials belong in Frappe Password fields or site configuration and must not
be committed to Git.
