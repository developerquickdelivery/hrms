"""Dedicated Employee Relations Case Management setup."""

from __future__ import annotations

import json

import frappe

WORKFLOW = "QD HR Case Lifecycle"
WORKSPACE = "Employee Relations"


def run():
	ensure_workflow()
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


def ensure_workflow():
	from qd_hrms.setup.performance import _ensure_simple_workflow

	hr_roles = ("HR User", "HR Manager", "System Manager")
	hr_managers = ("HR Manager", "System Manager")

	_ensure_simple_workflow(
		WORKFLOW,
		"QD HR Case",
		"case_status",
		[
			("Draft", "0", "Inverse", "HR User"),
			("Open", "0", "Primary", "HR User"),
			("Under Investigation", "0", "Warning", "HR User"),
			("Hearing Scheduled", "0", "Warning", "HR User"),
			("Awaiting Response", "0", "Warning", "HR User"),
			("Decision Issued", "0", "Info", "HR Manager"),
			("Appealed", "0", "Warning", "HR Manager"),
			("Closed", "1", "Success", "HR Manager"),
			("Withdrawn", "0", "Inverse", "HR User"),
		],
		[
			(("Draft", "Open Case", "Open"), hr_roles),
			(("Open", "Start Investigation", "Under Investigation"), hr_roles),
			(("Open", "Issue Decision", "Decision Issued"), hr_managers),
			(("Under Investigation", "Schedule Hearing", "Hearing Scheduled"), hr_roles),
			(("Under Investigation", "Issue Decision", "Decision Issued"), hr_managers),
			(("Hearing Scheduled", "Request Employee Response", "Awaiting Response"), hr_roles),
			(("Hearing Scheduled", "Issue Decision", "Decision Issued"), hr_managers),
			(("Awaiting Response", "Issue Decision", "Decision Issued"), hr_managers),
			(("Decision Issued", "File Appeal", "Appealed"), hr_roles),
			(("Decision Issued", "Close Case", "Closed"), hr_managers),
			(("Appealed", "Close Case", "Closed"), hr_managers),
			(("Draft", "Withdraw", "Withdrawn"), hr_roles),
			(("Open", "Withdraw", "Withdrawn"), hr_managers),
		],
		extra_actions=(
			"Open Case",
			"Start Investigation",
			"Schedule Hearing",
			"Request Employee Response",
			"Issue Decision",
			"File Appeal",
			"Close Case",
		),
	)


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
	doc.icon = "review"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	content = [
		_block("header", {"text": '<span class="h4"><b>Employee Relations</b></span>', "col": 12})
	]
	for label, target, color in (
		("HR Cases", "QD HR Case", "Blue"),
		("Disciplinary Cases", "QD Disciplinary Case", "Red"),
		("Grievances", "QD Grievance", "Orange"),
		("Complaints", "QD Complaint", "Orange"),
	):
		doc.append(
			"shortcuts",
			{"type": "DocType", "link_to": target, "doc_view": "List", "label": label, "color": color},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))
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
			"QD Grievance": ["read", "write", "create", "submit"],
			"QD Complaint": ["read", "write", "create", "submit"],
		},
		doc,
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {
		"QD HR Case",
		"QD Disciplinary Case",
		"QD Grievance",
		"QD Complaint",
		"QD Case Participant",
		"QD Case Evidence",
		"QD Case Hearing",
		"QD Case Employee Response",
	}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing Employee Relations DocTypes: {', '.join(missing)}")
	if frappe.db.get_value("Workflow", WORKFLOW, "is_active") != 1:
		raise frappe.ValidationError("HR Case lifecycle workflow is inactive")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Employee Relations workspace missing")
	return {
		"created": sorted(required),
		"workflow": WORKFLOW,
		"workspace": WORKSPACE,
		"verified": True,
	}
