#!/usr/bin/env python3
"""Generate 2.19 Administration DocTypes for qd_hrms."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/qd/frappe-bench/apps/qd_hrms/qd_hrms/quick_delivery_hrms/doctype")
MODULE = "Quick Delivery HRMS"

PERMS_ADMIN = [
	{"role": "System Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "HR Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
]

PERMS_READ = PERMS_ADMIN + [
	{"role": "QD HR Officer", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
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
	"QD Delegation Rule",
	{
		"allow_rename": 1,
		"autoname": "field:rule_name",
		"naming_rule": "By fieldname",
		"permissions": PERMS_READ,
		"search_fields": "rule_name,user,delegate_to_user",
		"field_order": [
			"rule_name", "is_active", "user", "delegate_to_user",
			"column_break_1", "from_date", "to_date",
			"section_scope", "applies_to_doctype", "reason", "remarks",
		],
		"fields": [
			{"fieldname": "rule_name", "fieldtype": "Data", "label": "Rule Name", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "in_list_view": 1},
			{"fieldname": "user", "fieldtype": "Link", "label": "User", "options": "User", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "delegate_to_user", "fieldtype": "Link", "label": "Delegate To", "options": "User", "reqd": 1, "in_list_view": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "from_date", "fieldtype": "Date", "label": "From Date", "reqd": 1, "default": "Today"},
			{"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "reqd": 1},
			{"fieldname": "section_scope", "fieldtype": "Section Break", "label": "Scope"},
			{"fieldname": "applies_to_doctype", "fieldtype": "Link", "label": "Applies To DocType", "options": "DocType", "description": "Leave blank for all approval types"},
			{"fieldname": "reason", "fieldtype": "Small Text", "label": "Reason"},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
	py_extra="""def validate(self):
		from frappe.utils import getdate
		if self.from_date and self.to_date and getdate(self.to_date) < getdate(self.from_date):
			import frappe
			frappe.throw('To Date cannot be before From Date')
		if self.user == self.delegate_to_user:
			import frappe
			frappe.throw('User and Delegate To must be different')
""",
)

write_doctype(
	"QD Retention Policy",
	{
		"allow_rename": 1,
		"autoname": "field:policy_name",
		"naming_rule": "By fieldname",
		"permissions": PERMS_ADMIN,
		"search_fields": "policy_name,document_type",
		"field_order": [
			"policy_name", "document_type", "is_active", "column_break_1",
			"retention_days", "action", "notes",
		],
		"fields": [
			{"fieldname": "policy_name", "fieldtype": "Data", "label": "Policy Name", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "document_type", "fieldtype": "Link", "label": "Document Type", "options": "DocType", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "in_list_view": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "retention_days", "fieldtype": "Int", "label": "Retention (Days)", "reqd": 1, "in_list_view": 1},
			{"fieldname": "action", "fieldtype": "Select", "label": "Action After Retention", "options": "Review\nArchive\nDelete", "default": "Review", "reqd": 1},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
		],
	},
)

print("done")
