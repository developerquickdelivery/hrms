"""Configurable Employee Request setup and lifecycle."""

from __future__ import annotations

import json

import frappe

WORKFLOW = "QD Employee Request Lifecycle"
WORKSPACE = "Employee Requests"


def run():
	ensure_request_types()
	ensure_workflow()
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


def ensure_request_types():
	request_types = (
		("HR Letter", "Request an employment, salary, service, or other HR letter.", 0, 0, None, "Medium", 3, None),
		("Profile Change", "Request a verified change to employee profile information.", 1, 1, "Reporting Manager", "Medium", 5, "Employee"),
		("Salary Advance", "Request an advance subject to company policy and payroll review.", 1, 1, "Reporting Manager", "High", 5, "Employee Advance"),
		("Benefit Enrollment", "Enroll in or change an eligible employee benefit.", 1, 1, "HR Manager", "Medium", 7, None),
		("Remote Work", "Request authorization to work remotely for a defined period.", 0, 1, "Reporting Manager", "Medium", 5, None),
		("Complaint", "Raise a confidential workplace complaint for HR processing.", 0, 1, "HR Manager", "High", 3, "QD Complaint"),
		("HR Support", "Ask HR for guidance or operational support.", 0, 0, None, "Medium", 3, None),
		("Custom Request", "Submit another employee request using a custom title.", 0, 1, "Reporting Manager", "Medium", 5, None),
	)
	for (
		name,
		description,
		attachment,
		approval,
		route,
		priority,
		sla,
		reference,
	) in request_types:
		if frappe.db.exists("QD Employee Request Type", name):
			continue
		frappe.get_doc(
			{
				"doctype": "QD Employee Request Type",
				"request_type": name,
				"description": description,
				"instructions": description,
				"requires_attachment": attachment,
				"requires_approval": approval,
				"approval_route": route,
				"default_priority": priority,
				"sla_days": sla,
				"suggested_reference_doctype": reference,
			}
		).insert(ignore_permissions=True)


def ensure_workflow():
	from qd_hrms.setup.performance import _ensure_simple_workflow

	_ensure_simple_workflow(
		WORKFLOW,
		"QD Employee Request",
		"workflow_state",
		[
			("Draft", "0", "Inverse", "Employee"),
			("Pending Validation", "0", "Warning", "HR User"),
			("Pending Approval", "0", "Warning", "Employee"),
			("HR Processing", "0", "Primary", "HR User"),
			("Completed", "1", "Success", "HR User"),
			("Rejected", "0", "Danger", "HR User"),
			("Withdrawn", "0", "Inverse", "Employee"),
		],
		[
			(("Draft", "Submit Request", "Pending Validation"), ("Employee", "HR User", "HR Manager", "System Manager")),
			(("Pending Validation", "Validate", "Pending Approval"), ("HR User", "HR Manager", "System Manager")),
			(("Pending Validation", "Validate & Process", "HR Processing"), ("HR User", "HR Manager", "System Manager")),
			(("Pending Validation", "Reject", "Rejected"), ("HR User", "HR Manager", "System Manager")),
			(("Pending Approval", "Approve", "HR Processing"), ("Employee", "HR User", "HR Manager", "System Manager")),
			(("Pending Approval", "Reject", "Rejected"), ("Employee", "HR User", "HR Manager", "System Manager")),
			(("HR Processing", "Complete", "Completed"), ("HR User", "HR Manager", "System Manager")),
			(("Draft", "Withdraw", "Withdrawn"), ("Employee", "HR User", "HR Manager", "System Manager")),
			(("Pending Validation", "Withdraw", "Withdrawn"), ("Employee", "HR User", "HR Manager", "System Manager")),
		],
		extra_actions=(
			"Submit Request",
			"Validate",
			"Validate & Process",
			"Complete",
		),
	)

	workflow = frappe.get_doc("Workflow", WORKFLOW)
	for row in workflow.transitions:
		if row.state == "Pending Validation" and row.action == "Validate":
			row.condition = "doc.requires_approval"
		elif row.state == "Pending Validation" and row.action == "Validate & Process":
			row.condition = "not doc.requires_approval"
		elif row.state == "Pending Approval" and row.action in ("Approve", "Reject"):
			row.allow_self_approval = 0
			if row.allowed in ("Employee", "HR User"):
				row.condition = "doc.approver == frappe.session.user"
			elif row.allowed == "HR Manager":
				row.condition = (
					"doc.approval_route == 'HR Manager' or "
					"doc.approver == frappe.session.user"
				)
	workflow.save(ignore_permissions=True)


def ensure_workspace():
	doc = (
		frappe.get_doc("Workspace", WORKSPACE)
		if frappe.db.exists("Workspace", WORKSPACE)
		else frappe.new_doc("Workspace")
	)
	if doc.is_new():
		doc.label = WORKSPACE
	doc.title = WORKSPACE
	doc.module = "QD HRMS"
	doc.icon = "list"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("Employee", "HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>Employee Requests</b></span>', "col": 12},
		)
	]
	for label, target, color in (
		("Employee Requests", "QD Employee Request", "Blue"),
		("Request Types", "QD Employee Request Type", "Grey"),
	):
		doc.append(
			"shortcuts",
			{
				"type": "DocType",
				"link_to": target,
				"doc_view": "List",
				"label": label,
				"color": color,
			},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 4}))
	doc.content = json.dumps(content)
	doc.flags.ignore_links = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def extend_ess():
	if not frappe.db.exists("User Type", "Employee Self Service"):
		return
	from hrms.setup import append_docperms_to_user_type

	doc = frappe.get_doc("User Type", "Employee Self Service")
	append_docperms_to_user_type(
		{
			"QD Employee Request Type": ["read"],
			"QD Employee Request": ["read", "write", "create"],
		},
		doc,
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {"QD Employee Request Type", "QD Employee Request"}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing Employee Request DocTypes: {', '.join(missing)}")
	missing_types = [
		name
		for name in (
			"HR Letter",
			"Profile Change",
			"Salary Advance",
			"Benefit Enrollment",
			"Remote Work",
			"Complaint",
			"HR Support",
			"Custom Request",
		)
		if not frappe.db.exists("QD Employee Request Type", name)
	]
	if missing_types:
		raise frappe.ValidationError(f"Missing request types: {', '.join(missing_types)}")
	if frappe.db.get_value("Workflow", WORKFLOW, "is_active") != 1:
		raise frappe.ValidationError("Employee Request workflow is inactive")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Employee Requests workspace missing")
	return {
		"created": sorted(required),
		"request_types": 8,
		"workflow": WORKFLOW,
		"workspace": WORKSPACE,
		"verified": True,
	}
