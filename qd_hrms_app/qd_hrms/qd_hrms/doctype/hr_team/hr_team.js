frappe.ui.form.on("HR Team", {
	setup(frm) {
		frm.set_query("team_leader", () => ({
			filters: {
				status: "Active",
				...(frm.doc.department ? { department: frm.doc.department } : {}),
			},
		}));

		frm.set_query("employee", "members", () => ({
			filters: {
				status: "Active",
				...(frm.doc.department ? { department: frm.doc.department } : {}),
			},
		}));
	},
});

