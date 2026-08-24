"""Quick Delivery organizational master data.

Creates the 8 QD departments, 6 employee grades, 25 designations, and
25 QD Position headcount seats with full reporting hierarchy.

Run via:
    bench --site <site> execute qd_hrms.setup.org_data.run
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

COMPANY = "Quick Delivery"

# ────────────────────────────────────────────────────────────────────
# 1. Departments
# ────────────────────────────────────────────────────────────────────

QD_DEPARTMENTS = (
	"Executive Management",
	"Human Resources",
	"Information Technology",
	"Finance",
	"Operations",
	"Marketing & Business Development",
	"Merchant Management",
	"ERP Development Division",
)

# ────────────────────────────────────────────────────────────────────
# 2. Employee Grades
# ────────────────────────────────────────────────────────────────────

QD_GRADES = (
	{"name": "Grade 1 - Entry", "code": "QD-G1", "level": 1, "category": "Entry"},
	{"name": "Grade 2 - Officer", "code": "QD-G2", "level": 2, "category": "Operational"},
	{"name": "Grade 3 - Intermediate", "code": "QD-G3", "level": 3, "category": "Professional"},
	{"name": "Grade 4 - Supervisor", "code": "QD-G4", "level": 4, "category": "Supervisory"},
	{"name": "Grade 5 - Manager", "code": "QD-G5", "level": 5, "category": "Management"},
	{"name": "Grade 6 - Executive", "code": "QD-G6", "level": 6, "category": "Executive"},
)

# ────────────────────────────────────────────────────────────────────
# 3. Designations  (name, grade, eligible_for_acting)
# ────────────────────────────────────────────────────────────────────

QD_DESIGNATIONS = (
	# Executive Management
	("General Manager", "Grade 6 - Executive", True),
	# Human Resources
	("HR Manager", "Grade 5 - Manager", True),
	("HR Officer", "Grade 2 - Officer", False),
	# Information Technology
	("IT Manager", "Grade 5 - Manager", True),
	("System Administrator", "Grade 4 - Supervisor", False),
	("System Support Officer", "Grade 2 - Officer", False),
	# Finance
	("Finance Manager", "Grade 5 - Manager", True),
	("Senior Finance Officer", "Grade 3 - Intermediate", False),
	("Junior Finance Officer", "Grade 1 - Entry", False),
	# Operations
	("Operations Supervisor", "Grade 4 - Supervisor", True),
	("Operations Coordinator", "Grade 2 - Officer", False),
	("Fleet Coordinator", "Grade 2 - Officer", False),
	("Order Processor", "Grade 2 - Officer", False),
	# Marketing & Business Development
	("Business Development Officer", "Grade 2 - Officer", False),
	("Marketing Officer", "Grade 2 - Officer", False),
	# Merchant Management
	("Merchant Officer", "Grade 2 - Officer", False),
	("Junior Merchant Officer", "Grade 1 - Entry", False),
	# ERP Development Division
	("Product Manager", "Grade 4 - Supervisor", False),
	("Senior Full Stack Developer", "Grade 3 - Intermediate", False),
	("Intermediate Full Stack Developer", "Grade 3 - Intermediate", False),
	("Junior Developer", "Grade 1 - Entry", False),
	("QA Engineer", "Grade 2 - Officer", False),
	("UI/UX Designer", "Grade 2 - Officer", False),
	("Business Analyst", "Grade 2 - Officer", False),
)

# ────────────────────────────────────────────────────────────────────
# 4. Positions  (position_name, code, designation, department, grade, reports_to_position)
# ────────────────────────────────────────────────────────────────────

QD_POSITIONS = (
	# Executive Management
	("General Manager", "QD-POS-001", "General Manager", "Executive Management", "Grade 6 - Executive", None),
	# Human Resources
	("HR Manager", "QD-POS-002", "HR Manager", "Human Resources", "Grade 5 - Manager", "General Manager"),
	("HR Officer", "QD-POS-003", "HR Officer", "Human Resources", "Grade 2 - Officer", "HR Manager"),
	# Information Technology
	("IT Manager", "QD-POS-004", "IT Manager", "Information Technology", "Grade 5 - Manager", "General Manager"),
	("System Administrator", "QD-POS-005", "System Administrator", "Information Technology", "Grade 4 - Supervisor", "IT Manager"),
	("System Support Officer", "QD-POS-006", "System Support Officer", "Information Technology", "Grade 2 - Officer", "IT Manager"),
	# Finance
	("Finance Manager", "QD-POS-007", "Finance Manager", "Finance", "Grade 5 - Manager", "General Manager"),
	("Senior Finance Officer", "QD-POS-008", "Senior Finance Officer", "Finance", "Grade 3 - Intermediate", "Finance Manager"),
	("Junior Finance Officer", "QD-POS-009", "Junior Finance Officer", "Finance", "Grade 1 - Entry", "Finance Manager"),
	# Operations
	("Operations Supervisor", "QD-POS-010", "Operations Supervisor", "Operations", "Grade 4 - Supervisor", "General Manager"),
	("Operations Coordinator", "QD-POS-011", "Operations Coordinator", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
	("Fleet Coordinator", "QD-POS-012", "Fleet Coordinator", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
	("Order Processor", "QD-POS-013", "Order Processor", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
	# Marketing & Business Development
	("Business Development Officer", "QD-POS-014", "Business Development Officer", "Marketing & Business Development", "Grade 2 - Officer", "General Manager"),
	("Marketing Officer", "QD-POS-015", "Marketing Officer", "Marketing & Business Development", "Grade 2 - Officer", "General Manager"),
	# Merchant Management
	("Merchant Officer", "QD-POS-016", "Merchant Officer", "Merchant Management", "Grade 2 - Officer", "General Manager"),
	("Junior Merchant Officer", "QD-POS-017", "Junior Merchant Officer", "Merchant Management", "Grade 1 - Entry", "Merchant Officer"),
	# ERP Development Division
	("Product Manager", "QD-POS-018", "Product Manager", "ERP Development Division", "Grade 4 - Supervisor", "General Manager"),
	("Senior Full Stack Developer", "QD-POS-019", "Senior Full Stack Developer", "ERP Development Division", "Grade 3 - Intermediate", "Product Manager"),
	("Intermediate Full Stack Developer", "QD-POS-020", "Intermediate Full Stack Developer", "ERP Development Division", "Grade 3 - Intermediate", "Product Manager"),
	("Junior Developer", "QD-POS-021", "Junior Developer", "ERP Development Division", "Grade 1 - Entry", "Product Manager"),
	("QA Engineer", "QD-POS-022", "QA Engineer", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
	("UI/UX Designer", "QD-POS-023", "UI/UX Designer", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
	("Business Analyst", "QD-POS-024", "Business Analyst", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
)


# ════════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════════

def run():
	"""Idempotent master-data provisioning. Safe to re-run."""
	_ensure_designation_active_field()
	result = {
		"departments": _setup_departments(),
		"grades": _setup_grades(),
		"designations": _setup_designations(),
		"positions": _setup_positions(),
	}
	frappe.db.commit()
	frappe.clear_cache()
	return result


# ────────────────────────────────────────────────────────────────────
# Designation active field (schema addition)
# ────────────────────────────────────────────────────────────────────

def _ensure_designation_active_field():
	"""Add custom_qd_is_active Check to Designation so old samples can be disabled."""
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


# ────────────────────────────────────────────────────────────────────
# Departments
# ────────────────────────────────────────────────────────────────────

def _get_root_department(company, abbr):
	for candidate in (
		f"{company} - {abbr}",
		f"All Departments - {abbr}",
		"All Departments",
	):
		if frappe.db.exists("Department", candidate):
			return candidate
	roots = frappe.get_all(
		"Department",
		filters={"is_group": 1, "company": company},
		pluck="name",
	)
	if roots:
		return roots[0]
	return None


def _setup_departments():
	"""Disable default sample departments and create the 8 QD departments."""
	company = COMPANY
	abbr = frappe.db.get_value("Company", company, "abbr") or "QD"
	root_dept = _get_root_department(company, abbr)

	# Build set of QD department internal names (e.g. "Human Resources - QD")
	qd_dept_names = set()
	for dept_name in QD_DEPARTMENTS:
		qd_dept_names.add(f"{dept_name} - {abbr}")

	# Disable all existing leaf departments that are NOT in the QD list
	existing = frappe.get_all(
		"Department",
		filters={"company": company, "is_group": 0},
		fields=["name", "disabled"],
	)
	disabled_count = 0
	for dept in existing:
		if dept.name not in qd_dept_names and not dept.disabled:
			frappe.db.set_value("Department", dept.name, "disabled", 1)
			disabled_count += 1

	# Create QD departments
	created = []
	for dept_name in QD_DEPARTMENTS:
		full_name = f"{dept_name} - {abbr}"
		if frappe.db.exists("Department", full_name):
			# Re-enable if it was previously disabled
			frappe.db.set_value("Department", full_name, "disabled", 0)
			continue
		doc_data = {
			"doctype": "Department",
			"department_name": dept_name,
			"company": company,
			"is_group": 0,
		}
		if root_dept:
			doc_data["parent_department"] = root_dept
		doc = frappe.get_doc(doc_data)
		doc.flags.ignore_links = True
		doc.insert(ignore_permissions=True)
		created.append(doc.name)

	return {"disabled": disabled_count, "created": created}


# ────────────────────────────────────────────────────────────────────
# Employee Grades
# ────────────────────────────────────────────────────────────────────

def _setup_grades():
	"""Create 6 employee grades with QD-specific metadata."""
	created = []
	for grade in QD_GRADES:
		if frappe.db.exists("Employee Grade", grade["name"]):
			# Update existing
			doc = frappe.get_doc("Employee Grade", grade["name"])
		else:
			doc = frappe.get_doc({"doctype": "Employee Grade", "name": grade["name"]})
			doc.name = grade["name"]
			created.append(grade["name"])

		if doc.meta.has_field("custom_qd_grade_code"):
			doc.custom_qd_grade_code = grade["code"]
		if doc.meta.has_field("custom_qd_grade_level"):
			doc.custom_qd_grade_level = grade["level"]
		if doc.meta.has_field("custom_qd_grade_category"):
			doc.custom_qd_grade_category = grade["category"]
		if doc.meta.has_field("custom_qd_is_active"):
			doc.custom_qd_is_active = 1

		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)

	return {"created": created, "total": len(QD_GRADES)}


# ────────────────────────────────────────────────────────────────────
# Designations
# ────────────────────────────────────────────────────────────────────

def _setup_designations():
	"""Disable default sample designations and create 25 QD designations."""
	qd_names = {d[0] for d in QD_DESIGNATIONS}

	# Mark all existing designations that are NOT in the QD list as inactive
	existing = frappe.get_all("Designation", pluck="name")
	disabled_count = 0
	for name in existing:
		if name not in qd_names:
			if frappe.get_meta("Designation").has_field("custom_qd_is_active"):
				frappe.db.set_value("Designation", name, "custom_qd_is_active", 0)
				disabled_count += 1

	# Create QD designations
	created = []
	for desig_name, grade_name, eligible_acting in QD_DESIGNATIONS:
		if frappe.db.exists("Designation", desig_name):
			doc = frappe.get_doc("Designation", desig_name)
		else:
			doc = frappe.get_doc({"doctype": "Designation", "designation": desig_name})
			created.append(desig_name)

		# Set grade link
		if doc.meta.has_field("custom_qd_default_employee_grade"):
			doc.custom_qd_default_employee_grade = grade_name
		# Set active flag
		if doc.meta.has_field("custom_qd_is_active"):
			doc.custom_qd_is_active = 1
		# Set acting eligibility
		if doc.meta.has_field("custom_qd_eligible_for_acting"):
			doc.custom_qd_eligible_for_acting = 1 if eligible_acting else 0

		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)

	return {"disabled": disabled_count, "created": created}


# ────────────────────────────────────────────────────────────────────
# QD Positions
# ────────────────────────────────────────────────────────────────────

def _setup_positions():
	"""Create 25 QD Position headcount seats with reporting hierarchy."""
	company = COMPANY
	abbr = frappe.db.get_value("Company", company, "abbr") or "QD"

	created = []
	for pos_name, pos_code, designation, dept_short, grade, reports_to in QD_POSITIONS:
		department = f"{dept_short} - {abbr}"

		if frappe.db.exists("QD Position", pos_name):
			doc = frappe.get_doc("QD Position", pos_name)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "QD Position",
					"position_name": pos_name,
				}
			)
			created.append(pos_name)

		doc.position_code = pos_code
		doc.active = 1
		doc.company = company
		doc.designation = designation
		doc.employee_grade = grade
		doc.department = department
		doc.reports_to_position = reports_to or ""

		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)

	return {"created": created, "total": len(QD_POSITIONS)}
