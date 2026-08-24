"""Configure QD leave policy, approval, balances, calendar and adjustments."""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

LEAVE_WORKFLOW = "QD Leave Application Approval"
ADJUSTMENT_WORKFLOW = "QD Leave Adjustment Approval"
WORKSPACE = "Leave and Team Calendar"
POLICY = "QD Standard Leave Policy"


def run():
	ensure_custom_fields()
	ensure_leave_types_and_policy()
	ensure_hr_settings()
	ensure_workflows()
	ensure_workspace()
	frappe.clear_cache()
	return verify()


def ensure_custom_fields():
	create_custom_fields(
		{
			"Leave Application": [
				{
					"fieldname": "custom_qd_coverage_section",
					"fieldtype": "Section Break",
					"label": "Work Coverage",
					"insert_after": "description",
					"collapsible": 1,
				},
				{
					"fieldname": "custom_qd_coverage_employee",
					"fieldtype": "Link",
					"label": "Covering Employee",
					"options": "Employee",
					"insert_after": "custom_qd_coverage_section",
				},
				{
					"fieldname": "custom_qd_coverage_notes",
					"fieldtype": "Small Text",
					"label": "Handover / Coverage Notes",
					"insert_after": "custom_qd_coverage_employee",
				},
				{
					"fieldname": "custom_qd_approval_status",
					"fieldtype": "Select",
					"label": "Approval Status",
					"options": "Draft\nPending Approval\nPending Final Approval\nApproved\nRejected\nWithdrawn\nCancelled",
					"default": "Draft",
					"read_only": 1,
					"insert_after": "status",
				},
			],
			"Leave Policy": [
				{
					"fieldname": "custom_qd_policy_description",
					"fieldtype": "Small Text",
					"label": "Policy Description",
					"insert_after": "title",
				}
			],
		},
		ignore_validate=True,
		update=True,
	)


def ensure_leave_types_and_policy():
	_upsert_leave_type("Sick Leave", max_leaves_allowed=180, include_holiday=1)
	_upsert_leave_type("Unpaid Leave", is_lwp=1, allow_negative=1)
	_upsert_leave_type("Emergency Leave", max_leaves_allowed=3)

	if not frappe.db.exists("Leave Policy", {"title": POLICY}):
		doc = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": POLICY,
				"custom_qd_policy_description": (
					"Operational baseline. HR must review allocations against the "
					"applicable employment contract and Ethiopian law before assignment."
				),
				"leave_policy_details": [
					{"leave_type": "Annual Leave", "annual_allocation": 16},
					{"leave_type": "Sick Leave", "annual_allocation": 30},
					{"leave_type": "Emergency Leave", "annual_allocation": 3},
				],
			}
		).insert(ignore_permissions=True)
		doc.submit()


def _upsert_leave_type(name, **values):
	doc = (
		frappe.get_doc("Leave Type", name)
		if frappe.db.exists("Leave Type", name)
		else frappe.get_doc({"doctype": "Leave Type", "leave_type_name": name})
	)
	for fieldname, value in values.items():
		if doc.meta.has_field(fieldname):
			doc.set(fieldname, value)
	doc.save(ignore_permissions=True)


def ensure_hr_settings():
	for fieldname, value in {
		"leave_approver_mandatory_in_leave_application": 1,
		"prevent_self_leave_approval": 1,
		"restrict_backdated_leave_application": 1,
		"role_allowed_to_create_backdated_leave_application": "HR Manager",
		"show_leaves_of_all_department_members_in_calendar": 1,
	}.items():
		if frappe.get_meta("HR Settings").has_field(fieldname):
			frappe.db.set_single_value("HR Settings", fieldname, value)


def ensure_workflows():
	ensure_workflow(
		LEAVE_WORKFLOW,
		"Leave Application",
		"custom_qd_approval_status",
		update_status=True,
	)
	ensure_workflow(
		ADJUSTMENT_WORKFLOW,
		"Leave Adjustment Request",
		"approval_status",
		update_status=False,
	)


def ensure_workflow(name, doctype, state_field, update_status=False):
	for state, style in (
		("Draft", "Inverse"),
		("Pending Approval", "Warning"),
		("Pending Final Approval", "Warning"),
		("Approved", "Success"),
		("Rejected", "Danger"),
		("Withdrawn", "Inverse"),
		("Cancelled", "Inverse"),
	):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)
	for action in (
		"Submit for Approval",
		"Approve",
		"Direct Approve",
		"Final Approve",
		"Reject",
		"Reopen",
		"Withdraw",
		"Cancel",
	):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)

	doc = frappe.get_doc("Workflow", name) if frappe.db.exists("Workflow", name) else frappe.new_doc("Workflow")
	if doc.is_new():
		doc.workflow_name = name
	doc.document_type = doctype
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = state_field
	doc.set("states", [])
	doc.set("transitions", [])

	states_config = (
		("Draft", "0", "Inverse", "Employee", "Open"),
		("Pending Approval", "0", "Warning", "Leave Approver", "Open"),
		("Pending Final Approval", "0", "Warning", "HR Manager", "Open"),
		("Approved", "1", "Success", "HR User", "Approved"),
		("Rejected", "0", "Danger", "Employee", "Rejected"),
		("Withdrawn", "0", "Inverse", "Employee", "Cancelled"),
		("Cancelled", "2", "Inverse", "HR User", "Cancelled"),
	)
	if name == ADJUSTMENT_WORKFLOW:
		states_config = (
			("Draft", "0", "Inverse", "Employee", "Draft"),
			("Pending Approval", "0", "Warning", "Leave Approver", "Pending Approval"),
			("Approved", "1", "Success", "HR User", "Approved"),
			("Rejected", "0", "Danger", "Employee", "Rejected"),
			("Withdrawn", "0", "Inverse", "Employee", "Withdrawn"),
			("Cancelled", "2", "Inverse", "HR User", "Cancelled"),
		)

	for state, docstatus, style, allow_edit, core_status in states_config:
		row = {
			"state": state,
			"doc_status": docstatus,
			"style": style,
			"allow_edit": allow_edit,
			"update_field": "status" if update_status else state_field,
			"update_value": core_status if update_status else state,
		}
		doc.append("states", row)

	def transition(state, action, next_state, role, allow_self=0):
		if frappe.db.exists("Role", role):
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

	requesters = ("Employee", "Employee Self Service", "HR User", "HR Manager", "System Manager")
	dept_approvers = ("Leave Approver", "HR User", "HR Manager", "System Manager")
	final_approvers = ("HR Manager", "System Manager")

	if name == LEAVE_WORKFLOW:
		for role in requesters:
			transition("Draft", "Submit for Approval", "Pending Approval", role, 1)
			transition("Draft", "Withdraw", "Withdrawn", role, 1)
			transition("Pending Approval", "Withdraw", "Withdrawn", role, 1)
			transition("Pending Final Approval", "Withdraw", "Withdrawn", role, 1)
		for role in dept_approvers:
			transition("Pending Approval", "Approve", "Pending Final Approval", role)
			transition("Pending Approval", "Reject", "Rejected", role)
			transition("Rejected", "Reopen", "Pending Approval", role)
		for role in final_approvers:
			transition("Pending Approval", "Direct Approve", "Approved", role)
			transition("Pending Final Approval", "Final Approve", "Approved", role)
			transition("Pending Final Approval", "Reject", "Rejected", role)
		for role in ("HR User", "HR Manager", "System Manager"):
			transition("Approved", "Cancel", "Cancelled", role)
	else:
		for role in requesters:
			transition("Draft", "Submit for Approval", "Pending Approval", role, 1)
			transition("Draft", "Withdraw", "Withdrawn", role, 1)
			transition("Pending Approval", "Withdraw", "Withdrawn", role, 1)
		for role in dept_approvers:
			transition("Pending Approval", "Approve", "Approved", role)
			transition("Pending Approval", "Reject", "Rejected", role)
			transition("Rejected", "Reopen", "Pending Approval", role)
		for role in ("HR User", "HR Manager", "System Manager"):
			transition("Approved", "Cancel", "Cancelled", role)

	doc.save(ignore_permissions=True)


def ensure_workspace():
	if frappe.db.exists("Workspace", WORKSPACE):
		doc = frappe.get_doc("Workspace", WORKSPACE)
		doc.shortcuts = []
		doc.links = []
		doc.roles = []
	else:
		doc = frappe.new_doc("Workspace")
		doc.label = WORKSPACE
	doc.title = WORKSPACE
	doc.module = "QD HRMS"
	doc.icon = "calendar"
	doc.public = 1
	doc.is_hidden = 0
	for role in ("HR User", "HR Manager", "Leave Approver", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	content = [_block("header", {"text": '<span class="h4"><b>Leave Management</b></span>', "col": 12})]
	for label, target, view, color in (
		("Team Leave Calendar", "Leave Application", "Calendar", "Blue"),
		("Leave Applications", "Leave Application", "List", "Blue"),
		("Leave Adjustments", "Leave Adjustment Request", "List", "Orange"),
		("Leave Policies", "Leave Policy", "List", "Grey"),
		("Leave Allocations", "Leave Allocation", "List", "Grey"),
		("Holiday Lists", "Holiday List", "List", "Grey"),
	):
		doc.append(
			"shortcuts",
			{"type": "DocType", "link_to": target, "doc_view": view, "label": label, "color": color},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))

	doc.append("links", {"type": "Card Break", "label": "Balances and Audit", "link_count": 3})
	for report in ("Employee Leave Balance", "Employee Leave Balance Summary", "Leave Ledger"):
		doc.append(
			"links",
			{
				"type": "Link",
				"link_type": "Report",
				"link_to": report,
				"label": report,
				"is_query_report": 1,
			},
		)
	content.extend(
		[
			_block("spacer", {"col": 12}),
			_block("header", {"text": '<span class="h4"><b>Balances and Audit</b></span>', "col": 12}),
			_block("card", {"card_name": "Balances and Audit", "col": 6}),
		]
	)
	doc.content = json.dumps(content)
	doc.flags.ignore_links = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {"Leave Adjustment Request", "Leave Adjustment Audit"}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing DocTypes: {', '.join(missing)}")
	for workflow in (LEAVE_WORKFLOW, ADJUSTMENT_WORKFLOW):
		if frappe.db.get_value("Workflow", workflow, "is_active") != 1:
			raise frappe.ValidationError(f"Inactive workflow: {workflow}")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Leave workspace is missing")
	return {
		"leave_types": ["Annual Leave", "Sick Leave", "Unpaid Leave", "Emergency Leave"],
		"workflows": [LEAVE_WORKFLOW, ADJUSTMENT_WORKFLOW],
		"workspace": WORKSPACE,
		"verified": True,
	}
