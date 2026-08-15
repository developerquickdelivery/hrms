frappe.ui.form.on("Employee Separation", {
	refresh(frm) {
		if (frm.doc.custom_qd_exit_clearance) {
			frm.add_custom_button(__("Open Exit Clearance"), () => {
				frappe.set_route("Form", "QD Exit Clearance", frm.doc.custom_qd_exit_clearance);
			});
		}
		if (frm.doc.docstatus !== 1) return;

		const actions = {
			"Final Payroll": ["Complete Final Payroll", "final_payroll"],
			"Exit Interview": ["Complete Exit Interview", "exit_interview"],
			"Access Deactivation": ["Deactivate Access", "deactivate_access"],
			"Records Preservation": ["Preserve Records & Complete", "preserve_records"],
		};
		const action = actions[frm.doc.custom_qd_lifecycle_status];
		if (action) {
			frm.add_custom_button(__(action[0]), () => advance_stage(frm, action[1]), __("Separation"));
		}
	},
});

function advance_stage(frm, action) {
	frappe.call({
		method: "qd_hrms.separation.advance_separation_stage",
		args: { separation: frm.doc.name, action },
		freeze: true,
		freeze_message: __("Updating separation stage..."),
		callback: () => frm.reload_doc(),
	});
}
