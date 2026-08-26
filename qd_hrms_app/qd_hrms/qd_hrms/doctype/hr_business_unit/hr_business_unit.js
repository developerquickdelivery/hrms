frappe.ui.form.on("HR Business Unit", {
	setup(frm) {
		frm.set_query("unit_head", () => ({
			filters: {
				status: "Active",
				...(frm.doc.company ? { company: frm.doc.company } : {}),
				...(frm.doc.branch ? { branch: frm.doc.branch } : {}),
			},
		}));
		frm.set_query("parent_unit", () => ({
			filters: {
				active: 1,
				...(frm.doc.name ? { name: ["!=", frm.doc.name] } : {}),
			},
		}));
	},
});

