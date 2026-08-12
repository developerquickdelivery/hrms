#!/usr/bin/env python3
"""Generate 2.17 Notifications DocTypes for qd_hrms."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/qd/frappe-bench/apps/qd_hrms/qd_hrms/quick_delivery_hrms/doctype")
MODULE = "Quick Delivery HRMS"

PERMS_FULL = [
	{"role": "System Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "HR Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD HR Officer", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD Department Manager", "create": 0, "read": 1, "write": 0, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 0},
]

CHANNEL_OPTIONS = "Email\nSystem Notification\nSMS"
STATUS_OPTIONS = "Queued\nSent\nFailed\nSkipped"


def slug(name: str) -> str:
	return name.lower().replace(" ", "_")


def write_doctype(name: str, payload: dict, py_extra: str = "pass"):
	folder = ROOT / slug(name)
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").write_text("", encoding="utf-8")
	class_name = name.replace(" ", "")
	(folder / f"{slug(name)}.py").write_text(
		f"""# Copyright (c) 2026, Quick Delivery Service and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class {class_name}(Document):
	{py_extra}
""",
		encoding="utf-8",
	)
	doc = {
		"actions": [],
		"creation": "2026-08-11 00:00:00.000000",
		"doctype": "DocType",
		"engine": "InnoDB",
		"index_web_pages_for_search": 1,
		"links": [],
		"modified": "2026-08-11 00:00:00.000000",
		"modified_by": "Administrator",
		"module": MODULE,
		"name": name,
		"owner": "Administrator",
		"sort_field": "modified",
		"sort_order": "DESC",
		"states": [],
		"track_changes": 1,
		**payload,
	}
	(folder / f"{slug(name)}.json").write_text(
		json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
	)
	print("wrote", name)


write_doctype(
	"QD Notification Template",
	{
		"allow_rename": 1,
		"autoname": "field:template_name",
		"naming_rule": "By fieldname",
		"permissions": PERMS_FULL,
		"search_fields": "template_name,channel,reference_doctype",
		"field_order": [
			"template_name", "channel", "reference_doctype", "column_break_1",
			"is_active", "category",
			"section_message", "subject", "message",
			"description",
		],
		"fields": [
			{"fieldname": "template_name", "fieldtype": "Data", "label": "Template Name", "reqd": 1, "unique": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "channel", "fieldtype": "Select", "label": "Channel", "options": CHANNEL_OPTIONS, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "reference_doctype", "fieldtype": "Link", "label": "Reference DocType", "options": "DocType", "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "in_list_view": 1},
			{"fieldname": "category", "fieldtype": "Select", "label": "Category", "options": "Leave\nRecruitment\nDocument\nSeparation\nSupport\nGeneral", "in_list_view": 1},
			{"fieldname": "section_message", "fieldtype": "Section Break", "label": "Message"},
			{"fieldname": "subject", "fieldtype": "Data", "label": "Subject / Title"},
			{"fieldname": "message", "fieldtype": "Text Editor", "label": "Message", "reqd": 1},
			{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
		],
	},
)

write_doctype(
	"QD Reminder Escalation Rule",
	{
		"allow_rename": 1,
		"autoname": "field:rule_name",
		"naming_rule": "By fieldname",
		"permissions": PERMS_FULL,
		"search_fields": "rule_name,document_type,channel",
		"field_order": [
			"rule_name", "is_active", "document_type", "column_break_1",
			"status_field", "pending_status", "days_open_threshold",
			"section_notify", "channel", "notification_template", "notify_role",
			"section_escalation", "escalate_after_days", "escalate_to_role",
			"remarks",
		],
		"fields": [
			{"fieldname": "rule_name", "fieldtype": "Data", "label": "Rule Name", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "in_list_view": 1},
			{"fieldname": "document_type", "fieldtype": "Link", "label": "Document Type", "options": "DocType", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "status_field", "fieldtype": "Data", "label": "Status Field", "default": "status"},
			{"fieldname": "pending_status", "fieldtype": "Small Text", "label": "Pending Status Values", "description": "Comma-separated values treated as pending"},
			{"default": "3", "fieldname": "days_open_threshold", "fieldtype": "Int", "label": "Days Open Before Reminder", "reqd": 1},
			{"fieldname": "section_notify", "fieldtype": "Section Break", "label": "Notification"},
			{"fieldname": "channel", "fieldtype": "Select", "label": "Channel", "options": CHANNEL_OPTIONS, "default": "System Notification", "reqd": 1},
			{"fieldname": "notification_template", "fieldtype": "Link", "label": "Notification Template", "options": "QD Notification Template"},
			{"fieldname": "notify_role", "fieldtype": "Link", "label": "Notify Role", "options": "Role"},
			{"fieldname": "section_escalation", "fieldtype": "Section Break", "label": "Escalation"},
			{"fieldname": "escalate_after_days", "fieldtype": "Int", "label": "Escalate After (Days)"},
			{"fieldname": "escalate_to_role", "fieldtype": "Link", "label": "Escalate To Role", "options": "Role"},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
)

write_doctype(
	"QD Notification Delivery Log",
	{
		"allow_rename": 0,
		"autoname": "naming_series:",
		"naming_rule": 'By "Naming Series" field',
		"permissions": PERMS_FULL + [
			{"role": "QD Employee", "create": 0, "read": 1, "write": 0, "delete": 0, "print": 0, "email": 0, "export": 0, "report": 0, "share": 0},
		],
		"search_fields": "recipient,channel,status,reference_doctype",
		"field_order": [
			"naming_series", "channel", "status", "sent_on",
			"column_break_1", "recipient", "recipient_user",
			"section_reference", "reference_doctype", "reference_name",
			"notification_template", "reminder_rule",
			"section_message", "subject", "message",
			"error_message",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-NOT-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "channel", "fieldtype": "Select", "label": "Channel", "options": CHANNEL_OPTIONS, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": STATUS_OPTIONS, "default": "Queued", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "sent_on", "fieldtype": "Datetime", "label": "Sent On", "in_list_view": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "recipient", "fieldtype": "Data", "label": "Recipient", "in_list_view": 1},
			{"fieldname": "recipient_user", "fieldtype": "Link", "label": "Recipient User", "options": "User"},
			{"fieldname": "section_reference", "fieldtype": "Section Break", "label": "Reference"},
			{"fieldname": "reference_doctype", "fieldtype": "Link", "label": "Reference DocType", "options": "DocType", "in_standard_filter": 1},
			{"fieldname": "reference_name", "fieldtype": "Dynamic Link", "label": "Reference Name", "options": "reference_doctype", "in_list_view": 1},
			{"fieldname": "notification_template", "fieldtype": "Link", "label": "Notification Template", "options": "QD Notification Template"},
			{"fieldname": "reminder_rule", "fieldtype": "Link", "label": "Reminder Rule", "options": "QD Reminder Escalation Rule"},
			{"fieldname": "section_message", "fieldtype": "Section Break", "label": "Message"},
			{"fieldname": "subject", "fieldtype": "Data", "label": "Subject"},
			{"fieldname": "message", "fieldtype": "Text Editor", "label": "Message"},
			{"fieldname": "error_message", "fieldtype": "Small Text", "label": "Error Message"},
		],
	},
)

print("done")
