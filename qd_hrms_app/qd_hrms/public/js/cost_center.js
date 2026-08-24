frappe.ui.form.on("Cost Center", {
	setup(frm) {
		frm.set_query("custom_qd_business_unit", () => ({
			filters: {
				active: 1,
				...(frm.doc.company ? { company: frm.doc.company } : {}),
				...(frm.doc.custom_qd_branch
					? { branch: frm.doc.custom_qd_branch }
					: {}),
			},
		}));

		frm.set_query("custom_qd_department", () => ({
			filters: {
				...(frm.doc.company ? { company: frm.doc.company } : {}),
				...(frm.doc.custom_qd_business_unit
					? { custom_qd_business_unit: frm.doc.custom_qd_business_unit }
					: {}),
			},
		}));
	},
});

