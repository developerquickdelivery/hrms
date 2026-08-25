frappe.ui.form.on("Employee Reporting Assignment", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.effective_from) {
			frm.set_value("effective_from", frappe.datetime.get_today());
		}
	},

	setup(frm) {
		for (const fieldname of [
			"primary_manager",
			"secondary_manager",
			"acting_manager",
		]) {
			frm.set_query(fieldname, () => ({
				filters: {
					status: "Active",
					name: ["!=", frm.doc.employee || ""],
				},
			}));
		}
	},

	async employee(frm) {
		if (!frm.doc.employee || frm.doc.primary_manager) return;
		const { message } = await frappe.db.get_value(
			"Employee",
			frm.doc.employee,
			"reports_to"
		);
		if (message?.reports_to) {
			await frm.set_value("primary_manager", message.reports_to);
		}
	},

	refresh(frm) {
		frm.set_intro(
			__(
				"Submitted assignments preserve reporting history. During an effective period, Acting Manager takes precedence over Primary Manager in the standard Reports To field."
			),
			"blue"
		);
	},
});

