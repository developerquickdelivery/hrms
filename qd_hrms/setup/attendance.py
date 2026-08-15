"""Attendance Request correction workflow, period lock, and biometric registry."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

WORKFLOW_NAME = "QD Attendance Correction"
REASON_OPTIONS = "\n".join(
	[
		"Work From Home",
		"On Duty",
		"Missed Punch",
		"Wrong Status",
		"Device Failure",
		"Shift Coverage",
		"Other",
	]
)
CORRECTION_TYPES = "\n".join(
	["", "Missed Punch", "Wrong Status", "Device Failure", "Shift Coverage", "Other"]
)


def run():
	ensure_custom_fields()
	ensure_reason_options()
	ensure_permissions()
	ensure_workflow_masters()
	ensure_workflow()
	from qd_hrms.setup.attendance_time import run as run_attendance_time

	extensions = run_attendance_time()
	frappe.clear_cache()
	return {
		"workflow": WORKFLOW_NAME,
		"period_lock": "Attendance Period",
		"biometric_device": "QD Biometric Device",
		"active": frappe.db.get_value("Workflow", WORKFLOW_NAME, "is_active"),
		"extensions": extensions,
	}


def ensure_custom_fields():
	create_custom_fields(_fields(), ignore_validate=True, update=True)


def _fields():
	return {
		"Attendance Request": [
			{
				"fieldname": "custom_qd_correction_section",
				"fieldtype": "Section Break",
				"label": "Correction Details",
				"insert_after": "explanation",
			},
			{
				"fieldname": "custom_qd_correction_type",
				"fieldtype": "Select",
				"label": "Correction Type",
				"options": CORRECTION_TYPES,
				"insert_after": "custom_qd_correction_section",
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "custom_qd_requested_status",
				"fieldtype": "Select",
				"label": "Requested Attendance Status",
				"options": "Present\nAbsent\nHalf Day\nWork From Home\nOn Leave",
				"insert_after": "custom_qd_correction_type",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"reqd": 1,
			},
			{
				"fieldname": "custom_qd_status",
				"fieldtype": "Select",
				"label": "Correction Status",
				"options": "Pending\nApproved\nRejected\nWithdrawn\nCancelled",
				"default": "Pending",
				"insert_after": "custom_qd_requested_status",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"read_only": 1,
				"allow_on_submit": 1,
			},
			{
				"fieldname": "custom_qd_correction_col",
				"fieldtype": "Column Break",
				"insert_after": "custom_qd_status",
			},
			{
				"fieldname": "custom_qd_original_status",
				"fieldtype": "Small Text",
				"label": "Original Attendance",
				"insert_after": "custom_qd_correction_col",
				"read_only": 1,
				"description": "Summary of submitted Attendance records in the correction date range.",
			},
		],
		"Attendance": [
			{
				"fieldname": "custom_qd_overtime_hours",
				"fieldtype": "Float",
				"label": "Overtime Hours",
				"insert_after": "working_hours",
				"precision": "2",
			},
			{
				"fieldname": "custom_qd_zone_notes",
				"fieldtype": "Small Text",
				"label": "Hub / Zone Notes",
				"insert_after": "early_exit",
			},
		],
		"Employee Checkin": [
			{
				"fieldname": "custom_qd_source",
				"fieldtype": "Select",
				"label": "Source",
				"options": "\nWeb\nMobile\nBiometric\nImport",
				"insert_after": "device_id",
				"in_standard_filter": 1,
			},
			{
				"fieldname": "custom_qd_biometric_device",
				"fieldtype": "Link",
				"label": "Biometric Device",
				"options": "QD Biometric Device",
				"insert_after": "custom_qd_source",
			},
		],
	}


def ensure_reason_options():
	existing = frappe.db.exists(
		"Property Setter",
		{"doc_type": "Attendance Request", "field_name": "reason", "property": "options"},
	)
	if existing:
		ps = frappe.get_doc("Property Setter", existing)
		ps.value = REASON_OPTIONS
		ps.save(ignore_permissions=True)
		return
	frappe.get_doc(
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Attendance Request",
			"field_name": "reason",
			"property": "options",
			"property_type": "Small Text",
			"value": REASON_OPTIONS,
		}
	).insert(ignore_permissions=True)


def ensure_permissions():
	role_flags = {
		"HR Manager": {
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 1,
			"submit": 1,
			"cancel": 1,
			"amend": 1,
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
			"submit": 1,
			"cancel": 1,
			"amend": 0,
			"print": 1,
			"email": 1,
			"report": 1,
			"export": 1,
			"share": 1,
		},
		"Leave Approver": {
			"read": 1,
			"write": 1,
			"create": 0,
			"delete": 0,
			"submit": 1,
			"cancel": 0,
			"amend": 0,
			"print": 1,
			"email": 1,
			"report": 1,
			"export": 0,
			"share": 0,
		},
		"Employee": {
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 0,
			"submit": 0,
			"cancel": 0,
			"amend": 0,
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
			add_permission("Attendance Request", role, 0)
		except Exception:
			pass
		for ptype, value in flags.items():
			try:
				update_permission_property("Attendance Request", role, 0, ptype, value)
			except Exception:
				pass


def ensure_workflow_masters():
	for name, style in (
		("Pending", "Warning"),
		("Approved", "Success"),
		("Rejected", "Danger"),
		("Withdrawn", "Inverse"),
		("Cancelled", "Inverse"),
	):
		if not frappe.db.exists("Workflow State", name):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": name, "style": style}
			).insert(ignore_permissions=True)

	for action in ("Approve", "Reject", "Cancel", "Reopen"):
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

	doc.document_type = "Attendance Request"
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = "workflow_state"
	if doc.meta.has_field("override_status"):
		doc.override_status = 0

	for other in frappe.get_all(
		"Workflow",
		filters={"document_type": "Attendance Request", "name": ["!=", WORKFLOW_NAME], "is_active": 1},
		pluck="name",
	):
		frappe.db.set_value("Workflow", other, "is_active", 0)

	# Approved is submitted so core Attendance Request.on_submit creates/updates Attendance.
	states = [
		("Pending", "0", "Warning", "Employee", "Pending"),
		("Approved", "1", "Success", "HR User", "Approved"),
		("Rejected", "0", "Danger", "Employee", "Rejected"),
		("Withdrawn", "0", "Inverse", "Employee", "Withdrawn"),
		("Cancelled", "2", "Inverse", "HR User", "Cancelled"),
	]
	for state, docstatus, style, allow_edit, status_value in states:
		doc.append(
			"states",
			{
				"state": state,
				"doc_status": docstatus,
				"style": style,
				"allow_edit": allow_edit,
				"update_field": "custom_qd_status",
				"update_value": status_value,
			},
		)

	def add_transition(state, action, next_state, role, allow_self=0):
		if not frappe.db.exists("Role", role):
			return
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

	for role in ("Leave Approver", "HR User", "HR Manager", "System Manager"):
		add_transition("Pending", "Approve", "Approved", role)
		add_transition("Pending", "Reject", "Rejected", role)
		add_transition("Rejected", "Reopen", "Pending", role)
		add_transition("Approved", "Cancel", "Cancelled", role)

	add_transition("Pending", "Cancel", "Withdrawn", "Employee", 1)
	add_transition("Pending", "Cancel", "Withdrawn", "HR User")
	add_transition("Pending", "Cancel", "Withdrawn", "HR Manager")
	add_transition("Pending", "Cancel", "Withdrawn", "System Manager")
	add_transition("Rejected", "Cancel", "Withdrawn", "Employee", 1)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
