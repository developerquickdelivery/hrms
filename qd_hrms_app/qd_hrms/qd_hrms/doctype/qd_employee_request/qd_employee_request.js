frappe.ui.form.on("QD Employee Request", {
	setup(frm) {
		frm.set_query("request_type", () => ({ filters: { is_active: 1 } }));
	},

	onload(frm) {
		if (frm.is_new()) {
			if (!frm.doc.request_date) {
				frm.set_value("request_date", frappe.datetime.get_today());
			}
			if (!frm.doc.employee && frappe.boot.employee) {
				frm.set_value("employee", frappe.boot.employee);
			}
		}
	},

	request_type(frm) {
		if (!frm.doc.request_type) return;
		frappe.db
			.get_value("QD Employee Request Type", frm.doc.request_type, [
				"default_priority",
				"instructions",
				"requires_attachment",
			])
			.then(({ message }) => {
				if (!message) return;
				frm.set_value("priority", message.default_priority);
				if (message.instructions) {
					frm.dashboard.set_headline(message.instructions);
				}
				if (message.requires_attachment) {
					frm.set_df_property("attachment", "description", __("Required for this request type."));
				}
			});
	},
});
