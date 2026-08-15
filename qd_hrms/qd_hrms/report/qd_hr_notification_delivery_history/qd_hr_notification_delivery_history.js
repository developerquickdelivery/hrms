frappe.query_reports["QD HR Notification Delivery History"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "channel",
			label: __("Channel"),
			fieldtype: "Select",
			options: "\nIn-app\nEmail",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Data",
		},
	],
};
