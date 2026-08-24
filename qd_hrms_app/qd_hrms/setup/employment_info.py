"""Employment Information fields on standard Employee."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def run():
	create_custom_fields(_fields(), ignore_validate=True, update=True)
	_apply_labels()
	frappe.clear_cache(doctype="Employee")
	return {
		"added": [
			"custom_qd_probation_start",
			"custom_qd_probation_end",
			"custom_qd_contract_start",
			"custom_qd_work_location",
		],
		"existing": [
			"name",
			"employment_type",
			"status",
			"date_of_joining",
			"final_confirmation_date",
			"contract_end_date",
			"company",
			"branch",
			"custom_qd_business_unit",
			"department",
			"custom_qd_team",
			"custom_qd_position",
			"grade",
			"reports_to",
		],
	}


def _fields():
	return {
		"Employee": [
			{
				"fieldname": "custom_qd_employment_info_section",
				"fieldtype": "Section Break",
				"label": "Employment Information",
				"insert_after": "employment_type",
				"collapsible": 0,
			},
			{
				"fieldname": "custom_qd_probation_start",
				"fieldtype": "Date",
				"label": "Probation Start",
				"insert_after": "custom_qd_employment_info_section",
			},
			{
				"fieldname": "custom_qd_probation_end",
				"fieldtype": "Date",
				"label": "Probation End",
				"insert_after": "custom_qd_probation_start",
			},
			{
				"fieldname": "custom_qd_employment_info_col",
				"fieldtype": "Column Break",
				"insert_after": "custom_qd_probation_end",
			},
			{
				"fieldname": "custom_qd_contract_start",
				"fieldtype": "Date",
				"label": "Contract Start",
				"insert_after": "custom_qd_employment_info_col",
			},
			{
				"fieldname": "custom_qd_work_location",
				"fieldtype": "Data",
				"label": "Work Location",
				"insert_after": "custom_qd_contract_start",
				"fetch_from": "custom_qd_position.work_location",
				"fetch_if_empty": 1,
			},
		]
	}


def _apply_labels():
	labels = {
		"date_of_joining": "Hire Date",
		"contract_end_date": "Contract End",
		"custom_qd_business_unit": "Unit",
	}
	for fieldname, label in labels.items():
		_set_property(fieldname, "label", label, "Data")


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
