frappe.ui.form.on("Appraisal", {
	refresh(frm) {
		if (
			frm.doc.custom_qd_pip_required &&
			!frm.doc.custom_qd_pip &&
			frappe.model.can_create("QD Performance Improvement Plan")
		) {
			frm.add_custom_button(__("Start PIP"), () => {
				frappe.call({
					method: "qd_hrms.performance.start_pip_from_appraisal",
					args: { appraisal: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "QD Performance Improvement Plan", r.message);
						}
					},
				});
			});
		}
		if (frm.doc.custom_qd_pip) {
			frm.add_custom_button(__("Open PIP"), () => {
				frappe.set_route("Form", "QD Performance Improvement Plan", frm.doc.custom_qd_pip);
			});
		}
	},
});
