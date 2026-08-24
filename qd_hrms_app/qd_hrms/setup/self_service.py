"""My HR workspace, ESS User Type extras, and self-service field locks."""

from __future__ import annotations

import json

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.permissions import add_permission, update_permission_property

from qd_hrms.setup.bank_tax_pension import SENSITIVE_PERMLEVEL, SENSITIVE_ROLES

WORKSPACE_NAME = "My HR"
ESS_USER_TYPE = "Employee Self Service"

# Extra ESS DocTypes appended to HRMS defaults (never replace the shipped list).
ESS_EXTRA_DOCTYPES = {
	"Attendance": ["read"],
	"Appraisal": ["read", "write"],
	"Goal": ["read", "write", "create"],
	"Employee Performance Feedback": ["read", "write", "create", "submit"],
	"Energy Point Log": ["read"],
	"QD Performance Improvement Plan": ["read"],
	"KRA": ["read"],
	"Appraisal Cycle": ["read"],
	"Appraisal Template": ["read"],
	"Training Event": ["read"],
	"QD Training Course": ["read"],
	"Training Program": ["read"],
	"QD Training Request": ["read", "write", "create"],
	"QD Training Nomination": ["read"],
	"QD Training Enrollment": ["read"],
	"QD Training Attendance": ["read"],
	"QD Training Assessment": ["read"],
	"QD Training Certification": ["read"],
	"QD License Type": ["read"],
	"QD Employee License": ["read"],
	"QD Grievance": ["read", "write", "create", "submit"],
	"QD Complaint": ["read", "write", "create", "submit"],
	"Appointment Letter": ["read"],
	"Asset": ["read"],
	"QD Employee Asset Assignment": ["read"],
	"QD Asset Loss Damage Case": ["read", "write", "create"],
	"QD Asset Recovery": ["read"],
	"QD Employee Request Type": ["read"],
	"QD Employee Request": ["read", "write", "create"],
	"Employee Separation": ["read"],
	"QD Exit Clearance": ["read"],
	"Employee Employment History": ["read"],
	"Employee Promotion": ["read"],
	"Salary Structure Assignment": ["read"],
	"Leave Encashment": ["read", "write", "create"],
	"Overtime Request": ["read", "write", "create"],
	"QD Employee Document": ["read", "write", "create"],
	"QD Policy Acknowledgement": ["read", "write", "submit"],
	"QD Policy": ["read"],
}

SENSITIVE_EMPLOYEE_FIELDS = ("ctc", "salary_mode")

SHORTCUTS = (
	("My Profile", "Employee", "Blue"),
	("My Documents", "QD Employee Document", "Orange"),
	("My Leave", "Leave Application", "Blue"),
	("My Attendance", "Attendance", "Blue"),
	("My Payslips", "Salary Slip", "Orange"),
	("My Assets", "QD Employee Asset Assignment", "Grey"),
	("My Requests", "QD Employee Request", "Blue"),
	("My Performance", "Appraisal", "Blue"),
	("My Training", "Training Event", "Grey"),
	("My Licenses", "QD Employee License", "Orange"),
	("My Letters", "Appointment Letter", "Grey"),
	("My Cases", "Employee Grievance", "Orange"),
)

REQUEST_LINKS = (
	"Attendance Request",
	"Shift Request",
	"Expense Claim",
	"Employee Advance",
	"Travel Request",
	"Leave Encashment",
	"Overtime Request",
	"QD Training Request",
	"QD Employee Request",
)

MORE_LINKS = (
	"Compensatory Leave Request",
	"Employee Tax Exemption Declaration",
	"Training Feedback",
	"Employee Referral",
	"Timesheet",
	"Employee Checkin",
	"Goal",
	"Employee Performance Feedback",
	"Energy Point Log",
	"QD Training Enrollment",
	"QD Training Certification",
	"QD Employee License",
	"QD Grievance",
	"QD Complaint",
	"QD Asset Loss Damage Case",
	"QD Asset Recovery",
	"Employee Separation",
	"QD Exit Clearance",
)

DOCUMENT_LINKS = (
	"QD Employee Document",
	"QD Policy Acknowledgement",
)


def run():
	extend_ess_user_type()
	lock_sensitive_employee_fields()
	ensure_workspace()
	frappe.clear_cache()
	return {
		"workspace": WORKSPACE_NAME,
		"ess_user_type": ESS_USER_TYPE if frappe.db.exists("User Type", ESS_USER_TYPE) else None,
		"ess_extra": [dt for dt in ESS_EXTRA_DOCTYPES if frappe.db.exists("DocType", dt)],
		"sensitive_fields": list(SENSITIVE_EMPLOYEE_FIELDS),
	}


def extend_ess_user_type():
	if not frappe.db.exists("User Type", ESS_USER_TYPE):
		return
	from hrms.setup import append_docperms_to_user_type

	doc = frappe.get_doc("User Type", ESS_USER_TYPE)
	doc.set(
		"user_doctypes",
		[row for row in doc.user_doctypes if row.document_type != "QD Recognition Award"],
	)
	docperms = {dt: perms for dt, perms in ESS_EXTRA_DOCTYPES.items() if frappe.db.exists("DocType", dt)}
	append_docperms_to_user_type(docperms, doc)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def lock_sensitive_employee_fields():
	for fieldname in SENSITIVE_EMPLOYEE_FIELDS:
		if not frappe.get_meta("Employee").has_field(fieldname):
			continue
		frappe.db.delete(
			"Property Setter",
			{
				"doc_type": "Employee",
				"field_name": fieldname,
				"property": "permlevel",
			},
		)
		make_property_setter(
			"Employee",
			fieldname,
			"permlevel",
			str(SENSITIVE_PERMLEVEL),
			"Int",
			validate_fields_for_doctype=False,
			is_system_generated=False,
		)
	for role in SENSITIVE_ROLES:
		if not frappe.db.exists("Role", role):
			continue
		if not frappe.db.exists(
			"Custom DocPerm",
			{
				"parent": "Employee",
				"role": role,
				"permlevel": SENSITIVE_PERMLEVEL,
				"if_owner": 0,
			},
		):
			add_permission("Employee", role, SENSITIVE_PERMLEVEL)
		update_permission_property("Employee", role, SENSITIVE_PERMLEVEL, "read", 1)
		update_permission_property("Employee", role, SENSITIVE_PERMLEVEL, "write", 1)


def ensure_workspace():
	shortcuts = [(label, dt, color) for label, dt, color in SHORTCUTS if frappe.db.exists("DocType", dt)]
	request_links = [dt for dt in REQUEST_LINKS if frappe.db.exists("DocType", dt)]
	more_links = [dt for dt in MORE_LINKS if frappe.db.exists("DocType", dt)]
	document_links = [dt for dt in DOCUMENT_LINKS if frappe.db.exists("DocType", dt)]

	if frappe.db.exists("Workspace", WORKSPACE_NAME):
		doc = frappe.get_doc("Workspace", WORKSPACE_NAME)
		doc.shortcuts = []
		doc.links = []
		doc.roles = []
	else:
		doc = frappe.new_doc("Workspace")
		doc.label = WORKSPACE_NAME

	doc.title = WORKSPACE_NAME
	doc.module = "QD HRMS"
	doc.icon = "assign"
	doc.public = 1
	doc.is_hidden = 0
	doc.hide_custom = 0
	doc.parent_page = ""
	if doc.meta.has_field("sequence_id") and not doc.sequence_id:
		doc.sequence_id = 2

	for role in ("Employee", "Employee Self Service"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	for label, dt, color in shortcuts:
		doc.append(
			"shortcuts",
			{
				"type": "DocType",
				"link_to": dt,
				"doc_view": "List",
				"label": label,
				"color": color,
			},
		)

	_append_card(doc, "My Requests", request_links)
	_append_card(doc, "More Self Service", more_links)
	_append_card(doc, "My Documents", document_links)

	content = [
		_block("header", {"text": '<span class="h4"><b>My HR</b></span>', "col": 12}),
	]
	for label, _dt, _color in shortcuts:
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))
	content.append(_block("spacer", {"col": 12}))
	content.append(
		_block("header", {"text": '<span class="h4"><b>Requests &amp; documents</b></span>', "col": 12})
	)
	if request_links:
		content.append(_block("card", {"card_name": "My Requests", "col": 4}))
	if more_links:
		content.append(_block("card", {"card_name": "More Self Service", "col": 4}))
	if document_links:
		content.append(_block("card", {"card_name": "My Documents", "col": 4}))
	doc.content = json.dumps(content)

	doc.flags.ignore_links = True
	doc.flags.ignore_permissions = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def _append_card(doc, card_name, doctypes):
	if not doctypes:
		return
	doc.append(
		"links",
		{
			"type": "Card Break",
			"label": card_name,
			"hidden": 0,
			"link_count": len(doctypes),
		},
	)
	for dt in doctypes:
		doc.append(
			"links",
			{
				"type": "Link",
				"link_type": "DocType",
				"link_to": dt,
				"label": dt,
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
			},
		)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}
