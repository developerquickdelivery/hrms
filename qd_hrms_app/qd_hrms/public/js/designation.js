frappe.ui.form.on("Designation", {
	refresh(frm) {
		if (frm.doc.custom_qd_eligible_for_acting) {
			frm.dashboard.set_headline_alert(
				__("This designation can be used for Acting Assignments on Employee."),
				"blue"
			);
		}
	},
});
