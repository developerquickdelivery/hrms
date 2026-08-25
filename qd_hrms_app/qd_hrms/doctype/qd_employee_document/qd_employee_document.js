frappe.ui.form.on("QD Employee Document", {
	onload(frm) {
		if (frm.is_new() && frappe.boot.employee && !frm.doc.employee) {
			frm.set_value("employee", frappe.boot.employee);
		}
	},
});
