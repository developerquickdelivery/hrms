frappe.ui.form.on("Department", {
	setup(frm) {
		frm.set_query("custom_qd_business_unit", () => ({
			filters: {
				active: 1,
				...(frm.doc.company ? { company: frm.doc.company } : {}),
			},
		}));
	},
});

