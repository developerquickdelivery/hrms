frappe.ui.form.on("QD HR Integration", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Test Connection"), () => {
			frappe.call({
				method: "qd_hrms.integrations.runtime.test_connection",
				args: { integration: frm.doc.name },
				freeze: true,
				freeze_message: __("Testing connection..."),
				callback: (response) => {
					if (response.message) {
						const indicator = response.message.connected ? "green" : "red";
						frappe.msgprint({
							title: __("Connection Test"),
							message: response.message.message,
							indicator,
						});
					}
					frm.reload_doc();
				},
			});
		});

		frm.add_custom_button(__("Operation Logs"), () => {
			frappe.set_route("List", "QD HR Integration Log", {
				integration: frm.doc.name,
			});
		}, __("View"));

		frm.add_custom_button(__("Audit Trail"), () => {
			frappe.set_route("List", "QD HR Integration Audit", {
				integration: frm.doc.name,
			});
		}, __("View"));
	},
});
