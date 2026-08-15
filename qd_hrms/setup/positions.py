"""Link custom headcount positions to standard Employee records."""

from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def run():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "custom_qd_position",
					"fieldtype": "Link",
					"label": "Position",
					"options": "QD Position",
					"insert_after": "grade",
					"in_list_view": 1,
					"in_standard_filter": 1,
					"description": (
						"One approved headcount seat. The Position supplies organization, "
						"Designation, Employee Grade, and reporting defaults."
					),
				}
			]
		},
		ignore_validate=True,
		update=True,
	)

	return {
		"position_master": "QD Position",
		"employee_link": "custom_qd_position",
	}

