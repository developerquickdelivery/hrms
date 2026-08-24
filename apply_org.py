import frappe

SITE = "hrms.quickdelivery6484.com"
frappe.init(site=SITE)
frappe.connect()

# 1. Company Detection
companies = frappe.get_all("Company", fields=["name", "abbr"])
if not companies:
    print("ERROR: No company found!")
    exit(1)

COMPANY = companies[0].name
abbr = companies[0].abbr
print(f"Target Company: '{COMPANY}' (Abbr: '{abbr}') on site: '{SITE}'")

# 2. Custom Fields
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
create_custom_fields(
    {
        "Designation": [
            {
                "fieldname": "custom_qd_is_active",
                "fieldtype": "Check",
                "label": "Active",
                "default": "1",
                "insert_after": "designation_name",
                "in_list_view": 1,
                "in_standard_filter": 1,
            }
        ]
    },
    ignore_validate=True,
    update=True,
)

# 3. Departments
DEPTS = [
    "Executive Management",
    "Human Resources",
    "Information Technology",
    "Finance",
    "Operations",
    "Marketing & Business Development",
    "Merchant Management",
    "ERP Development Division",
]
root = frappe.get_all("Department", filters={"is_group": 1, "company": COMPANY}, pluck="name")
root_dept = root[0] if root else None
qd_depts = {f"{d} - {abbr}" for d in DEPTS}

print("Disabling default non-QD departments...")
for d in frappe.get_all("Department", filters={"company": COMPANY, "is_group": 0}, pluck="name"):
    if d not in qd_depts:
        frappe.db.set_value("Department", d, "disabled", 1)

print("Provisioning 8 QD Departments...")
for d in DEPTS:
    name = f"{d} - {abbr}"
    if frappe.db.exists("Department", name):
        frappe.db.set_value("Department", name, "disabled", 0)
    else:
        doc = frappe.get_doc({
            "doctype": "Department",
            "department_name": d,
            "company": COMPANY,
            "is_group": 0,
            "parent_department": root_dept,
        })
        doc.flags.ignore_links = True
        doc.insert(ignore_permissions=True)

# 4. Employee Grades
GRADES = [
    ("Grade 1 - Entry", "QD-G1", 1, "Entry"),
    ("Grade 2 - Officer", "QD-G2", 2, "Operational"),
    ("Grade 3 - Intermediate", "QD-G3", 3, "Professional"),
    ("Grade 4 - Supervisor", "QD-G4", 4, "Supervisory"),
    ("Grade 5 - Manager", "QD-G5", 5, "Management"),
    ("Grade 6 - Executive", "QD-G6", 6, "Executive"),
]
print("Provisioning 6 Employee Grades...")
for gname, gcode, glvl, gcat in GRADES:
    if frappe.db.exists("Employee Grade", gname):
        doc = frappe.get_doc("Employee Grade", gname)
    else:
        doc = frappe.get_doc({"doctype": "Employee Grade", "name": gname})
    if doc.meta.has_field("custom_qd_grade_code"): doc.custom_qd_grade_code = gcode
    if doc.meta.has_field("custom_qd_grade_level"): doc.custom_qd_grade_level = glvl
    if doc.meta.has_field("custom_qd_grade_category"): doc.custom_qd_grade_category = gcat
    if doc.meta.has_field("custom_qd_is_active"): doc.custom_qd_is_active = 1
    doc.flags.ignore_links = True
    doc.save(ignore_permissions=True)

# 5. Designations
DESIGS = [
    ("General Manager", "Grade 6 - Executive", 1),
    ("HR Manager", "Grade 5 - Manager", 1),
    ("HR Officer", "Grade 2 - Officer", 0),
    ("IT Manager", "Grade 5 - Manager", 1),
    ("System Administrator", "Grade 4 - Supervisor", 0),
    ("System Support Officer", "Grade 2 - Officer", 0),
    ("Finance Manager", "Grade 5 - Manager", 1),
    ("Senior Finance Officer", "Grade 3 - Intermediate", 0),
    ("Junior Finance Officer", "Grade 1 - Entry", 0),
    ("Operations Supervisor", "Grade 4 - Supervisor", 1),
    ("Operations Coordinator", "Grade 2 - Officer", 0),
    ("Fleet Coordinator", "Grade 2 - Officer", 0),
    ("Order Processor", "Grade 2 - Officer", 0),
    ("Business Development Officer", "Grade 2 - Officer", 0),
    ("Marketing Officer", "Grade 2 - Officer", 0),
    ("Merchant Officer", "Grade 2 - Officer", 0),
    ("Junior Merchant Officer", "Grade 1 - Entry", 0),
    ("Product Manager", "Grade 4 - Supervisor", 0),
    ("Senior Full Stack Developer", "Grade 3 - Intermediate", 0),
    ("Intermediate Full Stack Developer", "Grade 3 - Intermediate", 0),
    ("Junior Developer", "Grade 1 - Entry", 0),
    ("QA Engineer", "Grade 2 - Officer", 0),
    ("UI/UX Designer", "Grade 2 - Officer", 0),
    ("Business Analyst", "Grade 2 - Officer", 0),
]
active_desigs = {d[0] for d in DESIGS}
print("Deactivating default designations...")
for d in frappe.get_all("Designation", pluck="name"):
    if d not in active_desigs and frappe.get_meta("Designation").has_field("custom_qd_is_active"):
        frappe.db.set_value("Designation", d, "custom_qd_is_active", 0)

print("Provisioning 24 QD Designations...")
for dname, dgrd, dact in DESIGS:
    if frappe.db.exists("Designation", dname):
        doc = frappe.get_doc("Designation", dname)
    else:
        doc = frappe.get_doc({"doctype": "Designation", "designation": dname})
    if doc.meta.has_field("custom_qd_default_employee_grade"): doc.custom_qd_default_employee_grade = dgrd
    if doc.meta.has_field("custom_qd_is_active"): doc.custom_qd_is_active = 1
    if doc.meta.has_field("custom_qd_eligible_for_acting"): doc.custom_qd_eligible_for_acting = dact
    doc.flags.ignore_links = True
    doc.save(ignore_permissions=True)

# 6. Positions
POSITIONS = [
    ("General Manager", "QD-POS-001", "General Manager", "Executive Management", "Grade 6 - Executive", None),
    ("HR Manager", "QD-POS-002", "HR Manager", "Human Resources", "Grade 5 - Manager", "General Manager"),
    ("HR Officer", "QD-POS-003", "HR Officer", "Human Resources", "Grade 2 - Officer", "HR Manager"),
    ("IT Manager", "QD-POS-004", "IT Manager", "Information Technology", "Grade 5 - Manager", "General Manager"),
    ("System Administrator", "QD-POS-005", "System Administrator", "Information Technology", "Grade 4 - Supervisor", "IT Manager"),
    ("System Support Officer", "QD-POS-006", "System Support Officer", "Information Technology", "Grade 2 - Officer", "IT Manager"),
    ("Finance Manager", "QD-POS-007", "Finance Manager", "Finance", "Grade 5 - Manager", "General Manager"),
    ("Senior Finance Officer", "QD-POS-008", "Senior Finance Officer", "Finance", "Grade 3 - Intermediate", "Finance Manager"),
    ("Junior Finance Officer", "QD-POS-009", "Junior Finance Officer", "Finance", "Grade 1 - Entry", "Finance Manager"),
    ("Operations Supervisor", "QD-POS-010", "Operations Supervisor", "Operations", "Grade 4 - Supervisor", "General Manager"),
    ("Operations Coordinator", "QD-POS-011", "Operations Coordinator", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
    ("Fleet Coordinator", "QD-POS-012", "Fleet Coordinator", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
    ("Order Processor", "QD-POS-013", "Order Processor", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
    ("Business Development Officer", "QD-POS-014", "Business Development Officer", "Marketing & Business Development", "Grade 2 - Officer", "General Manager"),
    ("Marketing Officer", "QD-POS-015", "Marketing Officer", "Marketing & Business Development", "Grade 2 - Officer", "General Manager"),
    ("Merchant Officer", "QD-POS-016", "Merchant Officer", "Merchant Management", "Grade 2 - Officer", "General Manager"),
    ("Junior Merchant Officer", "QD-POS-017", "Junior Merchant Officer", "Merchant Management", "Grade 1 - Entry", "Merchant Officer"),
    ("Product Manager", "QD-POS-018", "Product Manager", "ERP Development Division", "Grade 4 - Supervisor", "General Manager"),
    ("Senior Full Stack Developer", "QD-POS-019", "Senior Full Stack Developer", "ERP Development Division", "Grade 3 - Intermediate", "Product Manager"),
    ("Intermediate Full Stack Developer", "QD-POS-020", "Intermediate Full Stack Developer", "ERP Development Division", "Grade 3 - Intermediate", "Product Manager"),
    ("Junior Developer", "QD-POS-021", "Junior Developer", "ERP Development Division", "Grade 1 - Entry", "Product Manager"),
    ("QA Engineer", "QD-POS-022", "QA Engineer", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
    ("UI/UX Designer", "QD-POS-023", "UI/UX Designer", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
    ("Business Analyst", "QD-POS-024", "Business Analyst", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
]
print("Provisioning 24 Headcount Positions...")
for pname, pcode, pdes, pdep, pgrd, prep in POSITIONS:
    if frappe.db.exists("QD Position", pname):
        doc = frappe.get_doc("QD Position", pname)
    else:
        doc = frappe.get_doc({"doctype": "QD Position", "position_name": pname})
    doc.position_code = pcode
    doc.active = 1
    doc.company = COMPANY
    doc.designation = pdes
    doc.employee_grade = pgrd
    doc.department = f"{pdep} - {abbr}"
    doc.reports_to_position = prep or ""
    doc.flags.ignore_links = True
    doc.save(ignore_permissions=True)

# 7. Leave Workflow
print("Configuring Leave Workflow...")
import qd_hrms.setup.leave
qd_hrms.setup.leave.run()

frappe.db.commit()
frappe.clear_cache()

print("\n========================================================")
print(f"  ORGANIZATION SETUP APPLIED FOR {COMPANY} ({abbr})!")
print("========================================================\n")
