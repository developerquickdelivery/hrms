"""Customize standard Employee Promotion and configure its approval workflow."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

WORKFLOW_NAME = "QD Employee Promotion Approval"
WORKFLOW_FIELD = "custom_qd_approval_status"


def run():
	create_custom_fields(_fields(), ignore_validate=True, update=True)
	ensure_manager_permission()
	ensure_workflow_masters()
	ensure_workflow()
	frappe.clear_cache(doctype="Employee Promotion")
	return {
		"doctype": "Employee Promotion",
		"workflow": WORKFLOW_NAME,
		"workflow_field": WORKFLOW_FIELD,
	}


def _fields():
	return {
		"Employee Promotion": [
			{
				"fieldname": WORKFLOW_FIELD,
				"fieldtype": "Select",
				"label": "Approval Status",
				"options": "\nDraft\nSubmitted\nManager Approval\nHR Approval\nApproved\nEffective",
				"default": "Draft",
				"insert_after": "company",
				"read_only": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "custom_qd_manager_approver",
				"fieldtype": "Link",
				"label": "Manager Approver",
				"options": "User",
				"insert_after": WORKFLOW_FIELD,
				"read_only": 1,
			},
			{
				"fieldname": "custom_qd_target_section",
				"fieldtype": "Section Break",
				"label": "Promotion Targets",
				"insert_after": "custom_qd_manager_approver",
			},
			{
				"fieldname": "custom_qd_new_position",
				"fieldtype": "Link",
				"label": "New Position",
				"options": "QD Position",
				"insert_after": "custom_qd_target_section",
			},
			{
				"fieldname": "custom_qd_new_grade",
				"fieldtype": "Link",
				"label": "New Grade",
				"options": "Employee Grade",
				"insert_after": "custom_qd_new_position",
			},
			{
				"fieldname": "custom_qd_new_department",
				"fieldtype": "Link",
				"label": "New Department",
				"options": "Department",
				"insert_after": "custom_qd_new_grade",
			},
			{
				"fieldname": "custom_qd_target_column",
				"fieldtype": "Column Break",
				"insert_after": "custom_qd_new_department",
			},
			{
				"fieldname": "custom_qd_new_manager",
				"fieldtype": "Link",
				"label": "New Manager",
				"options": "Employee",
				"insert_after": "custom_qd_target_column",
			},
			{
				"fieldname": "custom_qd_new_salary_structure",
				"fieldtype": "Link",
				"label": "New Salary Structure",
				"options": "Salary Structure",
				"insert_after": "custom_qd_new_manager",
			},
			{
				"fieldname": "custom_qd_new_base_salary",
				"fieldtype": "Currency",
				"label": "New Base Salary",
				"options": "salary_currency",
				"insert_after": "custom_qd_new_salary_structure",
			},
			{
				"allow_on_submit": 1,
				"fieldname": "custom_qd_salary_structure_assignment",
				"fieldtype": "Link",
				"label": "Salary Structure Assignment",
				"options": "Salary Structure Assignment",
				"insert_after": "custom_qd_new_base_salary",
				"read_only": 1,
			},
		]
	}


def ensure_manager_permission():
	"""Workflow state/condition limits Employee write access to the exact manager."""
	if not frappe.db.exists("Role", "Employee"):
		return
	if not frappe.db.exists(
		"Custom DocPerm",
		{"parent": "Employee Promotion", "role": "Employee", "permlevel": 0, "if_owner": 0},
	):
		add_permission("Employee Promotion", "Employee", 0)
	update_permission_property("Employee Promotion", "Employee", 0, "read", 1)
	update_permission_property("Employee Promotion", "Employee", 0, "write", 1)


def ensure_workflow_masters():
	for name, style in (
		("Draft", "Inverse"),
		("Submitted", "Warning"),
		("Manager Approval", "Warning"),
		("HR Approval", "Warning"),
		("Approved", "Success"),
		("Effective", "Primary"),
	):
		if not frappe.db.exists("Workflow State", name):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": name, "style": style}
			).insert(ignore_permissions=True)

	for action in (
		"Submit for Review",
		"Request Manager Approval",
		"Manager Approve",
		"HR Approve",
		"Make Effective",
	):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)


def ensure_workflow():
	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		doc = frappe.get_doc("Workflow", WORKFLOW_NAME)
		doc.set("states", [])
		doc.set("transitions", [])
	else:
		doc = frappe.new_doc("Workflow")
		doc.workflow_name = WORKFLOW_NAME

	doc.document_type = "Employee Promotion"
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = WORKFLOW_FIELD
	if doc.meta.has_field("override_status"):
		doc.override_status = 0

	for other in frappe.get_all(
		"Workflow",
		filters={
			"document_type": "Employee Promotion",
			"name": ["!=", WORKFLOW_NAME],
			"is_active": 1,
		},
		pluck="name",
	):
		frappe.db.set_value("Workflow", other, "is_active", 0)

	states = [
		("Draft", "0", "Inverse", "HR User"),
		("Submitted", "0", "Warning", "HR User"),
		("Manager Approval", "0", "Warning", "Employee"),
		("HR Approval", "0", "Warning", "HR Manager"),
		("Approved", "0", "Success", "HR Manager"),
		("Effective", "1", "Primary", "HR Manager"),
	]
	for state, docstatus, style, allow_edit in states:
		doc.append(
			"states",
			{
				"state": state,
				"doc_status": docstatus,
				"style": style,
				"allow_edit": allow_edit,
			},
		)

	def add_transition(state, action, next_state, role, condition=None, allow_self=0):
		if not frappe.db.exists("Role", role):
			return
		doc.append(
			"transitions",
			{
				"state": state,
				"action": action,
				"next_state": next_state,
				"allowed": role,
				"condition": condition,
				"allow_self_approval": allow_self,
			},
		)

	for role in ("HR User", "HR Manager", "System Manager"):
		add_transition("Draft", "Submit for Review", "Submitted", role, allow_self=1)
		add_transition(
			"Submitted",
			"Request Manager Approval",
			"Manager Approval",
			role,
			allow_self=1,
		)

	manager_condition = "doc.custom_qd_manager_approver == frappe.session.user"
	for role in ("Employee", "Leave Approver", "HR Manager"):
		add_transition(
			"Manager Approval",
			"Manager Approve",
			"HR Approval",
			role,
			condition=manager_condition,
		)
	add_transition(
		"Manager Approval",
		"Manager Approve",
		"HR Approval",
		"System Manager",
		allow_self=1,
	)

	for role in ("HR Manager", "System Manager"):
		add_transition("HR Approval", "HR Approve", "Approved", role, allow_self=1)
		add_transition("Approved", "Make Effective", "Effective", role, allow_self=1)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
