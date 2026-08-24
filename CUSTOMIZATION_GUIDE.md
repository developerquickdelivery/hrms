# QD HRMS customization guide

QD HRMS extends ERPNext and Frappe HR without editing their source code.

## Supported customization mechanisms

- Custom DocTypes owned by the `QD HRMS` module
- Custom Fields and Property Setters created by idempotent setup functions
- `doc_events`, permission hooks, client scripts, and scheduled jobs
- Standard Frappe Workflows, Notifications, Reports, Dashboards, and Workspaces

Never edit files inside the `frappe`, `erpnext`, or `hrms` applications.

## Apply all configuration

Installing or migrating the app invokes `qd_hrms.setup.install.after_install`.
For an existing site:

```bash
cd ~/frappe-bench
bench --site <site> backup --with-files
bench --site <site> migrate
bench build --app qd_hrms
bench --site <site> clear-cache
```

Individual setup functions under `qd_hrms/setup/` are intended for development
and targeted recovery. Production deployments should use `bench migrate` so the
whole configuration is applied consistently.

## Main setup modules

- `branding`, `people`, `organization`, `job_grades`, `positions`
- `employee_directory`, `employment_info`, `bank_tax_pension`, `promotion`
- `offers`, `requisition`, `onboarding`
- `attendance` (includes attendance periods, overtime, and biometrics)
- `leave`, `leave_payroll`, `performance`, `learning`
- `employee_relations`, `employee_assets`, `employee_requests`, `separation`
- `analytics`, `notifications`, `integrations`, `hr_admin`, `self_service`

## Adding a standard DocType extension

1. Create fields in an idempotent setup function with `create_custom_fields`.
2. Prefix custom fields with `custom_qd_`.
3. Add server behavior through hooks, not core overrides, unless a class
   override is unavoidable.
4. Add record-level permission hooks for employee-facing data.
5. Make setup safe to run repeatedly.
6. Add tests and run `python scripts/validate_app.py`.

## Adding a custom DocType

Create it inside:

```text
qd_hrms_app/qd_hrms/qd_hrms/doctype/<doctype_name>/
```

Include `__init__.py`, metadata JSON, and a controller. Define least-privilege
permissions in metadata and enforce lifecycle invariants in the controller.
Whitelisted mutation methods must explicitly check permissions.

## Integrations and secrets

- Store credentials only in Frappe `Password` fields.
- Keep TLS verification enabled.
- Bound inbound payload sizes and authenticate before using elevated flags.
- Restrict outbound request paths to the configured integration host.
- Do not write credentials or unsanitized payloads to logs.

## Verification

```bash
python scripts/validate_app.py
bench --site <staging-site> migrate
bench --site <staging-site> run-tests --app qd_hrms
```

Complete functional acceptance on staging for employee self-service, approvals,
attendance locks, leave, payroll inputs, integrations, notifications, and
separation before promoting a release.
