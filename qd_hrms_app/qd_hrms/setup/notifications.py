"""HR rules on ERPNext's standard Notification and delivery-log engine."""

from __future__ import annotations

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

WORKSPACE = "HR Notifications"
HISTORY_REPORT = "QD HR Notification Delivery History"


def run():
	ensure_recipient_fields()
	ensure_rules()
	ensure_permissions()
	ensure_workspace()
	frappe.clear_cache()
	return verify()


def ensure_recipient_fields():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "custom_qd_reports_to_user",
					"fieldtype": "Link",
					"label": "Manager User",
					"options": "User",
					"fetch_from": "reports_to.user_id",
					"read_only": 1,
					"hidden": 1,
					"insert_after": "reports_to",
				},
				{
					"fieldname": "custom_qd_reports_to_mobile",
					"fieldtype": "Data",
					"label": "Manager Mobile",
					"fetch_from": "reports_to.cell_number",
					"read_only": 1,
					"hidden": 1,
					"insert_after": "custom_qd_reports_to_user",
				},
			],
			"QD Employee Document": [
				{
					"fieldname": "custom_qd_employee_user",
					"fieldtype": "Link",
					"label": "Employee User",
					"options": "User",
					"fetch_from": "employee.user_id",
					"read_only": 1,
					"hidden": 1,
					"insert_after": "employee_name",
				},
				{
					"fieldname": "custom_qd_employee_mobile",
					"fieldtype": "Data",
					"label": "Employee Mobile",
					"fetch_from": "employee.cell_number",
					"read_only": 1,
					"hidden": 1,
					"insert_after": "custom_qd_employee_user",
				},
			],
			"Leave Application": [
				{
					"fieldname": "custom_qd_leave_approver_mobile",
					"fieldtype": "Data",
					"label": "Leave Approver Mobile",
					"fetch_from": "leave_approver.mobile_no",
					"read_only": 1,
					"hidden": 1,
					"insert_after": "leave_approver",
				}
			],
		},
		ignore_validate=True,
		update=True,
	)


def ensure_rules():
	rules = [
		_date_rule(
			"QD Probation Ending - 30 Days",
			"Employee",
			"custom_qd_probation_end",
			30,
			"Probation ending for {{ doc.employee_name }}",
			"{{ doc.employee_name }}'s probation ends on {{ doc.custom_qd_probation_end }}.",
			fields=("user_id", "custom_qd_reports_to_user"),
			roles=("HR User", "HR Manager"),
		),
		_date_rule(
			"QD Probation Reminder - 7 Days",
			"Employee",
			"custom_qd_probation_end",
			7,
			"Reminder: probation ends in 7 days - {{ doc.employee_name }}",
			"Please complete the probation review before {{ doc.custom_qd_probation_end }}.",
			fields=("user_id", "custom_qd_reports_to_user"),
			roles=("HR User", "HR Manager"),
		),
		_date_rule(
			"QD Probation Escalation - 1 Day",
			"Employee",
			"custom_qd_probation_end",
			1,
			"Escalation: probation decision due - {{ doc.employee_name }}",
			"Probation ends tomorrow. HR and the manager must record the decision.",
			fields=("custom_qd_reports_to_user",),
			roles=("HR Manager",),
		),
		_date_rule(
			"QD Document Expiry - 30 Days",
			"QD Employee Document",
			"expiry_date",
			30,
			"Document expiring: {{ doc.title }}",
			"{{ doc.title }} expires on {{ doc.expiry_date }}. Please provide a renewed document.",
			fields=("custom_qd_employee_user",),
			roles=("HR User", "HR Manager"),
		),
		_date_rule(
			"QD Document Expiry Reminder - 7 Days",
			"QD Employee Document",
			"expiry_date",
			7,
			"Reminder: document expires in 7 days - {{ doc.title }}",
			"Renew {{ doc.title }} before {{ doc.expiry_date }}.",
			fields=("custom_qd_employee_user",),
			roles=("HR User", "HR Manager"),
		),
		_date_rule(
			"QD Document Expiry Escalation - 1 Day",
			"QD Employee Document",
			"expiry_date",
			1,
			"Escalation: document expires tomorrow - {{ doc.title }}",
			"Immediate action is required for {{ doc.employee_name }}'s {{ doc.title }}.",
			fields=("custom_qd_employee_user",),
			roles=("HR Manager",),
		),
		_date_rule(
			"QD License Renewal - 30 Days",
			"QD Employee License",
			"expiry_date",
			30,
			"License renewal due: {{ doc.license_type }} - {{ doc.employee_name }}",
			"{{ doc.employee_name }}'s {{ doc.license_type }} expires on {{ doc.expiry_date }}. A renewal request will open automatically if auto-renew is enabled.",
			fields=("employee_user", "manager_user"),
			roles=("HR User", "HR Manager"),
			condition="doc.status not in ('Renewed', 'Revoked')",
		),
		_date_rule(
			"QD License Renewal Reminder - 7 Days",
			"QD Employee License",
			"expiry_date",
			7,
			"Reminder: {{ doc.license_type }} expires in 7 days - {{ doc.employee_name }}",
			"Renew {{ doc.license_type }} for {{ doc.employee_name }} before {{ doc.expiry_date }}.",
			fields=("employee_user", "manager_user"),
			roles=("HR User", "HR Manager"),
			condition="doc.status not in ('Renewed', 'Revoked')",
		),
		_after_rule(
			"QD License Expired Escalation - 1 Day",
			"QD Employee License",
			"expiry_date",
			1,
			"Escalation: {{ doc.license_type }} has expired - {{ doc.employee_name }}",
			"{{ doc.employee_name }}'s {{ doc.license_type }} expired on {{ doc.expiry_date }}. Required-for-work licenses must be renewed immediately.",
			fields=("employee_user", "manager_user"),
			roles=("HR Manager",),
			condition="doc.status not in ('Renewed', 'Revoked')",
		),
		_event_rule(
			"QD Leave Pending - Manager",
			"Leave Application",
			"New",
			"Leave approval required: {{ doc.employee_name }}",
			"Leave request {{ doc.name }} is waiting for manager approval.",
			fields=("leave_approver",),
			condition="doc.status == 'Open' and doc.docstatus == 0",
		),
		_after_rule(
			"QD Leave Pending Reminder - 1 Day",
			"Leave Application",
			"posting_date",
			1,
			"Reminder: leave request awaiting approval - {{ doc.name }}",
			"Leave request {{ doc.name }} remains pending.",
			fields=("leave_approver",),
			condition="doc.status == 'Open' and doc.docstatus == 0",
		),
		_after_rule(
			"QD Leave Pending Escalation - 3 Days",
			"Leave Application",
			"posting_date",
			3,
			"Escalation: leave approval overdue - {{ doc.name }}",
			"Leave request {{ doc.name }} has remained pending for three days.",
			fields=("leave_approver",),
			roles=("HR Manager",),
			condition="doc.status == 'Open' and doc.docstatus == 0",
		),
		_event_rule(
			"QD Payroll Awaiting Approval",
			"Payroll Entry",
			"New",
			"Payroll entry awaiting approval: {{ doc.name }}",
			"Payroll entry {{ doc.name }} requires HR and Finance review.",
			roles=("Payroll Manager", "Accounts Manager", "HR Manager"),
			condition="doc.docstatus == 0 and doc.status == 'Draft'",
		),
		_after_rule(
			"QD Payroll Approval Reminder - 1 Day",
			"Payroll Entry",
			"posting_date",
			1,
			"Reminder: payroll approval pending - {{ doc.name }}",
			"Payroll entry {{ doc.name }} is still awaiting approval.",
			roles=("Payroll Manager", "Accounts Manager", "HR Manager"),
			condition="doc.docstatus == 0 and doc.status == 'Draft'",
		),
		_after_rule(
			"QD Payroll Approval Escalation - 3 Days",
			"Payroll Entry",
			"posting_date",
			3,
			"Escalation: payroll approval overdue - {{ doc.name }}",
			"Payroll entry {{ doc.name }} has awaited approval for three days.",
			roles=("Accounts Manager", "HR Manager"),
			condition="doc.docstatus == 0 and doc.status == 'Draft'",
		),
	]
	for rule in rules:
		_upsert_notification(rule)
	for rule in _sms_rules():
		_upsert_notification(rule)


def _date_rule(name, doctype, date_field, days, subject, message, fields=(), roles=(), condition=""):
	return {
		"name": name,
		"document_type": doctype,
		"event": "Days Before",
		"date_changed": date_field,
		"days_in_advance": days,
		"subject": subject,
		"message": message,
		"condition": condition or ("doc.status == 'Active'" if doctype == "Employee" else ""),
		"fields": fields,
		"roles": roles,
	}


def _after_rule(
	name,
	doctype,
	date_field,
	days,
	subject,
	message,
	fields=(),
	roles=(),
	condition="",
):
	return {
		"name": name,
		"document_type": doctype,
		"event": "Days After",
		"date_changed": date_field,
		"days_in_advance": days,
		"subject": subject,
		"message": message,
		"condition": condition,
		"fields": fields,
		"roles": roles,
	}


def _event_rule(
	name,
	doctype,
	event,
	subject,
	message,
	fields=(),
	roles=(),
	condition="",
):
	return {
		"name": name,
		"document_type": doctype,
		"event": event,
		"subject": subject,
		"message": message,
		"condition": condition,
		"fields": fields,
		"roles": roles,
	}


def _sms_rules():
	sms_enabled = bool(
		frappe.db.get_single_value("SMS Settings", "sms_gateway_url")
		if frappe.db.exists("DocType", "SMS Settings")
		else False
	)
	return (
		{
			**_date_rule(
				"QD SMS Probation Reminder - 7 Days",
				"Employee",
				"custom_qd_probation_end",
				7,
				"Probation reminder",
				"Probation for {{ doc.employee_name }} ends on {{ doc.custom_qd_probation_end }}.",
				fields=("cell_number", "custom_qd_reports_to_mobile"),
				roles=("HR Manager",),
			),
			"channel": "SMS",
			"enabled": sms_enabled,
		},
		{
			**_date_rule(
				"QD SMS Document Expiry - 7 Days",
				"QD Employee Document",
				"expiry_date",
				7,
				"Document expiry reminder",
				"{{ doc.title }} expires on {{ doc.expiry_date }}.",
				fields=("custom_qd_employee_mobile",),
				roles=("HR Manager",),
			),
			"channel": "SMS",
			"enabled": sms_enabled,
		},
		{
			**_after_rule(
				"QD SMS Leave Pending - 1 Day",
				"Leave Application",
				"posting_date",
				1,
				"Leave approval reminder",
				"Leave request {{ doc.name }} is awaiting approval.",
				fields=("custom_qd_leave_approver_mobile",),
				condition="doc.status == 'Open' and doc.docstatus == 0",
			),
			"channel": "SMS",
			"enabled": sms_enabled,
		},
		{
			**_after_rule(
				"QD SMS Payroll Approval - 1 Day",
				"Payroll Entry",
				"posting_date",
				1,
				"Payroll approval reminder",
				"Payroll entry {{ doc.name }} is awaiting approval.",
				roles=("Payroll Manager", "Accounts Manager", "HR Manager"),
				condition="doc.docstatus == 0 and doc.status == 'Draft'",
			),
			"channel": "SMS",
			"enabled": sms_enabled,
		},
	)


def _upsert_notification(rule):
	name = rule["name"]
	doc = (
		frappe.get_doc("Notification", name)
		if frappe.db.exists("Notification", name)
		else frappe.new_doc("Notification")
	)
	if doc.is_new():
		doc.name = name
	doc.enabled = rule.get("enabled", 1)
	doc.is_standard = 0
	doc.module = "QD HRMS"
	doc.channel = rule.get("channel", "Email")
	doc.document_type = rule["document_type"]
	doc.event = rule["event"]
	doc.date_changed = rule.get("date_changed")
	doc.days_in_advance = rule.get("days_in_advance", 0)
	doc.subject = rule["subject"]
	doc.condition = rule.get("condition", "")
	doc.message_type = "Plain Text"
	doc.message = rule["message"]
	doc.send_system_notification = 1 if doc.channel == "Email" else 0
	doc.notification_title = rule["subject"]
	doc.notification_message = rule["message"]
	doc.set("recipients", [])
	for field in rule.get("fields", ()):
		doc.append("recipients", {"receiver_by_document_field": field})
	for role in rule.get("roles", ()):
		if frappe.db.exists("Role", role):
			doc.append("recipients", {"receiver_by_role": role})
	doc.save(ignore_permissions=True)


def ensure_permissions():
	for doctype in ("Notification", "Notification Log"):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.exists("Role", "HR Manager"):
			continue
		if not frappe.db.exists(
			"Custom DocPerm",
			{"parent": doctype, "role": "HR Manager", "permlevel": 0},
		):
			add_permission(doctype, "HR Manager", 0)
		update_permission_property(doctype, "HR Manager", 0, "read", 1)
		update_permission_property(doctype, "HR Manager", 0, "report", 1)


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
	doc.icon = "notification"
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
			{"text": '<span class="h4"><b>HR Notifications</b></span>', "col": 12},
		)
	]
	for label, target, shortcut_type, color in (
		("HR Notification Rules", "Notification", "DocType", "Blue"),
		("Delivery History", HISTORY_REPORT, "Report", "Green"),
		("In-app Notification Log", "Notification Log", "DocType", "Grey"),
		("Email Queue", "Email Queue", "DocType", "Orange"),
		("SMS Log", "SMS Log", "DocType", "Orange"),
	):
		if shortcut_type == "Report" and not frappe.db.exists("Report", target):
			continue
		if shortcut_type == "DocType" and not frappe.db.exists("DocType", target):
			continue
		doc.append(
			"shortcuts",
			{
				"type": shortcut_type,
				"link_to": target,
				"doc_view": "List" if shortcut_type == "DocType" else None,
				"label": label,
				"color": color,
			},
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


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = (
		"QD Probation Ending - 30 Days",
		"QD Document Expiry - 30 Days",
		"QD License Renewal - 30 Days",
		"QD Leave Pending - Manager",
		"QD Payroll Awaiting Approval",
	)
	missing = [name for name in required if not frappe.db.exists("Notification", name)]
	if missing:
		raise frappe.ValidationError(f"Missing HR Notification rules: {', '.join(missing)}")
	if not frappe.db.exists("Report", HISTORY_REPORT):
		raise frappe.ValidationError("HR notification delivery history report missing")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("HR Notifications workspace missing")
	return {
		"engine": "ERPNext Notification",
		"email_and_in_app_rules": 15,
		"sms_templates": 4,
		"history": ["Notification Log", "Email Queue", "SMS Log", HISTORY_REPORT],
		"workspace": WORKSPACE,
		"verified": True,
	}
