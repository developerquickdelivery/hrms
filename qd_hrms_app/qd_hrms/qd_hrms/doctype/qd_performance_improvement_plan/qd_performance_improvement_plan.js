frappe.ui.form.on("QD Performance Improvement Plan", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.start_date) {
			frm.set_value("start_date", frappe.datetime.get_today());
		}
	},
	setup(frm) {
		frm.set_query("appraisal", () => ({
			filters: { employee: frm.doc.employee || "" },
		}));
		frm.set_query("goal", "objectives", () => ({
			filters: { employee: frm.doc.employee || "" },
		}));
	},
});
