"""Workforce Requisitions via standard Job Requisition + approval workflow."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

WORKFLOW_NAME = "QD Workforce Requisition"
STAFF_CATEGORIES = "\n".join(
	["", "Rider", "Dispatcher", "Driver", "Hub Staff", "Office Staff", "Management"]
)
URGENCY = "\n".join(["", "Normal", "Urgent", "Critical"])
REQUEST_TYPES = "\n".join(["", "New Headcount", "Replacement", "Temporary / Acting"])


def run():
	ensure_custom_fields()
	ensure_permissions()
	ensure_workflow_masters()
	ensure_workflow()
	frappe.clear_cache()
	return {
		"doctype": "Job Requisition",
		"workflow": WORKFLOW_NAME,
		"active": frappe.db.get_value("Workflow", WORKFLOW_NAME, "is_active"),
	}


def ensure_custom_fields():
	create_custom_fields(
		{
			"Job Requisition": [
				{
					"fieldname": "custom_qd_workforce_section",
					"fieldtype": "Section Break",
					"label": "Workforce Details",
					"insert_after": "department",
				},
				{
					"fieldname": "custom_qd_request_type",
					"fieldtype": "Select",
					"label": "Request Type",
					"options": REQUEST_TYPES,
					"insert_after": "custom_qd_workforce_section",
					"in_standard_filter": 1,
					"reqd": 1,
					"default": "New Headcount",
				},
				{
					"fieldname": "custom_qd_staff_category",
					"fieldtype": "Select",
					"label": "Staff Category",
					"options": STAFF_CATEGORIES,
					"insert_after": "custom_qd_request_type",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_urgency",
					"fieldtype": "Select",
					"label": "Urgency",
					"options": URGENCY,
					"insert_after": "custom_qd_staff_category",
					"in_list_view": 1,
					"in_standard_filter": 1,
					"default": "Normal",
				},
				{
					"fieldname": "custom_qd_workforce_col",
					"fieldtype": "Column Break",
					"insert_after": "custom_qd_urgency",
				},
				{
					"fieldname": "custom_qd_branch",
					"fieldtype": "Link",
					"label": "Branch",
					"options": "Branch",
					"insert_after": "custom_qd_workforce_col",
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_employment_type",
					"fieldtype": "Link",
					"label": "Employment Type",
					"options": "Employment Type",
					"insert_after": "custom_qd_branch",
				},
				{
					"fieldname": "custom_qd_replacement_for",
					"fieldtype": "Link",
					"label": "Replacement For",
					"options": "Employee",
					"insert_after": "custom_qd_employment_type",
					"depends_on": "eval:doc.custom_qd_request_type=='Replacement'",
					"mandatory_depends_on": "eval:doc.custom_qd_request_type=='Replacement'",
				},
			]
		},
		ignore_validate=True,
		update=True,
	)


def ensure_permissions():
	role_flags = {
		"HR Manager": {
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 1,
			"print": 1,
			"email": 1,
			"report": 1,
			"export": 1,
			"share": 1,
		},
		"HR User": {
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 0,
			"print": 1,
			"email": 1,
			"report": 1,
			"export": 1,
			"share": 1,
		},
		"Employee": {
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 0,
			"print": 1,
			"email": 1,
			"report": 0,
			"export": 0,
			"share": 0,
		},
	}
	for role, flags in role_flags.items():
		if not frappe.db.exists("Role", role):
			continue
		try:
			add_permission("Job Requisition", role, 0)
		except Exception as exc:
			if "Duplicate" not in str(exc) and "already exists" not in str(exc).lower():
				frappe.log_error(
					title=f"Job Requisition permission setup failed for {role}",
					message=frappe.get_traceback(),
				)
				raise
		for ptype, value in flags.items():
			try:
				update_permission_property("Job Requisition", role, 0, ptype, value)
			except Exception:
				frappe.log_error(
					title=f"Job Requisition {ptype} permission failed for {role}",
					message=frappe.get_traceback(),
				)
				raise


def ensure_workflow_masters():
	states = [
		("Pending", "Warning"),
		("Open & Approved", "Success"),
		("Rejected", "Danger"),
		("On Hold", "Inverse"),
		("Filled", "Primary"),
		("Cancelled", "Inverse"),
	]
	for name, style in states:
		if not frappe.db.exists("Workflow State", name):
			frappe.get_doc(
				{
					"doctype": "Workflow State",
					"workflow_state_name": name,
					"style": style,
				}
			).insert(ignore_permissions=True)

	for action in ("Approve", "Reject", "Hold", "Reopen", "Mark Filled", "Cancel"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)


def ensure_workflow():
	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		doc = frappe.get_doc("Workflow", WORKFLOW_NAME)
		doc.set("states", [])
		doc.set("transitions", [])
	else:
		doc = frappe.new_doc("Workflow")
		doc.workflow_name = WORKFLOW_NAME

	doc.document_type = "Job Requisition"
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = "workflow_state"
	if doc.meta.has_field("override_status"):
		doc.override_status = 0

	# Deactivate any other workflow on this doctype
	for other in frappe.get_all(
		"Workflow",
		filters={"document_type": "Job Requisition", "name": ["!=", WORKFLOW_NAME], "is_active": 1},
		pluck="name",
	):
		frappe.db.set_value("Workflow", other, "is_active", 0)

	states = [
		("Pending", "0", "Warning", "Employee"),
		("Open & Approved", "0", "Success", "HR User"),
		("Rejected", "0", "Danger", "HR User"),
		("On Hold", "0", "Inverse", "HR User"),
		("Filled", "0", "Primary", "HR User"),
		("Cancelled", "0", "Inverse", "HR User"),
	]
	for state, docstatus, style, allow_edit in states:
		doc.append(
			"states",
			{
				"state": state,
				"doc_status": docstatus,
				"style": style,
				"allow_edit": allow_edit,
				"update_field": "status",
				"update_value": state,
			},
		)

	def add_transition(state, action, next_state, role, allow_self=0):
		doc.append(
			"transitions",
			{
				"state": state,
				"action": action,
				"next_state": next_state,
				"allowed": role,
				"allow_self_approval": allow_self,
			},
		)

	for role in ("HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			add_transition("Pending", "Approve", "Open & Approved", role, 1)
			add_transition("Pending", "Reject", "Rejected", role, 1)
			add_transition("Open & Approved", "Hold", "On Hold", role, 1)
			add_transition("On Hold", "Reopen", "Open & Approved", role, 1)
			add_transition("Open & Approved", "Mark Filled", "Filled", role, 1)
			add_transition("Open & Approved", "Cancel", "Cancelled", role, 1)
			add_transition("Pending", "Cancel", "Cancelled", role, 1)

	if frappe.db.exists("Role", "Employee"):
		add_transition("Pending", "Cancel", "Cancelled", "Employee", 1)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
