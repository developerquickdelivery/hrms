#!/usr/bin/env python3
"""Generate 2.20 Help and Support DocTypes for qd_hrms."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/qd/frappe-bench/apps/qd_hrms/qd_hrms/quick_delivery_hrms/doctype")
MODULE = "Quick Delivery HRMS"

HELP_CATEGORY = "Getting Started\nLeave\nAttendance\nPayroll\nDocuments\nBenefits\nSystem\nOther"

PERMS_ADMIN = [
	{"role": "System Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "HR Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
]

PERMS_CONTENT = PERMS_ADMIN + [
	{"role": "QD HR Officer", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD Department Manager", "create": 0, "read": 1, "write": 0, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 0},
	{"role": "QD Employee", "create": 0, "read": 1, "write": 0, "delete": 0, "print": 1, "email": 0, "export": 0, "report": 0, "share": 0},
]

PERMS_FEEDBACK = PERMS_ADMIN + [
	{"role": "QD HR Officer", "create": 0, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD Department Manager", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 0},
	{"role": "QD Employee", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 0, "export": 0, "report": 0, "share": 0},
]


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
	"QD Help Article",
	{
		"allow_rename": 1,
		"autoname": "field:article_title",
		"naming_rule": "By fieldname",
		"permissions": PERMS_CONTENT,
		"search_fields": "article_title,category,audience",
		"field_order": [
			"article_title", "category", "audience", "column_break_1",
			"is_published", "sort_order",
			"section_content", "summary", "content",
		],
		"fields": [
			{"fieldname": "article_title", "fieldtype": "Data", "label": "Article Title", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "category", "fieldtype": "Select", "label": "Category", "options": HELP_CATEGORY, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "audience", "fieldtype": "Select", "label": "Audience", "options": "All\nEmployee\nManager\nHR", "default": "All", "reqd": 1, "in_list_view": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"default": "0", "fieldname": "is_published", "fieldtype": "Check", "label": "Published", "in_list_view": 1, "in_standard_filter": 1},
			{"default": "100", "fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order"},
			{"fieldname": "section_content", "fieldtype": "Section Break", "label": "Content"},
			{"fieldname": "summary", "fieldtype": "Small Text", "label": "Summary"},
			{"fieldname": "content", "fieldtype": "Text Editor", "label": "Content", "reqd": 1},
		],
	},
)

write_doctype(
	"QD FAQ Entry",
	{
		"allow_rename": 1,
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"permissions": PERMS_CONTENT,
		"search_fields": "question,category",
		"field_order": [
			"naming_series", "question", "category", "column_break_1",
			"is_published", "sort_order",
			"section_answer", "answer",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "FAQ-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "question", "fieldtype": "Data", "label": "Question", "reqd": 1, "in_list_view": 1},
			{"fieldname": "category", "fieldtype": "Select", "label": "Category", "options": HELP_CATEGORY, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"default": "1", "fieldname": "is_published", "fieldtype": "Check", "label": "Published", "in_list_view": 1, "in_standard_filter": 1},
			{"default": "100", "fieldname": "sort_order", "fieldtype": "Int", "label": "Sort Order"},
			{"fieldname": "section_answer", "fieldtype": "Section Break", "label": "Answer"},
			{"fieldname": "answer", "fieldtype": "Text Editor", "label": "Answer", "reqd": 1},
		],
	},
)

write_doctype(
	"QD System Announcement",
	{
		"allow_rename": 1,
		"autoname": "field:title",
		"naming_rule": "By fieldname",
		"permissions": PERMS_CONTENT,
		"search_fields": "title,target_audience,priority",
		"field_order": [
			"title", "priority", "target_audience", "column_break_1",
			"is_active", "valid_from", "valid_to",
			"section_message", "message",
		],
		"fields": [
			{"fieldname": "title", "fieldtype": "Data", "label": "Title", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "priority", "fieldtype": "Select", "label": "Priority", "options": "Info\nImportant\nUrgent", "default": "Info", "reqd": 1, "in_list_view": 1},
			{"fieldname": "target_audience", "fieldtype": "Select", "label": "Target Audience", "options": "All\nEmployee\nManager\nHR", "default": "All", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active", "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "valid_from", "fieldtype": "Date", "label": "Valid From", "default": "Today", "reqd": 1},
			{"fieldname": "valid_to", "fieldtype": "Date", "label": "Valid To"},
			{"fieldname": "section_message", "fieldtype": "Section Break", "label": "Message"},
			{"fieldname": "message", "fieldtype": "Text Editor", "label": "Message", "reqd": 1},
		],
	},
	py_extra="""def validate(self):
		from frappe.utils import getdate
		import frappe
		if self.valid_from and self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
			frappe.throw('Valid To cannot be before Valid From')
""",
)

write_doctype(
	"QD Employee Feedback",
	{
		"allow_rename": 1,
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"permissions": PERMS_FEEDBACK,
		"search_fields": "employee,category,status",
		"field_order": [
			"naming_series", "employee", "employee_name", "category", "column_break_1",
			"status", "submitted_on", "rating",
			"section_feedback", "feedback", "hr_response", "remarks",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-FB-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "employee", "fieldtype": "Link", "label": "Employee", "options": "Employee", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "employee_name", "fieldtype": "Data", "label": "Employee Name", "fetch_from": "employee.employee_name", "read_only": 1, "in_list_view": 1},
			{"fieldname": "category", "fieldtype": "Select", "label": "Category", "options": "HRMS Usability\nPayroll\nLeave\nAttendance\nTraining\nGeneral", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "New\nUnder Review\nAcknowledged\nClosed", "default": "New", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "submitted_on", "fieldtype": "Date", "label": "Submitted On", "default": "Today", "reqd": 1},
			{"fieldname": "rating", "fieldtype": "Int", "label": "Rating (1-5)", "description": "Optional satisfaction score"},
			{"fieldname": "section_feedback", "fieldtype": "Section Break", "label": "Feedback"},
			{"fieldname": "feedback", "fieldtype": "Text", "label": "Feedback", "reqd": 1},
			{"fieldname": "hr_response", "fieldtype": "Text", "label": "HR Response"},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
)

write_doctype(
	"QD HR Contact Settings",
	{
		"issingle": 1,
		"permissions": PERMS_ADMIN
		+ [
			{"role": "QD HR Officer", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
			{"role": "QD Employee", "create": 0, "read": 1, "write": 0, "delete": 0, "print": 0, "email": 0, "export": 0, "report": 0, "share": 0},
		],
		"field_order": [
			"hr_email", "hr_phone", "column_break_1",
			"office_hours", "desk_location",
			"section_instructions", "support_instructions",
		],
		"fields": [
			{"fieldname": "hr_email", "fieldtype": "Data", "label": "HR Email", "options": "Email"},
			{"fieldname": "hr_phone", "fieldtype": "Data", "label": "HR Phone"},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "office_hours", "fieldtype": "Data", "label": "Office Hours", "default": "Mon–Fri 9:00 AM – 5:00 PM"},
			{"fieldname": "desk_location", "fieldtype": "Data", "label": "HR Desk Location"},
			{"fieldname": "section_instructions", "fieldtype": "Section Break", "label": "Instructions"},
			{
				"fieldname": "support_instructions",
				"fieldtype": "Text Editor",
				"label": "Support Instructions",
				"default": "<p>For urgent payroll or leave issues, submit an <b>HR Support</b> ticket from your Employee Dashboard.</p>",
			},
		],
	},
)

print("done")
