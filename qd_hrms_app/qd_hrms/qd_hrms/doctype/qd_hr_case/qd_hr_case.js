frappe.ui.form.on("QD HR Case", {
	onload(frm) {
		if (frm.is_new()) {
			if (!frm.doc.opened_on) {
				frm.set_value("opened_on", frappe.datetime.get_today());
			}
			if (!frm.doc.case_manager) {
				frm.set_value("case_manager", frappe.session.user);
			}
		}
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new() && frm.doc.case_status === "Under Investigation") {
			frm.dashboard.set_headline(__("Investigation in progress. Record findings before issuing a decision."));
		}
		if (frm.doc.source_doctype && frm.doc.source_name) {
			frm.add_custom_button(__("Open Source Record"), () => {
				frappe.set_route("Form", frm.doc.source_doctype, frm.doc.source_name);
			});
		}
	},
});
