"""HR Administration workspace over standard Frappe administration.

Users, Roles, Permissions, Authentication, Audit Logs, Backups, and APIs stay
on the stock Frappe engines; this only groups HR configuration in one place.
"""

from __future__ import annotations

import json

import frappe

WORKSPACE = "HR Administration"

# (section label, ((label, doctype), ...))
SECTIONS = (
	(
		"HR Settings",
		(
			("HR Settings", "HR Settings"),
			("Employee Self Service User Type", "User Type"),
		),
	),
	(
		"HR Master Data",
		(
			("Company", "Company"),
			("Department", "Department"),
			("Designation", "Designation"),
			("Employee Grade", "Employee Grade"),
			("Branch", "Branch"),
			("Employment Type", "Employment Type"),
			("Holiday List", "Holiday List"),
			("Employee", "Employee"),
		),
	),
	(
		"Approval Rules",
		(
			("Workflows", "Workflow"),
			("Workflow States", "Workflow State"),
			("Workflow Actions", "Workflow Action Master"),
			("Assignment Rules", "Assignment Rule"),
		),
	),
	(
		"Notification Rules",
		(
			("Notification Rules", "Notification"),
			("Email Templates", "Email Template"),
			("SMS Settings", "SMS Settings"),
		),
	),
	(
		"Leave Settings",
		(
			("Leave Type", "Leave Type"),
			("Leave Policy", "Leave Policy"),
			("Leave Period", "Leave Period"),
			("Leave Block List", "Leave Block List"),
		),
	),
	(
		"Payroll Settings",
		(
			("Payroll Settings", "Payroll Settings"),
			("Salary Component", "Salary Component"),
			("Salary Structure", "Salary Structure"),
			("Payroll Period", "Payroll Period"),
			("Income Tax Slab", "Income Tax Slab"),
		),
	),
	(
		"Recruitment Settings",
		(
			("Staffing Plan", "Staffing Plan"),
			("Interview Type", "Interview Type"),
			("Interview Round", "Interview Round"),
			("Job Offer Term Template", "Job Offer Term Template"),
			("Appointment Letter Template", "Appointment Letter Template"),
		),
	),
	(
		"Performance Settings",
		(
			("Appraisal Cycle", "Appraisal Cycle"),
			("Appraisal Template", "Appraisal Template"),
			("KRA", "KRA"),
			("Rating Scale", "QD Rating Scale"),
			("Feedback Criteria", "Employee Feedback Criteria"),
		),
	),
	(
		"Training Settings",
		(
			("Training Course", "QD Training Course"),
			("Training Program", "Training Program"),
		),
	),
	(
		"Document Settings",
		(
			("Document Settings", "QD Document Settings"),
			("Employee Documents", "QD Employee Document"),
			("HR Policies", "QD Policy"),
		),
	),
	(
		"Retention Settings",
		(
			("Retention Settings", "QD Retention Settings"),
			("Log Settings", "Log Settings"),
		),
	),
)


def run():
	ensure_workspace()
	frappe.clear_cache()
	return verify()


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
	doc.icon = "setting"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>HR Administration</b></span>', "col": 12},
		),
		_block(
			"paragraph",
			{
				"text": "Users, roles, permissions, authentication, audit logs, backups, and APIs remain in standard Frappe administration.",
				"col": 12,
			},
		),
	]

	for section_label, entries in SECTIONS:
		available = [
			(label, doctype)
			for label, doctype in entries
			if frappe.db.exists("DocType", doctype)
		]
		if not available:
			continue
		doc.append(
			"links",
			{
				"type": "Card Break",
				"label": section_label,
				"hidden": 0,
				"link_count": len(available),
			},
		)
		for label, doctype in available:
			doc.append(
				"links",
				{
					"type": "Link",
					"link_type": "DocType",
					"link_to": doctype,
					"label": label,
					"hidden": 0,
					"is_query_report": 0,
					"onboard": 0,
				},
			)
		content.append(_block("card", {"card_name": section_label, "col": 4}))

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
	for doctype in ("QD Document Settings", "QD Retention Settings"):
		if not frappe.db.exists("DocType", doctype):
			raise frappe.ValidationError(f"Missing settings DocType: {doctype}")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("HR Administration workspace missing")
	links = frappe.get_all(
		"Workspace Link",
		filters={"parent": WORKSPACE, "type": "Card Break"},
		pluck="label",
	)
	missing_sections = [label for label, _entries in SECTIONS if label not in links]
	if missing_sections:
		raise frappe.ValidationError(
			f"Missing workspace sections: {', '.join(missing_sections)}"
		)
	return {
		"kept": [
			"User",
			"Role",
			"Role Permission Manager",
			"Authentication",
			"Audit Trail / Activity Log",
			"Backups",
			"REST API",
		],
		"created": ["QD Document Settings", "QD Retention Settings", WORKSPACE],
		"sections": [label for label, _entries in SECTIONS],
		"verified": True,
	}
