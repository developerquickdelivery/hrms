frappe.ui.form.on("QD Biometric Device", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Register the hub device here. Map each employee Attendance Device ID. The listener service posts live punches to /api/method/qd_hrms.api.biometric.push_punches with header X-QD-Device-Secret."
			),
			"blue"
		);
		if (!frm.is_new()) {
			frm.add_custom_button(__("Sync Logs"), () => {
				frappe.set_route("List", "QD Biometric Sync Log", {
					biometric_device: frm.doc.name,
				});
			});
		}
	},
});
