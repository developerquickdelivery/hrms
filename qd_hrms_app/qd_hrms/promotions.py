"""QD workflow extensions for standard HRMS Employee Promotion."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

TARGET_FIELDS = (
	("custom_qd_new_position", "custom_qd_position"),
	("custom_qd_new_grade", "grade"),
	("custom_qd_new_department", "department"),
	("custom_qd_new_manager", "reports_to"),
)


def validate_promotion(doc, method=None):
	employee = frappe.get_doc("Employee", doc.employee)
	_set_manager_approver(doc, employee)
	_apply_position_defaults(doc)
	_apply_grade_salary_defaults(doc)
	_resolve_salary_structure(doc)
	_sync_standard_promotion_details(doc, employee)
	_validate_has_changes(doc)

	if (
		doc.get("custom_qd_approval_status") == "Manager Approval"
		and not doc.get("custom_qd_manager_approver")
		and frappe.session.user != "Administrator"
		and "System Manager" not in frappe.get_roles()
	):
		frappe.throw(
			_(
				"The employee's current Manager has no linked User account. "
				"Link a User to the manager or ask a System Manager to approve."
			)
		)


def on_promotion_submit(doc, method=None):
	if not doc.get("custom_qd_new_base_salary"):
		return

	existing = frappe.db.get_value(
		"Salary Structure Assignment",
		{
			"employee": doc.employee,
			"from_date": doc.promotion_date,
			"docstatus": ("!=", 2),
		},
		["name", "docstatus", "salary_structure", "base"],
		as_dict=True,
	)
	if existing and existing.docstatus == 1:
		if (
			existing.salary_structure != doc.custom_qd_new_salary_structure
			or flt(existing.base) != flt(doc.custom_qd_new_base_salary)
		):
			frappe.throw(
				_(
					"Submitted Salary Structure Assignment {0} already exists "
					"for the Promotion Date."
				).format(existing.name)
			)
		doc.db_set("custom_qd_salary_structure_assignment", existing.name)
		return

	if existing:
		assignment = frappe.get_doc("Salary Structure Assignment", existing.name)
	else:
		assignment = frappe.new_doc("Salary Structure Assignment")

	assignment.employee = doc.employee
	assignment.salary_structure = doc.custom_qd_new_salary_structure
	assignment.from_date = doc.promotion_date
	assignment.company = doc.company
	assignment.base = doc.custom_qd_new_base_salary
	assignment.save(ignore_permissions=True)
	assignment.submit()
	doc.db_set("custom_qd_salary_structure_assignment", assignment.name)


def on_promotion_cancel(doc, method=None):
	name = doc.get("custom_qd_salary_structure_assignment")
	if not name or not frappe.db.exists("Salary Structure Assignment", name):
		return
	assignment = frappe.get_doc("Salary Structure Assignment", name)
	if assignment.docstatus == 1:
		assignment.cancel()


@frappe.whitelist()
def get_position_defaults(position: str):
	if not set(frappe.get_roles()) & {"System Manager", "HR Manager", "HR User"}:
		frappe.throw(_("Not permitted to read position defaults."), frappe.PermissionError)
	if not position:
		return {}
	row = frappe.db.get_value(
		"QD Position",
		position,
		["department", "employee_grade", "reports_to_position"],
		as_dict=True,
	)
	if not row:
		return {}
	return {
		"department": row.department,
		"grade": row.employee_grade,
		"manager": _manager_for_position(row.reports_to_position),
		**_grade_salary_defaults(row.employee_grade),
	}


def _set_manager_approver(doc, employee):
	manager = employee.reports_to
	doc.custom_qd_manager_approver = (
		frappe.db.get_value("Employee", manager, "user_id") if manager else None
	)


def _apply_position_defaults(doc):
	position = doc.get("custom_qd_new_position")
	if not position:
		return
	defaults = get_position_defaults(position)
	if defaults.get("department") and not doc.get("custom_qd_new_department"):
		doc.custom_qd_new_department = defaults["department"]
	if defaults.get("grade") and not doc.get("custom_qd_new_grade"):
		doc.custom_qd_new_grade = defaults["grade"]
	if defaults.get("manager") and not doc.get("custom_qd_new_manager"):
		doc.custom_qd_new_manager = defaults["manager"]
	if defaults.get("salary_structure") and not doc.get("custom_qd_new_salary_structure"):
		doc.custom_qd_new_salary_structure = defaults["salary_structure"]
	if defaults.get("base") and not doc.get("custom_qd_new_base_salary"):
		doc.custom_qd_new_base_salary = defaults["base"]


def _apply_grade_salary_defaults(doc):
	grade = doc.get("custom_qd_new_grade")
	if not grade:
		return
	defaults = _grade_salary_defaults(grade)
	if defaults.get("salary_structure") and not doc.get("custom_qd_new_salary_structure"):
		doc.custom_qd_new_salary_structure = defaults["salary_structure"]
	if defaults.get("base") and not doc.get("custom_qd_new_base_salary"):
		doc.custom_qd_new_base_salary = defaults["base"]


def _grade_salary_defaults(grade: str | None):
	if not grade:
		return {}
	row = frappe.db.get_value(
		"Employee Grade",
		grade,
		["default_salary_structure", "default_base_pay"],
		as_dict=True,
	)
	if not row:
		return {}
	return {
		"salary_structure": row.default_salary_structure,
		"base": row.default_base_pay,
	}


def _resolve_salary_structure(doc):
	base = doc.get("custom_qd_new_base_salary")
	structure = doc.get("custom_qd_new_salary_structure")
	if not base and not structure:
		return

	if not structure:
		structure = frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": doc.employee, "docstatus": 1},
			"salary_structure",
			order_by="from_date desc",
		)
		doc.custom_qd_new_salary_structure = structure
	if not base:
		frappe.throw(_("New Base Salary is required when changing Salary Structure."))
	if not structure:
		frappe.throw(_("New Salary Structure is required when changing Base Salary."))


def _sync_standard_promotion_details(doc, employee):
	for source_field, employee_field in TARGET_FIELDS:
		new_value = doc.get(source_field)
		if not new_value:
			continue
		meta_field = employee.meta.get_field(employee_field)
		if not meta_field:
			continue
		current_value = employee.get(employee_field)
		row = next(
			(item for item in doc.promotion_details if item.fieldname == employee_field),
			None,
		)
		if not row:
			row = doc.append("promotion_details", {})
		row.fieldname = employee_field
		row.property = meta_field.label
		row.current = current_value
		row.new = new_value


def _validate_has_changes(doc):
	if not doc.promotion_details and not doc.get("custom_qd_new_base_salary") and not doc.revised_ctc:
		frappe.throw(_("Add at least one Position, Grade, Department, Manager, or Salary change."))


def _manager_for_position(reports_to_position: str | None):
	if not reports_to_position:
		return None
	return frappe.db.get_value(
		"Employee",
		{"custom_qd_position": reports_to_position, "status": "Active"},
		"name",
	)
