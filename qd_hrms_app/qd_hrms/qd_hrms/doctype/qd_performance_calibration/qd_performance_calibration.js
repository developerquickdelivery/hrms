frappe.ui.form.on("QD Performance Calibration", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Open Nine-Box Grid"), () => {
				frappe.set_route("qd-nine-box-grid", frm.doc.name);
			});
		}
	},
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
