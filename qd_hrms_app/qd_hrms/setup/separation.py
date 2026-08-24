"""Customize standard HRMS Employee Separation and add structured clearance."""

from __future__ import annotations

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.permissions import add_permission, update_permission_property

WORKSPACE = "Separation Management"


def run():
	ensure_custom_fields()
	ensure_permissions()
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


def ensure_custom_fields():
	create_custom_fields(
		{
			"Employee Separation": [
				{"fieldname":"custom_qd_separation_type","fieldtype":"Select","label":"Separation Type","options":"Resignation\nTermination\nRetirement\nRedundancy\nContract Completion","reqd":1,"in_list_view":1,"in_standard_filter":1,"insert_after":"employee"},
				{"fieldname":"custom_qd_final_working_date","fieldtype":"Date","label":"Final Working Date","reqd":1,"in_list_view":1,"insert_after":"custom_qd_separation_type"},
				{"fieldname":"custom_qd_lifecycle_status","fieldtype":"Select","label":"Separation Stage","options":"Draft\nClearance\nFinal Payroll\nExit Interview\nAccess Deactivation\nRecords Preservation\nSeparation Complete\nCancelled","default":"Draft","read_only":1,"allow_on_submit":1,"in_list_view":1,"in_standard_filter":1,"insert_after":"custom_qd_final_working_date"},
				{"fieldname":"custom_qd_exit_clearance","fieldtype":"Link","label":"Exit Clearance","options":"QD Exit Clearance","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_lifecycle_status"},
				{"fieldname":"custom_qd_finalization_section","fieldtype":"Section Break","label":"Separation Finalization","insert_after":"exit_interview"},
				{"fieldname":"custom_qd_final_payroll_reference_doctype","fieldtype":"Link","label":"Final Payroll Reference Type","options":"DocType","allow_on_submit":1,"insert_after":"custom_qd_finalization_section"},
				{"fieldname":"custom_qd_final_payroll_reference","fieldtype":"Dynamic Link","label":"Final Payroll Reference","options":"custom_qd_final_payroll_reference_doctype","allow_on_submit":1,"insert_after":"custom_qd_final_payroll_reference_doctype"},
				{"fieldname":"custom_qd_final_payroll_completed","fieldtype":"Check","label":"Final Payroll Completed","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_final_payroll_reference"},
				{"fieldname":"custom_qd_final_payroll_completed_on","fieldtype":"Datetime","label":"Final Payroll Completed On","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_final_payroll_completed"},
				{"fieldname":"custom_qd_exit_interview_completed","fieldtype":"Check","label":"Exit Interview Completed","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_final_payroll_completed_on"},
				{"fieldname":"custom_qd_exit_interview_completed_on","fieldtype":"Datetime","label":"Exit Interview Completed On","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_exit_interview_completed"},
				{"fieldname":"custom_qd_access_section","fieldtype":"Section Break","label":"Access Deactivation","insert_after":"custom_qd_exit_interview_completed_on"},
				{"fieldname":"custom_qd_access_deactivated","fieldtype":"Check","label":"Access Deactivated","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_access_section"},
				{"fieldname":"custom_qd_access_deactivated_by","fieldtype":"Link","label":"Deactivated By","options":"User","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_access_deactivated"},
				{"fieldname":"custom_qd_access_deactivated_on","fieldtype":"Datetime","label":"Deactivated On","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_access_deactivated_by"},
				{"fieldname":"custom_qd_records_section","fieldtype":"Section Break","label":"Records Preservation","insert_after":"custom_qd_access_deactivated_on"},
				{"fieldname":"custom_qd_records_location","fieldtype":"Data","label":"Preservation Location / Archive Reference","allow_on_submit":1,"insert_after":"custom_qd_records_section"},
				{"fieldname":"custom_qd_records_retention_until","fieldtype":"Date","label":"Retain Until","allow_on_submit":1,"insert_after":"custom_qd_records_location"},
				{"fieldname":"custom_qd_records_preserved","fieldtype":"Check","label":"Records Preserved","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_records_retention_until"},
				{"fieldname":"custom_qd_records_preserved_by","fieldtype":"Link","label":"Preserved By","options":"User","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_records_preserved"},
				{"fieldname":"custom_qd_records_preserved_on","fieldtype":"Datetime","label":"Preserved On","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_records_preserved_by"},
				{"fieldname":"custom_qd_completed_on","fieldtype":"Datetime","label":"Separation Completed On","read_only":1,"allow_on_submit":1,"insert_after":"custom_qd_records_preserved_on"},
			],
			"Task": [
				{"fieldname":"custom_qd_exit_clearance","fieldtype":"Link","label":"Exit Clearance","options":"QD Exit Clearance","read_only":1,"in_standard_filter":1,"insert_after":"subject"},
				{"fieldname":"custom_qd_clearance_department","fieldtype":"Data","label":"Clearance Function","read_only":1,"insert_after":"custom_qd_exit_clearance"},
			],
		},
		ignore_validate=True,
		update=True,
	)
	make_property_setter(
		"Employee Separation",
		"exit_interview",
		"allow_on_submit",
		"1",
		"Check",
		validate_fields_for_doctype=False,
		is_system_generated=False,
	)


def ensure_permissions():
	for role, rights in (
		("HR Manager", ("read", "write", "create", "submit", "cancel", "amend", "report", "export", "print", "email")),
		("HR User", ("read", "write", "create", "submit", "report", "export", "print", "email")),
		("Employee", ("read", "print")),
	):
		if not frappe.db.exists("Role", role):
			continue
		if not frappe.db.exists(
			"Custom DocPerm",
			{"parent": "Employee Separation", "role": role, "permlevel": 0},
		):
			add_permission("Employee Separation", role, 0)
		for right in rights:
			update_permission_property("Employee Separation", role, 0, right, 1)


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
	doc.icon = "change"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>Separation Management</b></span>', "col": 12},
		)
	]
	for label, target, color in (
		("Employee Separations", "Employee Separation", "Orange"),
		("Separation Templates", "Employee Separation Template", "Grey"),
		("Exit Clearances", "QD Exit Clearance", "Blue"),
		("Clearance Tasks", "Task", "Green"),
	):
		doc.append(
			"shortcuts",
			{"type":"DocType","link_to":target,"doc_view":"List","label":label,"color":color},
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
			"Employee Separation": ["read"],
			"QD Exit Clearance": ["read"],
		},
		doc,
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	if not frappe.db.exists("DocType", "Employee Separation"):
		raise frappe.ValidationError("Standard Employee Separation is unavailable")
	if not frappe.db.exists("DocType", "QD Exit Clearance"):
		raise frappe.ValidationError("Exit Clearance DocType is unavailable")
	required_fields = (
		"custom_qd_separation_type",
		"custom_qd_final_working_date",
		"custom_qd_lifecycle_status",
		"custom_qd_exit_clearance",
	)
	meta = frappe.get_meta("Employee Separation")
	missing = [field for field in required_fields if not meta.has_field(field)]
	if missing:
		raise frappe.ValidationError(f"Missing Employee Separation fields: {', '.join(missing)}")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Separation Management workspace missing")
	return {
		"kept": ["Employee Separation", "Employee Separation Template"],
		"created": ["QD Exit Clearance", "QD Exit Clearance Item"],
		"stages": ["Clearance", "Final Payroll", "Exit Interview", "Access Deactivation", "Records Preservation", "Separation Complete"],
		"workspace": WORKSPACE,
		"verified": True,
	}
