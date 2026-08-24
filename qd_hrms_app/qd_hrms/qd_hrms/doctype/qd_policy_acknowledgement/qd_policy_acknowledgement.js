frappe.ui.form.on("QD Policy Acknowledgement", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.set_intro(
				__(
					"Read the policy, tick agreement, type your name, and draw your signature. Submit to lock the acknowledgement (required before day one)."
				),
				"blue"
			);
		}
		if (frm.doc.docstatus === 1) {
			frm.set_intro(__("Signed on {0}", [frm.doc.signed_on || ""]), "green");
			frm.set_df_property("signature", "read_only", 1);
			frm.set_df_property("acknowledged", "read_only", 1);
			frm.set_df_property("typed_full_name", "read_only", 1);
		}
	},

	policy(frm) {
		if (frm.doc.policy) {
			frappe.db.get_value("QD Policy", frm.doc.policy, ["policy_body", "version"], (r) => {
				if (r) {
					frm.set_value("policy_body", r.policy_body);
					frm.set_value("policy_version", r.version);
				}
			});
		}
	},
});
