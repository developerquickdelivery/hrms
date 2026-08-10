# QD HRMS — Safe Customization Rules (never touch ERPNext core)

## You can start NOW

Your stack is running:
- URL: http://127.0.0.1:8000
- Apps: `frappe`, `erpnext`, `hrms`, `qd_hrms`
- Company setup wizard already completed

**Golden rule:** edit only `~/frappe-bench/apps/qd_hrms`.  
Never edit files under `apps/frappe`, `apps/erpnext`, or `apps/hrms`.

---

## Navigation policy (Option B) — no duplicate menus

**Decision:** Do **not** create parallel “QD Organization / QD Employees / QD Recruitment / QD Onboarding” sidebars.

| User sees | Purpose |
|---|---|
| **… Dashboard** (role homes only) | Branded Quick Delivery landing + shortcuts |
| **Standard HRMS menus** | Recruitment, Employee Lifecycle, Shift & Attendance, Leave, Payroll |
| **Projects / Assets** | Kept (onboarding tasks + equipment) — not duplicated |
| **QD custom DocTypes** | Open via dashboard links, Awesome Bar, or buttons on forms |

### Sitemap → where to click

| Sitemap | Use this (standard + QD extensions) |
|---|---|
| 2.1 Dashboards | **HR / Manager / Employee Dashboard** (+ Administrator overall control) |
| 2.2 Organization | Company, Branch, Department, Cost Center, Designation, Grade + **QD Position** |
| 2.3 Employees | Employee + **QD Employment Event**, **QD Employee Document** |
| 2.4 Recruitment | Workspace **Recruitment** + **QD Background Check** |
| 2.5 Onboarding | Workspace **Employee Lifecycle** + **QD Probation Review** |
| 2.6 Attendance | Workspace **Shift & Attendance** + Biometric Device |
| 2.7 Leave | Workspace **Leaves** |
| 2.8 Payroll | Workspaces **Payroll** / **Salary Payout** / **Tax & Benefits** |
| 2.9 Performance | Workspace **Performance** + PIP / Recognition |
| 2.10 Learning | Training Program/Event + Training Request |
| 2.11 Employee Relations | Disciplinary Case + Grievance (no ER sidebar) |
| 2.12 Assets | Workspace **Assets** + Asset Incident |
| Projects | Standard **Project** (also used by onboarding) |

Refresh Option B + attendance:
```bash
bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.navigation.run
bench --site qd.local execute qd_hrms.setup.attendance.run
bench --site qd.local execute qd_hrms.setup.dashboards.run
bench build --app qd_hrms
bench --site qd.local clear-cache
```

---

## Create users with roles (fixed)

Frappe normally hides role checkboxes until **after** the first Save. `qd_hrms` now:

1. Shows the **Roles** UI on **new** User forms  
2. Ships **Role Profiles** you can pick at create time  

| Role Profile | Includes |
|---|---|
| Employee | QD Employee + Employee |
| Department Manager | QD Department Manager + Employee + Leave Approver |
| HR Officer | QD HR Officer + HR User |
| Recruitment Officer | QD Recruitment Officer + HR User |
| Payroll Officer | QD Payroll Officer + HR User (+ Accounts User if present) |
| Administrator | Built-in System Manager — full site control (no separate Executive role) |
| Payroll Officer | QD Payroll Officer + HR User (+ Accounts User if present) |

### Steps
1. User → **New**
2. Email, name, password; **User Type = System User**
3. **Roles** tab → set **Role Profile** (e.g. HR Officer) **or** tick roles
4. Save once  
5. (Optional) Permissions → **Set User Permissions** to limit data by Employee/Company  

Refresh after deploy: `bench build --app qd_hrms && bench --site qd.local clear-cache`

---

## What “safe customization” means

| Do this (upgrade-safe) | Never do this |
|---|---|
| Custom DocTypes in `qd_hrms` | Edit ERPNext/HRMS Python/JS |
| Custom Fields via Customize Form → export fixtures | Patch core DocType JSON |
| Client Script / Server Script (or app `.js` / `.py` hooks) | Fork `erpnext` / `hrms` repos for small changes |
| `hooks.py` overrides (doc_events, override_whitelisted_methods) | Copy-paste core files into custom app |
| Print Formats, Workflows, Notifications, Workspace | Change core naming series in core files |
| Reports / Script Reports in `qd_hrms` | Commit changes inside `apps/erpnext` |

When ERPNext/HRMS updates: `bench update` pulls core; your `qd_hrms` stays. Fix only if APIs change.

---

## Where to put each kind of work

### 1) Extra fields on standard forms (Employee, Leave, Attendance…)
1. Desk → Customize Form → pick DocType  
2. Add fields (`custom_qd_*` naming)  
3. Export into app:

```bash
cd ~/frappe-bench
bench --site qd.local export-fixtures
```

Configure in `qd_hrms/hooks.py`:

```python
fixtures = [
  "Custom Field",
  "Property Setter",
  "Client Script",
  "Server Script",
  "Workflow",
  "Workflow State",
  "Workflow Action Master",
  "Role",
  {"dt": "Workspace", "filters": [["module", "=", "QD HRMS"]]},
]
```

### 2) New business objects (ER cases, requests, probation…)
Desk → DocType → New → **Module = QD HRMS**  
Files land in `apps/qd_hrms/...` automatically (developer_mode on).

### 3) Behavior without forking core
In `qd_hrms/hooks.py`:

```python
doc_events = {
  "Employee": {
    "validate": "qd_hrms.overrides.employee.validate",
  },
  "Employee Checkin": {
    "after_insert": "qd_hrms.integrations.biometric.on_checkin",
  },
}
```

### 4) Biometric attendance (recommended pattern)
Use **standard** `Employee Checkin` + `Attendance` (do not rebuild attendance).

In `qd_hrms`:
1. DocType `QD Biometric Device` (device id, IP, secret, location, active)
2. DocType / log `QD Biometric Sync Log` (optional)
3. API method e.g. `/api/method/qd_hrms.integrations.biometric.push_punch`
4. Map device user-id → Employee (`attendance_device_id` custom field on Employee)
5. Create **Employee Checkin** rows (IN/OUT); let HRMS mark Attendance

Device vendors differ (ZKTeco, etc.) — adapter lives only in `qd_hrms/integrations/`.

### 5) Module fit for Quick Delivery
Priority order (extend, don’t replace):

1. **Employee** custom fields + org (Branch/Department/Designation)  
2. **QD Employee Request** (letters, advances, profile changes)  
3. **Attendance** + biometric integration  
4. **Leave** policies for delivery ops  
5. **Recruitment / Onboarding / Probation** extensions  
6. **QD ER Case**, Separation clearance  
7. Payroll inputs only via Additional Salary / standard payroll  

See earlier blueprint for DocType list.

---

## Daily start (no full reinstall)

Keep `bench start` terminal running while you work.

```bash
wsl -d Ubuntu-24.04
export PATH="$HOME/.local/bin:$PATH"
sudo service mariadb start   # if needed
cd ~/frappe-bench
# if ports busy from yesterday:
#   fuser -k 11000/tcp 13000/tcp 8000/tcp 9000/tcp 2>/dev/null
bench start
```

Browser: http://127.0.0.1:8000

---

## GitHub: only version `qd_hrms` (and docs)

Collaborators do **not** need your whole `frappe-bench`. They install ERPNext normally, then:

```bash
cd ~/frappe-bench
bench get-app https://github.com/<org>/qd_hrms.git
bench --site <site> install-app qd_hrms
bench --site <site> migrate
```

### First push (one-time, on this machine)

```bash
cd ~/frappe-bench/apps/qd_hrms
git init
git add .
git commit -m "Initial QD HRMS custom app"
# create empty repo on GitHub, then:
git remote add origin https://github.com/<org>/qd_hrms.git
git branch -M main
git push -u origin main
```

Optional: also push this Windows folder `C:\anw\work\QD-HRMS` (scripts + SETUP docs) as a second repo `qd-hrms-ops` for environment scripts — not the bench itself.

### What NOT to commit
- `frappe-bench/sites/` (DB passwords, site_config)
- `env/`, logs, Redis dumps
- Core apps (`frappe`, `erpnext`, `hrms`)

---

## Collaboration model

| Person | Needs |
|---|---|
| You | Existing WSL bench + `bench start` |
| Teammate | Own bench (same major version-15) + `get-app qd_hrms` |
| Shared truth | GitHub `qd_hrms` repo + fixtures |

Agree on branch: `main` stable, feature branches `feat/biometric`, `feat/employee-request`.

After pulling teammate work:

```bash
cd ~/frappe-bench
bench get-app qd_hrms   # or: cd apps/qd_hrms && git pull
bench --site qd.local migrate
bench --site qd.local clear-cache
```

---

## First customization session — Sitemap 2.1 Dashboards (DONE)

Installed in `qd_hrms` (no core edits):

| Workspace | Role |
|---|---|
| **HR Dashboard** | QD HR Officer (+ System Manager) |
| **Manager Dashboard** | QD Department Manager |
| **Employee Dashboard** | QD Employee (+ Employee) |

**No Executive Dashboard / QD Executive role.** Administrator (System Manager) is overall site control — creating a parallel “Executive” persona duplicated that and confused users.

Also created Number Cards (active employees, leave, attendance, vacancies, applicants, appraisals).

### How to open them
1. Start stack (`daily_start.sh` or `bench start`) — **MariaDB must be running**
2. Login as Administrator (full control) or as an HR/Manager/Employee user
3. Awesome Bar → `HR Dashboard` / `Manager Dashboard` / `Employee Dashboard`
4. Or left sidebar under module **Quick Delivery HRMS**

### Assign roles to users
User → Role Profile (Employee / Department Manager / HR Officer / …) or Roles → e.g. `QD HR Officer`.

Employee Dashboard navbar icon uses Frappe icon **`assign`** (valid SVG). Do not use `user` — that symbol does not exist in Desk icons.

### Re-install / refresh dashboards after code changes
```bash
cd ~/frappe-bench
bench --site qd.local execute qd_hrms.setup.dashboards.run
bench --site qd.local clear-cache
```

### Next (after 2.1)
Continue sitemap **2.2 Organization Management** — DONE (see below).

## Sitemap 2.2 — Organization Management (DONE)

| Sitemap item | Implementation |
|---|---|
| Company / Legal Entity | Standard **Company** |
| Branches | Standard **Branch** + `custom_qd_is_hub`, `custom_qd_delivery_zone` |
| Departments / Units / Teams | Standard **Department** tree + `custom_qd_org_level` (Division/Department/Unit/Team) |
| Cost Centers | Standard **Cost Center** |
| Locations | **Work Location** on QD Position + Branch zone (standard Location if installed) |
| Job Grades | Standard **Employee Grade** |
| Positions | Custom **QD Position** DocType |
| Organization Chart | Employee list / org chart via **reports_to** |
| Reporting Structure | Employee `reports_to` + QD Position `reports_to_position` |

### Open in Desk
Awesome Bar → **Company** / **Branch** / **Department** / **QD Position**  
Or **QD HR Dashboard** → Organization & Employees card.

### Suggested setup order for Quick Delivery
1. Confirm **Company** (from wizard)
2. Create **Branches** (hubs/stations) — tick Is Delivery Hub where needed
3. Build **Department** tree (Operations → Units/Teams; set QD Org Level)
4. Create **Employee Grade** + **Designation** (Rider, Dispatcher, Hub Supervisor, …)
5. Create **QD Position** rows (one headcount seat each) and link on **Employee**

### Refresh organization setup
```bash
bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.organization.run
bench --site qd.local clear-cache
```

### Next module
**2.6 Attendance and Time** (after 2.3–2.5 done)

---

## Sitemap 2.3 — Employee Management (DONE)

| Sitemap item | Implementation |
|---|---|
| Employee Directory | Standard **Employee** list + workspace **QD Employees** |
| Employee Profile | Standard **Employee** form + QD custom fields |
| Personal Information | Standard Employee tabs (basic, personal, contact) |
| Employment Information | Standard fields + **QD Position**, Staff Category, Work Location |
| Education & Experience | Standard child tables `education`, `external_work_history` |
| Bank / Tax / Pension | Standard bank fields + `custom_qd_tin`, `custom_qd_pension_id` |
| Emergency Contacts | Standard emergency contact section on Employee |
| Employee Documents | Custom **QD Employee Document** (with expiry + attachment) |
| Promotions / Transfers / Salary / Acting | Custom **QD Employment Event** (approved → updates Employee) |
| Employee Self-Service | **QD Employee Dashboard** + Employee portal (User linked to Employee) |

### Open in Desk
Awesome Bar → **Employee** (or **QD Employment Event** / **QD Employee Document**)  
Or **QD HR Dashboard** / **QD Employee Dashboard**.

### Create your first employee (test flow)
1. **QD Organization** → create Branch, Grade, Designation, **QD Position**
2. **QD Employees** → **New Employee**
3. Fill basics + **QD HR Details** (Staff Category, National ID, etc.)
4. Link **QD Position** (auto-fills department/designation)
5. Add **QD Employee Document** (contract, ID scan)
6. For promotion/transfer later → **QD Employment Event** → Approve

### Refresh employee module setup
```bash
bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.employee_management.run
bench build --app qd_hrms
bench --site qd.local clear-cache
```

---

## Sitemap 2.4 — Recruitment (DONE)

| Sitemap item | Implementation |
|---|---|
| Workforce Requisitions | Standard **Job Requisition** + **Staffing Plan** + QD fields (Position, Branch, Urgency) |
| Vacancy Management | Standard **Job Opening** + link to **QD Position** |
| Candidate Database | Standard **Job Applicant** list |
| Application Tracking | **Job Applicant** status + **Employee Referral** |
| Screening and Assessment | QD fields: Screening Score, Notes, Staff Category |
| Interview Management | Standard **Interview**, **Interview Feedback**, **Interview Type/Round** |
| Reference / Background Checks | Custom **QD Background Check** (rolls up status on Applicant) |
| Offer Letters | Standard **Job Offer** + print format |
| Recruitment Reports | Standard **Recruitment Analytics** report |
| Recruitment Settings | **Interview Type**, **Job Applicant Source** (via workspace links) |

Also created role **QD Recruitment Officer** and workspace **QD Recruitment**.

### Open in Desk
Awesome Bar → workspace **Recruitment** (or **QD Background Check**)  
Also: **QD HR Dashboard** shortcuts.

### Typical hiring flow (Quick Delivery)
1. Manager creates **Job Requisition** (link **QD Position**, set Urgency)
2. HR approves requisition → creates **Job Opening** (same QD Position auto-fills dept/designation)
3. Applicants enter via **Job Applicant** (or website form if published)
4. HR screens (score + notes) → schedules **Interview**
5. **QD Background Check** for riders/drivers (license, references)
6. **Job Offer** → accepted applicant → **Employee Onboarding** (2.5)

### Refresh recruitment module setup
```bash
bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.recruitment.run
bench build --app qd_hrms
bench --site qd.local clear-cache
```

### Next module
**2.6 Attendance and Time**

---

## Sitemap 2.5 — Onboarding and Probation (DONE)

| Sitemap item | Implementation |
|---|---|
| Onboarding Cases | Standard **Employee Onboarding** |
| Task Checklists | Onboarding **Activities** table + template **QD Standard Onboarding** |
| Document Collection | Checklist flag + **QD Employee Document** |
| Account and Workspace Readiness | Checklist flags on Employee Onboarding |
| Equipment Assignment | Checklist flag + **Asset Movement** (Issue) when Assets installed |
| Orientation | Checklist flag + template activity |
| Policy Acknowledgements | Checklist flag + **QD Employee Document** (Policy type) |
| Probation Objectives | Child table on **QD Probation Review** |
| Probation Reviews | Custom **QD Probation Review** |
| Confirmation / Extension / Termination | Decision on review → updates Employee probation fields |

Also created workspace **QD Onboarding** and Employee fields: Probation Status, Period, End Date.

### Open in Desk
Awesome Bar → **Employee Lifecycle** (onboarding) or **QD Probation Review**  
Also: **QD HR Dashboard** shortcuts.

### Typical flow
1. After Job Offer accepted → **New Onboarding** (use template **QD Standard Onboarding**)
2. Tick QD checklist items (docs, account, equipment, orientation, policies)
3. Complete activities → create **Employee** from onboarding
4. Set Employee **User ID** + Probation months → status **In Probation**
5. Manager/HR create **QD Probation Review** (objectives + decision)
6. Approve review:
   - **Confirm** → Confirmation Date + status Confirmed
   - **Extend** → new Probation End Date
   - **Terminate** → status Terminated (then open Employee Separation if needed)

### Refresh onboarding module setup
```bash
bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.onboarding.run
bench build --app qd_hrms
bench --site qd.local clear-cache
```

---

## Sitemap 2.6 — Attendance and Time (DONE)

| Sitemap item | Implementation |
|---|---|
| Attendance Dashboard | Cards on **QD HR / Manager / Employee** dashboards + workspace **Shift & Attendance** |
| Shift Management | Standard **Shift Type** (seeded: QD Morning/Afternoon/Night) |
| Shift Assignments | Standard **Shift Assignment** / **Shift Request** |
| Attendance Records | Standard **Attendance** + QD overtime/zone notes |
| Biometric / File Imports | **QD Biometric Device** registry + standard **Upload Attendance** / Checkin `device_id` |
| Web and Mobile Check-in | Standard **Employee Checkin** + QD source/hub fields |
| Attendance Corrections | Standard **Attendance Request** |
| Overtime | `custom_qd_overtime_hours` on Attendance (payroll link later) |
| Timesheets | Standard **Timesheet** (Projects) |
| Period Lock | Use standard attendance tools / company processes |
| Attendance Reports | Standard reports under **Shift & Attendance** |

**No QD Attendance workspace** (Option B).

### Open in Desk
Awesome Bar → **Shift & Attendance**  
Or from **QD HR Dashboard** → Attendance / Checkin / Biometric Device.

### Typical flow
1. Create/confirm **Shift Type** (QD Morning Hub, etc.)
2. **Shift Assignment** for riders/hub staff
3. Register hub device in **QD Biometric Device** (integration later)
4. Daily: **Employee Checkin** (Web/Mobile/Biometric) → **Attendance**
5. Corrections via **Attendance Request**
6. Optional: **Timesheet** for project/ops hours

### Refresh attendance setup
```bash
bench --site qd.local migrate
bench --site qd.local execute qd_hrms.setup.attendance.run
bench build --app qd_hrms
bench --site qd.local clear-cache
```

### Next module
**2.9 Performance Management**

---

## Sitemap 2.7 — Leave Management (DONE)

| Sitemap item | Implementation |
|---|---|
| Leave Requests | Standard **Leave Application** + delivery/coverage fields |
| Leave Approvals | Leave Approver / Manager via standard workflow |
| Leave Balances | **Leave Allocation** + reports |
| Team Leave Calendar | Reports / Leave list filters |
| Public Holidays | **Holiday List** |
| Leave Policies | **Leave Policy** / **Leave Period** |
| Leave Adjustments | Allocation / Encashment / Compensatory Leave |
| Leave Reports | Standard under workspace **Leaves** |

Seeded Leave Types (if missing): Annual, Sick, Unpaid, Emergency.

**No QD Leave workspace** — use **Leaves**.

### Open in Desk
Awesome Bar → **Leaves**  
Or **HR Dashboard** → Leave card.

### Typical flow
1. Setup Holiday List + Leave Period + Leave Types  
2. Leave Policy / Allocation for employees  
3. Employee submits Leave Application (set coverage for riders)  
4. Manager approves  

```bash
bench --site qd.local execute qd_hrms.setup.leave.run
```

---

## Sitemap 2.8 — Payroll, Compensation and Benefits (DONE)

| Sitemap item | Implementation |
|---|---|
| Payroll Dashboard | Workspace **Payroll** + cards on HR dashboards |
| Pay Groups | Employee field **Pay Group** (Monthly Office / Ops / Weekly Rider) |
| Salary Structures | Standard **Salary Structure** + Assignment |
| Earning / Deduction Types | **Salary Component** (seeded Basic, Transport, OT, Tax, Pension…) |
| Benefits | Tax & Benefits workspace / Employee Benefit docs |
| Loans and Advances | **Employee Advance** / Loan (standard) |
| Payroll Inputs | **Additional Salary** (+ reason code / ops ref) |
| Preview / Approval / Lock | **Payroll Entry** (+ Ops Inputs Validated flag) |
| Payslips | **Salary Slip** (+ staff category / hub) |
| Bank / Statutory Exports | Bank remittance reports + Bank Export Code on Employee |
| Payroll Reports | Salary Register / Bank Remittance (standard) |

Role profile **Payroll Officer** added (`QD Payroll Officer`).

**No QD Payroll workspace** — use **Payroll**.

### Open in Desk
Awesome Bar → **Payroll** / **Salary Payout**  
Or **HR Dashboard** → Payroll & Benefits.

### Typical flow
1. Create Salary Components / Structure / assign to employees  
2. Enter Additional Salary (overtime, incentives)  
3. Payroll Entry for the period → validate ops inputs → create slips  
4. Submit slips → bank export reports  

```bash
bench --site qd.local execute qd_hrms.setup.payroll.run
```

---

## Sitemap 2.9 — Performance Management (DONE)

| Sitemap item | Implementation |
|---|---|
| Goals / KPIs | Standard **Goal** (+ category / ops metric fields) |
| Appraisals | Standard **Appraisal** (+ staff category, hub, delivery KPI notes, PIP flag) |
| Cycles / Templates | **Appraisal Cycle** / **Appraisal Template** |
| Feedback | **Employee Performance Feedback** |
| Promotion | **Employee Promotion** |
| Energy Points | Standard Energy Point System (optional) |
| PIP | Custom **QD Performance Improvement Plan** (UI: PIP) |
| Recognition / Awards | Custom **QD Recognition Award** (UI: Recognition) |

**No QD Performance workspace** — use **Performance**.

### Open in Desk
Awesome Bar → **Performance**  
Or **HR Dashboard** → Performance card / **Manager Dashboard** → PIP / Appraisals.

### Typical flow
1. Create Appraisal Cycle + Template  
2. Set Goals (delivery KPI categories for riders)  
3. Run Appraisals; mark PIP Required when needed → Start PIP  
4. Log Recognition awards for excellence  

```bash
bench --site qd.local execute qd_hrms.setup.performance.run
```

---

## Sitemap 2.10 — Learning & Development (DONE)

| Sitemap item | Implementation |
|---|---|
| Training Catalog | **Training Program** (+ category, target staff, mandatory) |
| Sessions | **Training Event** (+ hub, capacity, mandatory) |
| Nomination / Approval | Custom **QD Training Request** (UI: Training Request) |
| Feedback / Results | **Training Feedback** / **Training Result** |
| Skills | **Employee Skill Map** |
| Seeded programs | Rider Safety Induction, Customer Service Essentials, Hub Operations Basics |

**No QD Learning workspace** — search Training docs / HR Dashboard → Learning.

### Open in Desk
Awesome Bar → **Training Program** / **Training Event** / **Training Request**  
Or **Employee Dashboard** → Training Request.

### Typical flow
1. Confirm / edit seeded Training Programs  
2. Employee or manager creates Training Request → Pending Approval → Approved  
3. Schedule Training Event and enroll employees; set request to Enrolled  
4. Capture Feedback / Result; maintain Skill Map  

```bash
bench --site qd.local execute qd_hrms.setup.learning.run
```

### Next module
**2.13 Employee Requests**

---

## Sitemap 2.11 — Employee Relations (DONE)

| Sitemap item | Implementation |
|---|---|
| Disciplinary Cases | Custom **QD Disciplinary Case** |
| Grievances / Complaints | Custom **QD Grievance** (Type = Grievance or Complaint) |
| Investigations / Evidence / Participants | Sections + child tables on both DocTypes |
| Hearings / Employee Responses | Fields on Disciplinary Case |
| Appeals | Appeal section on Disciplinary Case |
| Warning / Decision Letters | Decision + Attach on Disciplinary Case |
| Case Closure | Status Closed + closure notes |

**No QD Employee Relations workspace** — use **HR Dashboard** → Employee Relations.

```bash
bench --site qd.local execute qd_hrms.setup.employee_relations.run
```

---

## Sitemap 2.12 — Asset Management (DONE)

| Sitemap item | Implementation |
|---|---|
| Asset Categories / Inventory | Standard **Asset Category** / **Asset** (+ QD equipment fields) |
| Assignment / Transfer / Return | **Asset Movement** (Issue / Transfer / Receipt) + reason codes |
| Maintenance | **Asset Maintenance** / **Asset Repair** |
| Loss / Damage / Recovery | Custom **QD Asset Incident** |
| Asset Reports | Standard Assets reports |

Categories seeded by cloning the first existing Asset Category’s accounts (Uniforms, Delivery Bags, Phones and Devices, Vehicles and Bikes, Hub Equipment) when at least one category already exists.

**No QD Assets workspace** — use **Assets**.

```bash
bench --site qd.local execute qd_hrms.setup.assets.run
```

### Next module
**2.13 Employee Requests**

---

## First customization session (older checklist)

1. Confirm Desk → Awesome Bar → search **QD HRMS** / **QD HR Dashboard**  
2. Customize Form → **Employee** → add 2–3 QD fields (e.g. delivery zone, device id)  
3. Create DocType **QD Employee Request** in module QD HRMS  
4. Add Workflow Draft → Pending → Approved  
5. `bench --site qd.local export-fixtures`  
6. Commit + push `qd_hrms` to GitHub  

You are ready to customize — stay inside `qd_hrms` and you remain upgrade-compatible with the community.
