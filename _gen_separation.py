#!/usr/bin/env python3
"""Generate 2.14 Separation & Exit DocTypes for qd_hrms."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/qd/frappe-bench/apps/qd_hrms/qd_hrms/quick_delivery_hrms/doctype")
MODULE = "Quick Delivery HRMS"

PERMS_FULL = [
	{"role": "System Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "HR Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD HR Officer", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD Department Manager", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD Employee", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 0, "export": 0, "report": 0, "share": 0},
]

SEPARATION_TYPE_OPTIONS = (
	"Resignation\nTermination\nRetirement\nRedundancy\nContract Completion\nOther"
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


# Child table
write_doctype(
	"QD Exit Clearance Item",
	{
		"istable": 1,
		"editable_grid": 1,
		"permissions": [],
		"field_order": [
			"department_area", "clearance_item", "status", "cleared_by", "cleared_on", "remarks"
		],
		"fields": [
			{"fieldname": "department_area", "fieldtype": "Select", "label": "Department / Area", "options": "HR\nIT\nFinance\nOperations\nHub / Assets\nManager\nOther", "in_list_view": 1, "reqd": 1},
			{"fieldname": "clearance_item", "fieldtype": "Data", "label": "Clearance Item", "in_list_view": 1, "reqd": 1},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Pending\nCleared\nNot Applicable", "default": "Pending", "in_list_view": 1},
			{"fieldname": "cleared_by", "fieldtype": "Link", "label": "Cleared By", "options": "Employee"},
			{"fieldname": "cleared_on", "fieldtype": "Date", "label": "Cleared On"},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
)

write_doctype(
	"QD Resignation Request",
	{
		"allow_rename": 1,
		"autoname": "naming_series:",
		"naming_rule": 'By "Naming Series" field',
		"permissions": PERMS_FULL,
		"search_fields": "employee,status,separation_type",
		"field_order": [
			"naming_series", "employee", "employee_name", "separation_type",
			"column_break_1", "status", "company", "requested_on",
			"resignation_letter_date", "requested_relieving_date",
			"section_details", "reason", "notice_period_days", "approver",
			"employee_separation", "remarks",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-RES-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "employee", "fieldtype": "Link", "label": "Employee", "options": "Employee", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "employee_name", "fieldtype": "Data", "label": "Employee Name", "fetch_from": "employee.employee_name", "read_only": 1, "in_list_view": 1},
			{"fieldname": "separation_type", "fieldtype": "Select", "label": "Separation Type", "options": SEPARATION_TYPE_OPTIONS, "default": "Resignation", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nPending Approval\nApproved\nRejected\nWithdrawn\nCancelled", "default": "Draft", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "fetch_from": "employee.company", "read_only": 1},
			{"fieldname": "requested_on", "fieldtype": "Date", "label": "Requested On", "default": "Today", "reqd": 1},
			{"fieldname": "resignation_letter_date", "fieldtype": "Date", "label": "Resignation Letter Date", "reqd": 1},
			{"fieldname": "requested_relieving_date", "fieldtype": "Date", "label": "Requested Relieving Date", "reqd": 1, "in_list_view": 1},
			{"fieldname": "section_details", "fieldtype": "Section Break", "label": "Details"},
			{"fieldname": "reason", "fieldtype": "Text", "label": "Reason", "reqd": 1},
			{"fieldname": "notice_period_days", "fieldtype": "Int", "label": "Notice Period (Days)"},
			{"fieldname": "approver", "fieldtype": "Link", "label": "Approver", "options": "Employee"},
			{"fieldname": "employee_separation", "fieldtype": "Link", "label": "Employee Separation", "options": "Employee Separation", "read_only": 1},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
	js="""frappe.ui.form.on('QD Resignation Request', {
	refresh(frm) {
		if (frm.doc.status === 'Draft') {
			frm.add_custom_button(__('Submit for Approval'), () => {
				frm.set_value('status', 'Pending Approval');
				frm.save();
			});
		}
		if (frm.doc.status === 'Pending Approval' && (frappe.user.has_role('QD HR Officer') || frappe.user.has_role('QD Department Manager') || frappe.user.has_role('System Manager') || frappe.user.has_role('HR Manager'))) {
			frm.add_custom_button(__('Approve'), () => {
				frm.set_value('status', 'Approved');
				frm.save();
			}, __('Actions'));
			frm.add_custom_button(__('Reject'), () => {
				frm.set_value('status', 'Rejected');
				frm.save();
			}, __('Actions'));
		}
		if (frm.doc.status === 'Approved' && !frm.doc.employee_separation) {
			frm.add_custom_button(__('Create Separation'), () => {
				frappe.new_doc('Employee Separation', {
					employee: frm.doc.employee,
					boarding_begins_on: frm.doc.requested_relieving_date,
					custom_qd_separation_type: frm.doc.separation_type,
					custom_qd_resignation_request: frm.doc.name,
				});
			}, __('Separation'));
		}
	}
});
""",
)

write_doctype(
	"QD Exit Clearance",
	{
		"allow_rename": 1,
		"autoname": "naming_series:",
		"naming_rule": 'By "Naming Series" field',
		"permissions": PERMS_FULL,
		"search_fields": "employee,status,separation_type",
		"field_order": [
			"naming_series", "employee", "employee_name", "separation_type",
			"column_break_1", "status", "company", "clearance_date",
			"section_links", "employee_separation", "exit_interview", "full_and_final_statement",
			"section_clearance", "clearance_items",
			"section_access", "access_deactivated", "access_deactivated_on", "access_deactivated_by", "access_notes",
			"section_payroll", "final_payroll_validated", "payroll_validation_notes",
			"section_records", "records_preserved", "archive_location", "records_notes",
			"remarks",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-CLR-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "employee", "fieldtype": "Link", "label": "Employee", "options": "Employee", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "employee_name", "fieldtype": "Data", "label": "Employee Name", "fetch_from": "employee.employee_name", "read_only": 1, "in_list_view": 1},
			{"fieldname": "separation_type", "fieldtype": "Select", "label": "Separation Type", "options": SEPARATION_TYPE_OPTIONS, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nIn Progress\nCleared\nClosed", "default": "Open", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "fetch_from": "employee.company", "read_only": 1},
			{"fieldname": "clearance_date", "fieldtype": "Date", "label": "Clearance Date", "default": "Today"},
			{"fieldname": "section_links", "fieldtype": "Section Break", "label": "Linked Records"},
			{"fieldname": "employee_separation", "fieldtype": "Link", "label": "Employee Separation", "options": "Employee Separation"},
			{"fieldname": "exit_interview", "fieldtype": "Link", "label": "Exit Interview", "options": "Exit Interview"},
			{"fieldname": "full_and_final_statement", "fieldtype": "Link", "label": "Full and Final Statement", "options": "Full and Final Statement"},
			{"fieldname": "section_clearance", "fieldtype": "Section Break", "label": "Exit Clearance Checklist"},
			{"fieldname": "clearance_items", "fieldtype": "Table", "label": "Clearance Items", "options": "QD Exit Clearance Item"},
			{"fieldname": "section_access", "fieldtype": "Section Break", "label": "Access Deactivation"},
			{"default": "0", "fieldname": "access_deactivated", "fieldtype": "Check", "label": "System Access Deactivated"},
			{"fieldname": "access_deactivated_on", "fieldtype": "Date", "label": "Deactivated On"},
			{"fieldname": "access_deactivated_by", "fieldtype": "Link", "label": "Deactivated By", "options": "Employee"},
			{"fieldname": "access_notes", "fieldtype": "Small Text", "label": "Access Notes"},
			{"fieldname": "section_payroll", "fieldtype": "Section Break", "label": "Final Payroll Inputs"},
			{"default": "0", "fieldname": "final_payroll_validated", "fieldtype": "Check", "label": "Final Payroll Inputs Validated"},
			{"fieldname": "payroll_validation_notes", "fieldtype": "Small Text", "label": "Payroll Validation Notes"},
			{"fieldname": "section_records", "fieldtype": "Section Break", "label": "Records Preservation"},
			{"default": "0", "fieldname": "records_preserved", "fieldtype": "Check", "label": "Employee Records Preserved"},
			{"fieldname": "archive_location", "fieldtype": "Data", "label": "Archive / File Location"},
			{"fieldname": "records_notes", "fieldtype": "Small Text", "label": "Records Notes"},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
	js="""frappe.ui.form.on('QD Exit Clearance', {
	refresh(frm) {
		if (!['Cleared', 'Closed'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Mark Cleared'), () => {
				frm.set_value('status', 'Cleared');
				frm.save();
			}, __('Actions'));
		}
		if (frm.doc.employee) {
			frm.add_custom_button(__('Open Separation'), () => {
				frappe.set_route('List', 'Employee Separation', { employee: frm.doc.employee });
			}, __('Separation'));
			frm.add_custom_button(__('Open FnF'), () => {
				frappe.set_route('List', 'Full and Final Statement', { employee: frm.doc.employee });
			}, __('Separation'));
		}
	},
	access_deactivated(frm) {
		if (frm.doc.access_deactivated && !frm.doc.access_deactivated_on) {
			frm.set_value('access_deactivated_on', frappe.datetime.get_today());
		}
	}
});
""",
	py_extra="""def validate(self):
		from frappe.utils import today
		if self.access_deactivated and not self.access_deactivated_on:
			self.access_deactivated_on = today()
		if self.status == 'Cleared' and not self.final_payroll_validated:
			import frappe
			frappe.msgprint('Consider validating final payroll inputs before marking clearance complete.', indicator='orange')
""",
)

print("done")
