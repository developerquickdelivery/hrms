frappe.listview_settings["Employee"] = {
	add_fields: [
		"status",
		"branch",
		"department",
		"grade",
		"custom_qd_position",
		"reports_to",
		"date_of_joining",
		"cell_number",
		"company_email",
		"image",
	],
	filters: [["status", "=", "Active"]],
	get_indicator(doc) {
		return [
			__(doc.status, null, "Employee"),
			{
				Active: "green",
				Inactive: "red",
				Left: "gray",
				Suspended: "orange",
			}[doc.status],
			"status,=," + doc.status,
		];
	},
};
