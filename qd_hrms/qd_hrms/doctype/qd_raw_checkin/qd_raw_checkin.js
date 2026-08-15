frappe.ui.form.on("QD Raw Checkin", {
	refresh(frm) {
		if (!frm.is_new() && ["Failed", "Blocked"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Reprocess"), () => {
				frappe.call({
					method: "qd_hrms.api.biometric.reprocess_raw_checkin",
					args: { name: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}
	},
});
