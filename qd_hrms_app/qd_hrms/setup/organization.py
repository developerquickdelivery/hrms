"""Business Unit and Team hierarchy fields."""

from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def run():
	create_custom_fields(
		{
			"Department": [
				{
					"fieldname": "custom_qd_business_unit",
					"fieldtype": "Link",
					"label": "Business Unit",
					"options": "HR Business Unit",
					"insert_after": "parent_department",
					"in_list_view": 1,
					"in_standard_filter": 1,
					"description": (
						"Optional hierarchy link: Company → Branch → Business Unit → Department."
					),
				}
			],
			"Cost Center": [
				{
					"fieldname": "custom_qd_branch",
					"fieldtype": "Link",
					"label": "Branch",
					"options": "Branch",
					"insert_after": "company",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_business_unit",
					"fieldtype": "Link",
					"label": "Business Unit",
					"options": "HR Business Unit",
					"insert_after": "custom_qd_branch",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_department",
					"fieldtype": "Link",
					"label": "Department",
					"options": "Department",
					"insert_after": "custom_qd_business_unit",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
			]
		},
		ignore_validate=True,
		update=True,
	)

	return {
		"business_unit": "HR Business Unit",
		"team": "HR Team",
		"department_link": "custom_qd_business_unit",
		"cost_center_links": ["company", "custom_qd_branch", "custom_qd_business_unit", "custom_qd_department"],
	}

