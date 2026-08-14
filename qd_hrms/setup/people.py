"""Salary Changes (Salary Structure Assignment) + Acting Assignment custom fields."""

from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

SALARY_CHANGE_TYPES = "\n".join(
	[
		"",
		"Increment",
		"Promotion",
		"Adjustment",
		"Correction",
		"Acting Allowance",
		"Other",
	]
)


def run():
	create_custom_fields(_fields(), ignore_validate=True, update=True)
	return {
		"salary_changes": "Salary Structure Assignment",
		"acting_fields": ["Employee", "Designation"],
		"custom_fields": _existing(),
	}


def _existing():
	import frappe

	rows = frappe.get_all(
		"Custom Field",
		filters={"fieldname": ["like", "custom_qd_%"]},
		fields=["dt", "fieldname", "label", "fieldtype"],
		order_by="dt, idx",
	)
	return rows


def _fields():
	return {
		"Employee": [
			{
				"fieldname": "custom_qd_acting_section",
				"fieldtype": "Section Break",
				"label": "Acting Assignment",
				"insert_after": "designation",
				"collapsible": 1,
			},
			{
				"fieldname": "custom_qd_is_acting",
				"fieldtype": "Check",
				"label": "Currently Acting",
				"insert_after": "custom_qd_acting_section",
				"in_standard_filter": 1,
			},
			{
				"fieldname": "custom_qd_acting_designation",
				"fieldtype": "Link",
				"label": "Acting Designation",
				"options": "Designation",
				"insert_after": "custom_qd_is_acting",
				"depends_on": "eval:doc.custom_qd_is_acting",
				"mandatory_depends_on": "eval:doc.custom_qd_is_acting",
			},
			{
				"fieldname": "custom_qd_acting_for",
				"fieldtype": "Link",
				"label": "Acting For",
				"options": "Employee",
				"insert_after": "custom_qd_acting_designation",
				"depends_on": "eval:doc.custom_qd_is_acting",
				"description": "Employee being covered while this person is acting.",
			},
			{
				"fieldname": "custom_qd_acting_col",
				"fieldtype": "Column Break",
				"insert_after": "custom_qd_acting_for",
			},
			{
				"fieldname": "custom_qd_acting_from",
				"fieldtype": "Date",
				"label": "Acting From",
				"insert_after": "custom_qd_acting_col",
				"depends_on": "eval:doc.custom_qd_is_acting",
				"mandatory_depends_on": "eval:doc.custom_qd_is_acting",
			},
			{
				"fieldname": "custom_qd_acting_to",
				"fieldtype": "Date",
				"label": "Acting To",
				"insert_after": "custom_qd_acting_from",
				"depends_on": "eval:doc.custom_qd_is_acting",
			},
			{
				"fieldname": "custom_qd_acting_notes",
				"fieldtype": "Small Text",
				"label": "Acting Notes",
				"insert_after": "custom_qd_acting_to",
				"depends_on": "eval:doc.custom_qd_is_acting",
			},
			{
				"fieldname": "custom_qd_salary_changes_section",
				"fieldtype": "Section Break",
				"label": "Salary Changes",
				"insert_after": "salary_mode",
				"collapsible": 0,
			},
			{
				"fieldname": "custom_qd_salary_changes_help",
				"fieldtype": "HTML",
				"label": "Salary Changes Help",
				"insert_after": "custom_qd_salary_changes_section",
				"options": (
					"<div class='form-message blue' style='margin-bottom:0'>"
					"<b>Salary Changes</b> are recorded with <b>Salary Structure Assignment</b>. "
					"Create a new assignment (new From Date + Base). Earlier assignments stay as history. "
					"Use the <b>Salary</b> button on this form, or Connections → Payroll."
					"</div>"
				),
			},
		],
		"Designation": [
			{
				"fieldname": "custom_qd_acting_section",
				"fieldtype": "Section Break",
				"label": "Acting Assignment",
				"insert_after": "description",
			},
			{
				"fieldname": "custom_qd_eligible_for_acting",
				"fieldtype": "Check",
				"label": "Eligible for Acting Assignment",
				"insert_after": "custom_qd_acting_section",
				"in_list_view": 1,
				"description": "Allow this designation to be selected as an acting designation on Employee.",
			},
			{
				"fieldname": "custom_qd_acting_notes",
				"fieldtype": "Small Text",
				"label": "Acting Role Notes",
				"insert_after": "custom_qd_eligible_for_acting",
				"depends_on": "eval:doc.custom_qd_eligible_for_acting",
			},
		],
		"Salary Structure Assignment": [
			{
				"fieldname": "custom_qd_salary_change_section",
				"fieldtype": "Section Break",
				"label": "Salary Change",
				"insert_after": "from_date",
			},
			{
				"fieldname": "custom_qd_salary_change_type",
				"fieldtype": "Select",
				"label": "Change Type",
				"options": SALARY_CHANGE_TYPES,
				"insert_after": "custom_qd_salary_change_section",
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "custom_qd_salary_change_notes",
				"fieldtype": "Small Text",
				"label": "Change Notes",
				"insert_after": "custom_qd_salary_change_type",
			},
		],
	}
