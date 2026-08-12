#!/usr/bin/env python3
"""Generate / update 2.15 Documents DocTypes for qd_hrms."""
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
	{"role": "QD Employee", "create": 0, "read": 1, "write": 0, "delete": 0, "print": 1, "email": 0, "export": 0, "report": 0, "share": 0},
]

DOC_TYPE_OPTIONS = (
	"Contract\nNational ID\nPassport\nDriving License\nWork Permit\n"
	"Certificate\nLetter\nForm\nPolicy\nOther"
)

CATEGORY_OPTIONS = (
	"Employee Document\nContract\nID and Certificate\nLetter and Form\nPolicy"
)


def slug(name: str) -> str:
	return name.lower().replace(" ", "_")


def write_doctype(name: str, payload: dict, js: str | None = None, py_extra: str = "pass"):
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
	if js:
		(folder / f"{slug(name)}.js").write_text(js, encoding="utf-8")
	print("wrote", name)


def update_employee_document():
	path = ROOT / "qd_employee_document" / "qd_employee_document.json"
	data = json.loads(path.read_text(encoding="utf-8"))
	data["field_order"] = [
		"naming_series", "employee", "employee_name", "document_category", "document_type",
		"document_name", "document_template", "column_break_1",
		"issue_date", "expiry_date", "status", "days_to_expiry",
		"section_details", "document_number", "issuing_authority", "hr_letter",
		"section_file", "attachment",
		"section_ack", "requires_acknowledgement", "acknowledged", "acknowledged_on",
		"remarks",
	]
	data["fields"] = [
		{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-DOC-.YYYY.-.#####", "reqd": 1},
		{"fieldname": "employee", "fieldtype": "Link", "label": "Employee", "options": "Employee", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
		{"fieldname": "employee_name", "fieldtype": "Data", "label": "Employee Name", "fetch_from": "employee.employee_name", "read_only": 1, "in_list_view": 1},
		{"fieldname": "document_category", "fieldtype": "Select", "label": "Category", "options": CATEGORY_OPTIONS, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
		{"fieldname": "document_type", "fieldtype": "Select", "label": "Document Type", "options": DOC_TYPE_OPTIONS, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
		{"fieldname": "document_name", "fieldtype": "Data", "label": "Document Name", "reqd": 1, "in_list_view": 1},
		{"fieldname": "document_template", "fieldtype": "Link", "label": "Document Template", "options": "QD Document Template"},
		{"fieldname": "column_break_1", "fieldtype": "Column Break"},
		{"fieldname": "issue_date", "fieldtype": "Date", "label": "Issue Date"},
		{"fieldname": "expiry_date", "fieldtype": "Date", "label": "Expiry Date", "in_list_view": 1},
		{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Valid\nPending Renewal\nExpired", "read_only": 1, "in_list_view": 1, "in_standard_filter": 1},
		{"fieldname": "days_to_expiry", "fieldtype": "Int", "label": "Days to Expiry", "read_only": 1},
		{"fieldname": "section_details", "fieldtype": "Section Break", "label": "Details"},
		{"fieldname": "document_number", "fieldtype": "Data", "label": "Document / ID Number"},
		{"fieldname": "issuing_authority", "fieldtype": "Data", "label": "Issuing Authority"},
		{"fieldname": "hr_letter", "fieldtype": "Link", "label": "HR Letter", "options": "QD HR Letter"},
		{"fieldname": "section_file", "fieldtype": "Section Break", "label": "File"},
		{"fieldname": "attachment", "fieldtype": "Attach", "label": "Attachment", "reqd": 1},
		{"fieldname": "section_ack", "fieldtype": "Section Break", "label": "Acknowledgement"},
		{"default": "0", "fieldname": "requires_acknowledgement", "fieldtype": "Check", "label": "Requires Acknowledgement"},
		{"default": "0", "fieldname": "acknowledged", "fieldtype": "Check", "label": "Acknowledged", "permlevel": 1},
		{"fieldname": "acknowledged_on", "fieldtype": "Datetime", "label": "Acknowledged On", "read_only": 1, "permlevel": 1},
		{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
	]
	data["permissions"] = PERMS_FULL + [
		{"role": "QD Employee", "permlevel": 1, "read": 1, "write": 1, "create": 0, "delete": 0, "print": 1},
	]
	data["search_fields"] = "employee,document_category,document_type,document_name,document_number"
	path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

	py_path = ROOT / "qd_employee_document" / "qd_employee_document.py"
	py_path.write_text(
		'''# Copyright (c) 2026, Quick Delivery Service and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, now_datetime


class QDEmployeeDocument(Document):
	def validate(self):
		self.apply_template_defaults()
		self.set_status()
		if self.acknowledged and not self.acknowledged_on:
			self.acknowledged_on = now_datetime()
		if not self.acknowledged:
			self.acknowledged_on = None

	def apply_template_defaults(self):
		if not self.document_template:
			return
		template = frappe.get_cached_doc("QD Document Template", self.document_template)
		if not self.document_name:
			self.document_name = template.template_name
		if not self.document_type:
			self.document_type = template.document_type
		if not self.document_category:
			self.document_category = template.template_category
		if template.requires_acknowledgement:
			self.requires_acknowledgement = 1
		if template.default_validity_days and self.issue_date and not self.expiry_date:
			self.expiry_date = add_days(self.issue_date, template.default_validity_days)

	def set_status(self):
		today = getdate()
		if self.expiry_date:
			self.days_to_expiry = date_diff(self.expiry_date, today)
			if getdate(self.expiry_date) < today:
				self.status = "Expired"
			elif self.days_to_expiry <= 30:
				self.status = "Pending Renewal"
			else:
				self.status = "Valid"
		else:
			self.days_to_expiry = None
			self.status = "Valid"


@frappe.whitelist()
def acknowledge_document(name: str):
	doc = frappe.get_doc("QD Employee Document", name)
	if not doc.requires_acknowledgement:
		frappe.throw("This document does not require acknowledgement.")
	if not _can_acknowledge(doc):
		frappe.throw("Not permitted to acknowledge this document.", frappe.PermissionError)
	doc.acknowledged = 1
	doc.save(ignore_permissions=True)
	return doc.name


def _can_acknowledge(doc) -> bool:
	if frappe.has_permission("QD Employee Document", "write", doc=doc):
		return True
	employee_user = frappe.db.get_value("Employee", doc.employee, "user_id")
	return employee_user and employee_user == frappe.session.user
''',
		encoding="utf-8",
	)
	print("updated QD Employee Document")


write_doctype(
	"QD Document Template",
	{
		"allow_rename": 1,
		"autoname": "field:template_name",
		"naming_rule": "By fieldname",
		"permissions": PERMS_FULL,
		"search_fields": "template_name,template_category,document_type",
		"field_order": [
			"template_name", "template_category", "document_type", "column_break_1",
			"is_active", "requires_acknowledgement", "default_validity_days",
			"section_file", "template_file", "description",
		],
		"fields": [
			{"fieldname": "template_name", "fieldtype": "Data", "label": "Template Name", "reqd": 1, "unique": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "template_category", "fieldtype": "Select", "label": "Category", "options": CATEGORY_OPTIONS, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "document_type", "fieldtype": "Select", "label": "Document Type", "options": DOC_TYPE_OPTIONS, "reqd": 1, "in_list_view": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "in_list_view": 1},
			{"default": "0", "fieldname": "requires_acknowledgement", "fieldtype": "Check", "label": "Requires Acknowledgement"},
			{"fieldname": "default_validity_days", "fieldtype": "Int", "label": "Default Validity (Days)"},
			{"fieldname": "section_file", "fieldtype": "Section Break", "label": "Template File"},
			{"fieldname": "template_file", "fieldtype": "Attach", "label": "Template File"},
			{"fieldname": "description", "fieldtype": "Text", "label": "Description"},
		],
	},
	js="""frappe.ui.form.on('QD Document Template', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Create Employee Document'), () => {
				frappe.new_doc('QD Employee Document', {
					document_template: frm.doc.name,
					document_name: frm.doc.template_name,
					document_type: frm.doc.document_type,
					document_category: frm.doc.template_category,
					requires_acknowledgement: frm.doc.requires_acknowledgement,
				});
			}, __('Actions'));
		}
	}
});
""",
)

update_employee_document()
print("done")
