frappe.ui.form.on("Job Requisition", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.requested_by && frappe.session.user !== "Administrator") {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
				if (r.message && r.message.name) {
					frm.set_value("requested_by", r.message.name);
				}
			});
		}
	},

	refresh(frm) {
		frm.set_intro(
			__(
				"Workforce Requisition: a manager requests headcount; HR Approves it, then uses Actions → Create Job Opening."
			),
			"blue"
		);

		if (frm.doc.custom_qd_urgency === "Critical") {
			frm.dashboard.set_headline_alert(__("Critical workforce request"), "red");
		} else if (frm.doc.custom_qd_urgency === "Urgent") {
			frm.dashboard.set_headline_alert(__("Urgent workforce request"), "orange");
		}
	},

	custom_qd_request_type(frm) {
		if (frm.doc.custom_qd_request_type !== "Replacement") {
			frm.set_value("custom_qd_replacement_for", null);
		}
	},
});
