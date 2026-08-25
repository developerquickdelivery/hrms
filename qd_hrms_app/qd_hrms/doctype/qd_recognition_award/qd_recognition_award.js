frappe.ui.form.on("QD Recognition Award", {
	onload(frm) {
		if (frm.is_new()) {
			if (!frm.doc.recognized_by) {
				frm.set_value("recognized_by", frappe.session.user);
			}
			if (!frm.doc.recognition_date) {
				frm.set_value("recognition_date", frappe.datetime.get_today());
			}
		}
	},
});
