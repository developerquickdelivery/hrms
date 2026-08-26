frappe.ui.form.on("QD Position", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.company) {
			frm.set_value("company", "Quick Delivery");
		}
	},

	setup(frm) {
		frm.set_query("business_unit", () => ({
			filters: {
				active: 1,
				...(frm.doc.company ? { company: frm.doc.company } : {}),
				...(frm.doc.branch ? { branch: frm.doc.branch } : {}),
			},
		}));
		frm.set_query("department", () => ({
			filters: {
				...(frm.doc.company ? { company: frm.doc.company } : {}),
				...(frm.doc.business_unit
					? { custom_qd_business_unit: frm.doc.business_unit }
					: {}),
			},
		}));
		frm.set_query("team", () => ({
			filters: {
				active: 1,
				...(frm.doc.department ? { department: frm.doc.department } : {}),
			},
		}));
		frm.set_query("employee_grade", () => ({
			filters: { custom_qd_is_active: 1 },
		}));
		frm.set_query("cost_center", () => ({
			filters: {
				...(frm.doc.company ? { company: frm.doc.company } : {}),
				...(frm.doc.branch ? { custom_qd_branch: frm.doc.branch } : {}),
				...(frm.doc.business_unit
					? { custom_qd_business_unit: frm.doc.business_unit }
					: {}),
				...(frm.doc.department
					? { custom_qd_department: frm.doc.department }
					: {}),
			},
		}));
		frm.set_query("reports_to_position", () => ({
			filters: {
				active: 1,
				...(frm.doc.name ? { name: ["!=", frm.doc.name] } : {}),
			},
		}));
	},

	async designation(frm) {
		if (!frm.doc.designation || frm.doc.employee_grade) return;
		const { message } = await frappe.db.get_value(
			"Designation",
			frm.doc.designation,
			"custom_qd_default_employee_grade"
		);
		if (message?.custom_qd_default_employee_grade) {
			await frm.set_value(
				"employee_grade",
				message.custom_qd_default_employee_grade
			);
		}
	},
});

