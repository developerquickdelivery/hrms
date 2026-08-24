frappe.ui.form.on("Job Offer", {
	setup(frm) {
		frm.set_query("custom_qd_position", () => ({
			filters: {
				active: 1,
				...(frm.doc.company ? { company: frm.doc.company } : {}),
			},
		}));
		frm.set_query("custom_qd_employee_grade", () => ({
			filters: { custom_qd_is_active: 1 },
		}));
	},

	onload(frm) {
		if (!frm.is_new()) return;
		if (!frm.doc.offer_date) {
			frm.set_value("offer_date", frappe.datetime.get_today());
		}
		if (!frm.doc.job_offer_term_template) {
			frm.set_value("job_offer_term_template", "QD Standard Offer Terms");
		}
	},

	async custom_qd_position(frm) {
		if (!frm.doc.custom_qd_position) return;
		const { message } = await frappe.db.get_value(
			"QD Position",
			frm.doc.custom_qd_position,
			["designation", "employee_grade", "company"]
		);
		if (!message) return;

		const values = {};
		if (message.designation) values.designation = message.designation;
		if (message.employee_grade) values.custom_qd_employee_grade = message.employee_grade;
		if (message.company) values.company = message.company;
		await frm.set_value(values);
		if (values.custom_qd_employee_grade) {
			await frm.trigger("custom_qd_employee_grade");
		}
	},

	async custom_qd_employee_grade(frm) {
		if (!frm.doc.custom_qd_employee_grade) return;
		const { message } = await frappe.db.get_value(
			"Employee Grade",
			frm.doc.custom_qd_employee_grade,
			["currency", "default_base_pay"]
		);
		if (!message) return;

		const values = {};
		if (message.currency) values.custom_qd_salary_currency = message.currency;
		if (message.default_base_pay && !frm.doc.custom_qd_base_salary) {
			values.custom_qd_base_salary = message.default_base_pay;
		}
		await frm.set_value(values);
	},

	custom_qd_start_date(frm) {
		set_probation_end(frm);
	},

	custom_qd_probation_months(frm) {
		set_probation_end(frm);
	},

	refresh(frm) {
		frm.set_intro(
			__(
				"Complete the offer details, then print or email using QD Standard Offer Letter. Position and grade populate salary defaults."
			),
			"blue"
		);
	},
});

function set_probation_end(frm) {
	if (!frm.doc.custom_qd_start_date || !frm.doc.custom_qd_probation_months) {
		frm.set_value("custom_qd_probation_end_date", null);
		return;
	}
	frm.set_value(
		"custom_qd_probation_end_date",
		frappe.datetime.add_months(
			frm.doc.custom_qd_start_date,
			cint(frm.doc.custom_qd_probation_months)
		)
	);
}
