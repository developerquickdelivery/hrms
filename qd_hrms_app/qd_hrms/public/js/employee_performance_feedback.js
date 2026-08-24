frappe.ui.form.on("Employee Performance Feedback", {
	setup(frm) {
		frm.set_query("reviewer", () => ({
			filters: {
				name: ["!=", frm.doc.employee || ""],
				status: "Active",
			},
		}));
	},
	employee(frm) {
		if (frm.doc.employee && frm.doc.reviewer === frm.doc.employee) {
			frm.set_value("reviewer", null);
		}
	},
});
