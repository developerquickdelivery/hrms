"""Employee Directory list columns and filters on standard Employee."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# List columns that are not already enabled on stock Employee.
LIST_VIEW_FIELDS = (
	"grade",
	"department",
	"branch",
	"reports_to",
	"status",
	"date_of_joining",
	"cell_number",
	"company_email",
)

# Prefer Position over Designation in the directory.
HIDE_LIST_FIELDS = ("designation",)

STANDARD_FILTERS = (
	"company",
	"branch",
	"department",
	"grade",
	"status",
)


def run():
	create_custom_fields(_fields(), ignore_validate=True, update=True)
	_apply_property_setters()
	frappe.clear_cache(doctype="Employee")
	return {
		"list_view": LIST_VIEW_FIELDS + ("custom_qd_position",),
		"filters": STANDARD_FILTERS
		+ ("custom_qd_position", "custom_qd_business_unit", "custom_qd_team"),
	}


def _fields():
	return {
		"Employee": [
			{
				"fieldname": "custom_qd_business_unit",
				"fieldtype": "Link",
				"label": "Business Unit",
				"options": "HR Business Unit",
				"insert_after": "custom_qd_position",
				"fetch_from": "custom_qd_position.business_unit",
				"fetch_if_empty": 1,
				"in_standard_filter": 1,
				"description": "Optional directory filter. Defaults from Position.",
			},
			{
				"fieldname": "custom_qd_team",
				"fieldtype": "Link",
				"label": "Team",
				"options": "HR Team",
				"insert_after": "custom_qd_business_unit",
				"fetch_from": "custom_qd_position.team",
				"fetch_if_empty": 1,
				"in_standard_filter": 1,
				"description": "Optional directory filter. Defaults from Position.",
			},
		]
	}


def _apply_property_setters():
	for fieldname in LIST_VIEW_FIELDS:
		_set_property(fieldname, "in_list_view", "1", "Check")

	for fieldname in HIDE_LIST_FIELDS:
		_set_property(fieldname, "in_list_view", "0", "Check")

	for fieldname in STANDARD_FILTERS:
		_set_property(fieldname, "in_standard_filter", "1", "Check")

	# Directory labels (form/list share labels; Manager is clearer than Reports To).
	_set_property("reports_to", "label", "Manager", "Data")
	_set_property("status", "label", "Employment Status", "Data")
	_set_property("cell_number", "label", "Phone", "Data")
	_set_property("company_email", "label", "Email", "Data")
	_set_property("date_of_joining", "label", "Hire Date", "Data")


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
