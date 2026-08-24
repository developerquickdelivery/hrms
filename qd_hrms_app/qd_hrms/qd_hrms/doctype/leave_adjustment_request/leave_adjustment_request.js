frappe.ui.form.on("Leave Adjustment Request", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.effective_from) {
			const today = frappe.datetime.get_today();
			frm.set_value({
				effective_from: today,
				effective_to: frappe.datetime.year_end(today),
			});
		}
	},

	setup(frm) {
		frm.set_query("reference_leave_application", () => ({
			filters: { employee: frm.doc.employee || "" },
		}));
		frm.set_query("reference_leave_allocation", () => ({
			filters: {
				employee: frm.doc.employee || "",
				leave_type: frm.doc.leave_type || "",
			},
		}));
	},
});
