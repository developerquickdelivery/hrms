"""Extend standard HRMS Employee Grade into the Quick Delivery HR grade master."""

from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def run():
	create_custom_fields(
		{
			"Employee Grade": [
				{
					"fieldname": "custom_qd_grade_details",
					"fieldtype": "Section Break",
					"label": "HR Grade Details",
					"insert_after": "default_base_pay",
				},
				{
					"fieldname": "custom_qd_grade_code",
					"fieldtype": "Data",
					"label": "Grade Code",
					"insert_after": "custom_qd_grade_details",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_grade_level",
					"fieldtype": "Int",
					"label": "Grade Level",
					"insert_after": "custom_qd_grade_code",
					"in_list_view": 1,
					"in_standard_filter": 1,
					"description": "Numeric rank used to order grades; higher values represent higher grades.",
				},
				{
					"fieldname": "custom_qd_grade_category",
					"fieldtype": "Select",
					"label": "Grade Category",
					"options": "\nEntry\nOperational\nProfessional\nSupervisory\nManagement\nExecutive",
					"insert_after": "custom_qd_grade_level",
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_grade_column",
					"fieldtype": "Column Break",
					"insert_after": "custom_qd_grade_category",
				},
				{
					"fieldname": "custom_qd_is_active",
					"fieldtype": "Check",
					"label": "Active",
					"default": "1",
					"insert_after": "custom_qd_grade_column",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_description",
					"fieldtype": "Small Text",
					"label": "Grade Description",
					"insert_after": "custom_qd_is_active",
				},
				{
					"fieldname": "custom_qd_salary_band",
					"fieldtype": "Section Break",
					"label": "Salary Band",
					"insert_after": "custom_qd_description",
				},
				{
					"fieldname": "custom_qd_minimum_base_pay",
					"fieldtype": "Currency",
					"label": "Minimum Base Pay",
					"options": "currency",
					"insert_after": "custom_qd_salary_band",
				},
				{
					"fieldname": "custom_qd_midpoint_base_pay",
					"fieldtype": "Currency",
					"label": "Midpoint Base Pay",
					"options": "currency",
					"insert_after": "custom_qd_minimum_base_pay",
				},
				{
					"fieldname": "custom_qd_maximum_base_pay",
					"fieldtype": "Currency",
					"label": "Maximum Base Pay",
					"options": "currency",
					"insert_after": "custom_qd_midpoint_base_pay",
				},
			],
			"Designation": [
				{
					"fieldname": "custom_qd_default_employee_grade",
					"fieldtype": "Link",
					"label": "Default Employee Grade",
					"options": "Employee Grade",
					"insert_after": "designation_name",
					"in_list_view": 1,
					"in_standard_filter": 1,
					"description": (
						"Optional default only. Designation remains the job title; "
						"Employee Grade remains the HR grade."
					),
				}
			],
		},
		ignore_validate=True,
		update=True,
	)

	return {
		"grade_master": "Employee Grade",
		"designation_default": "custom_qd_default_employee_grade",
	}

