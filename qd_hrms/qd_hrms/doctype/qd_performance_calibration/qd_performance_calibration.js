frappe.ui.form.on("QD Performance Calibration", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.facilitator) {
			frm.set_value("facilitator", frappe.session.user);
		}
	},
	appraisal_cycle(frm) {
		if (!frm.doc.appraisal_cycle || frm.doc.appraisals?.length) return;
		frappe.call({
			method: "qd_hrms.performance.load_calibration_rows",
			args: {
				appraisal_cycle: frm.doc.appraisal_cycle,
				department: frm.doc.department,
			},
			callback(r) {
				(r.message || []).forEach((row) => frm.add_child("appraisals", row));
				frm.refresh_field("appraisals");
			},
		});
	},
});
