"""Sensitive bank, tax, and pension fields on standard Employee."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.permissions import add_permission, update_permission_property

SENSITIVE_PERMLEVEL = 1
SENSITIVE_STANDARD_FIELDS = ("bank_name", "bank_ac_no", "iban")
SENSITIVE_ROLES = ("System Manager", "HR Manager", "Payroll Manager")


def run():
	create_custom_fields(_fields(), ignore_validate=True, update=True)
	_configure_standard_bank_fields()
	_configure_sensitive_permissions()
	frappe.clear_cache(doctype="Employee")
	return {
		"kept_standard": ["bank_name", "bank_ac_no", "iban", "salary_mode"],
		"added": [
			"custom_qd_account_name",
			"custom_qd_tax_id",
			"custom_qd_pension_id",
			"custom_qd_pension_scheme",
			"custom_qd_tax_status",
			"custom_qd_statutory_effective_date",
		],
		"permlevel": SENSITIVE_PERMLEVEL,
		"roles": [role for role in SENSITIVE_ROLES if frappe.db.exists("Role", role)],
	}


def _fields():
	return {
		"Employee": [
			{
				"fieldname": "custom_qd_account_name",
				"fieldtype": "Data",
				"label": "Account Name",
				"insert_after": "bank_name",
				"depends_on": "eval:doc.salary_mode == 'Bank'",
				"permlevel": SENSITIVE_PERMLEVEL,
				"no_copy": 1,
			},
			{
				"fieldname": "custom_qd_statutory_section",
				"fieldtype": "Section Break",
				"label": "Tax and Pension",
				"insert_after": "iban",
				"permlevel": SENSITIVE_PERMLEVEL,
				"collapsible": 1,
			},
			{
				"fieldname": "custom_qd_tax_id",
				"fieldtype": "Data",
				"label": "Tax ID",
				"insert_after": "custom_qd_statutory_section",
				"permlevel": SENSITIVE_PERMLEVEL,
				"no_copy": 1,
			},
			{
				"fieldname": "custom_qd_tax_status",
				"fieldtype": "Select",
				"label": "Tax Status",
				"options": "\nTaxable\nExempt\nNon-Resident",
				"default": "Taxable",
				"insert_after": "custom_qd_tax_id",
				"permlevel": SENSITIVE_PERMLEVEL,
				"no_copy": 1,
			},
			{
				"fieldname": "custom_qd_statutory_column",
				"fieldtype": "Column Break",
				"insert_after": "custom_qd_tax_status",
				"permlevel": SENSITIVE_PERMLEVEL,
			},
			{
				"fieldname": "custom_qd_pension_id",
				"fieldtype": "Data",
				"label": "Pension ID",
				"insert_after": "custom_qd_statutory_column",
				"permlevel": SENSITIVE_PERMLEVEL,
				"no_copy": 1,
			},
			{
				"fieldname": "custom_qd_pension_scheme",
				"fieldtype": "Data",
				"label": "Pension Scheme",
				"insert_after": "custom_qd_pension_id",
				"permlevel": SENSITIVE_PERMLEVEL,
				"no_copy": 1,
			},
			{
				"fieldname": "custom_qd_statutory_effective_date",
				"fieldtype": "Date",
				"label": "Effective Date",
				"insert_after": "custom_qd_pension_scheme",
				"permlevel": SENSITIVE_PERMLEVEL,
				"no_copy": 1,
			},
		]
	}


def _configure_standard_bank_fields():
	labels = {
		"bank_name": "Bank",
		"bank_ac_no": "Account Number",
	}
	for fieldname in SENSITIVE_STANDARD_FIELDS:
		_set_property(fieldname, "permlevel", str(SENSITIVE_PERMLEVEL), "Int")
	for fieldname, label in labels.items():
		_set_property(fieldname, "label", label, "Data")


def _configure_sensitive_permissions():
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


def _set_property(fieldname, prop, value, property_type):
	frappe.db.delete(
		"Property Setter",
		{
			"doc_type": "Employee",
			"field_name": fieldname,
			"property": prop,
		},
	)
	make_property_setter(
		"Employee",
		fieldname,
		prop,
		value,
		property_type,
		validate_fields_for_doctype=False,
		is_system_generated=False,
	)
