"""Employee Separation extensions, clearance automation, and completion gates."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now, nowdate


SEPARATION_TYPES = (
	"Resignation",
	"Termination",
	"Retirement",
	"Redundancy",
	"Contract Completion",
)


def validate_employee_separation(doc, method=None):
	if doc.custom_qd_separation_type not in SEPARATION_TYPES:
		frappe.throw(_("Select a valid Separation Type."))
	if not doc.custom_qd_final_working_date:
		frappe.throw(_("Final Working Date is required."))
	joining_date = frappe.db.get_value("Employee", doc.employee, "date_of_joining")
	if joining_date and getdate(doc.custom_qd_final_working_date) < getdate(joining_date):
		frappe.throw(_("Final Working Date cannot be before Date of Joining."))


def on_employee_separation_submit(doc, method=None):
	if doc.custom_qd_exit_clearance:
		return
	clearance = _make_clearance(doc)
	doc.db_set("custom_qd_exit_clearance", clearance.name, update_modified=False)
	doc.db_set("custom_qd_lifecycle_status", "Clearance", update_modified=False)


def on_employee_separation_cancel(doc, method=None):
	doc.db_set("custom_qd_lifecycle_status", "Cancelled", update_modified=False)
	if doc.custom_qd_exit_clearance and frappe.db.exists(
		"QD Exit Clearance", doc.custom_qd_exit_clearance
	):
		clearance = frappe.get_doc("QD Exit Clearance", doc.custom_qd_exit_clearance)
		clearance.db_set("clearance_status", "Reopened", update_modified=False)
		for row in clearance.clearance_items:
			if row.task and frappe.db.exists("Task", row.task):
				frappe.db.set_value("Task", row.task, "status", "Cancelled")


def _make_clearance(separation):
	existing = frappe.db.get_value(
		"QD Exit Clearance", {"employee_separation": separation.name}, "name"
	)
	if existing:
		return frappe.get_doc("QD Exit Clearance", existing)
	employee = frappe.db.get_value(
		"Employee", separation.employee, ["reports_to", "user_id"], as_dict=True
	)
	manager_user = employee.reports_to and frappe.db.get_value(
		"Employee", employee.reports_to, "user_id"
	)
	rows = (
		("HR", "Confirm separation documents and employee records", _role_user(("HR User", "HR Manager"))),
		("Manager", "Complete handover and confirm outstanding work", manager_user),
		("Finance", "Clear advances, expenses, loans, and final financial obligations", _role_user(("Accounts User", "Accounts Manager"))),
		("IT", "Recover equipment and schedule system access deactivation", _role_user(("System Manager",))),
		("Asset Management", "Recover and verify all assigned company assets", _role_user(("Asset Manager",))),
		("Administration", "Recover IDs, keys, documents, and facility access", _role_user(("HR User", "HR Manager"))),
	)
	clearance = frappe.new_doc("QD Exit Clearance")
	clearance.employee_separation = separation.name
	clearance.separation_type = separation.custom_qd_separation_type
	clearance.final_working_date = separation.custom_qd_final_working_date
	clearance.due_date = separation.custom_qd_final_working_date or add_days(nowdate(), 7)
	for department, item, user in rows:
		clearance.append(
			"clearance_items",
			{
				"clearance_department": department,
				"clearance_item": item,
				"responsible_user": user,
				"status": "Pending",
			},
		)
	clearance.insert(ignore_permissions=True)
	return clearance


def _role_user(roles):
	for role in roles:
		users = frappe.get_all(
			"Has Role",
			filters={"role": role, "parenttype": "User"},
			pluck="parent",
		)
		for user in users:
			if user != "Administrator" and frappe.db.get_value("User", user, "enabled"):
				return user
	return "Administrator"


def sync_clearance_from_task(doc, method=None):
	clearance_name = doc.get("custom_qd_exit_clearance")
	if not clearance_name or not frappe.db.exists("QD Exit Clearance", clearance_name):
		return
	row = frappe.db.get_value(
		"QD Exit Clearance Item",
		{"parent": clearance_name, "task": doc.name},
		"name",
	)
	if not row:
		return
	status = {
		"Open": "Pending",
		"Working": "In Progress",
		"Pending Review": "In Progress",
		"Completed": "Cleared",
		"Cancelled": "Exception",
	}.get(doc.status)
	if not status:
		return
	frappe.db.set_value("QD Exit Clearance Item", row, "status", status, update_modified=False)
	clearance = frappe.get_doc("QD Exit Clearance", clearance_name)
	clearance.save(ignore_permissions=True)


@frappe.whitelist()
def advance_separation_stage(separation, action):
	doc = frappe.get_doc("Employee Separation", separation)
	doc.check_permission("write")
	stage = doc.custom_qd_lifecycle_status

	if action == "final_payroll":
		_assert_stage(stage, "Final Payroll")
		if not (doc.custom_qd_final_payroll_reference_doctype and doc.custom_qd_final_payroll_reference):
			frappe.throw(_("Final Payroll reference is required."))
		doc.db_set(
			{
				"custom_qd_final_payroll_completed": 1,
				"custom_qd_final_payroll_completed_on": now(),
				"custom_qd_lifecycle_status": "Exit Interview",
			}
		)
	elif action == "exit_interview":
		_assert_stage(stage, "Exit Interview")
		if not doc.exit_interview:
			frappe.throw(_("Exit Interview Summary is required."))
		doc.db_set(
			{
				"custom_qd_exit_interview_completed": 1,
				"custom_qd_exit_interview_completed_on": now(),
				"custom_qd_lifecycle_status": "Access Deactivation",
			}
		)
	elif action == "deactivate_access":
		_assert_stage(stage, "Access Deactivation")
		user = frappe.db.get_value("Employee", doc.employee, "user_id")
		if user and user not in ("Administrator", "Guest"):
			frappe.db.set_value("User", user, "enabled", 0)
		doc.db_set(
			{
				"custom_qd_access_deactivated": 1,
				"custom_qd_access_deactivated_by": frappe.session.user,
				"custom_qd_access_deactivated_on": now(),
				"custom_qd_lifecycle_status": "Records Preservation",
			}
		)
	elif action == "preserve_records":
		_assert_stage(stage, "Records Preservation")
		if not doc.custom_qd_records_location:
			frappe.throw(_("Records Preservation Location is required."))
		doc.db_set(
			{
				"custom_qd_records_preserved": 1,
				"custom_qd_records_preserved_by": frappe.session.user,
				"custom_qd_records_preserved_on": now(),
				"custom_qd_lifecycle_status": "Separation Complete",
				"custom_qd_completed_on": now(),
			}
		)
		frappe.db.set_value(
			"Employee",
			doc.employee,
			{
				"status": "Left",
				"relieving_date": doc.custom_qd_final_working_date,
			},
		)
	else:
		frappe.throw(_("Unsupported separation action."))
	return doc.custom_qd_lifecycle_status


def _assert_stage(actual, expected):
	if actual != expected:
		frappe.throw(
			_("This action requires stage {0}; current stage is {1}.").format(expected, actual)
		)


def separation_query(user):
	return _employee_query("Employee Separation", user)


def clearance_query(user):
	return _employee_query("QD Exit Clearance", user)


def _employee_query(doctype, user):
	from qd_hrms.self_service import get_session_employee, is_privileged

	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	return f"`tab{doctype}`.`employee` = {frappe.db.escape(employee)}"


def has_separation_permission(doc, ptype=None, user=None, debug=False):
	from qd_hrms.self_service import get_session_employee, is_privileged

	user = user or frappe.session.user
	if is_privileged(user):
		return None
	return doc.get("employee") == get_session_employee(user) and ptype in (None, "read", "print")
