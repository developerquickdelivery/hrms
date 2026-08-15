frappe.ui.form.on("Attendance Period", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Submitting locks attendance, check-ins, corrections, overtime, timesheets, and payroll for this date range. Reopen the period before making any change."
			),
			frm.doc.status === "Locked" ? "orange" : "blue"
		);

		if (frm.doc.docstatus === 1 && frm.doc.status === "Locked") {
			frm.add_custom_button(__("Reopen Period"), () => {
				frappe.prompt(
					[
						{
							fieldname: "reason",
							fieldtype: "Small Text",
							label: __("Reopening Reason"),
							reqd: 1,
						},
					],
					(values) => {
						frappe.call({
							method:
								"qd_hrms.qd_hrms.doctype.attendance_period.attendance_period.reopen_period",
							args: { name: frm.doc.name, reason: values.reason },
							freeze: true,
							callback: () => frm.reload_doc(),
						});
					},
					__("Reopen Attendance Period"),
					__("Reopen")
				);
			});
		}
	},
});
