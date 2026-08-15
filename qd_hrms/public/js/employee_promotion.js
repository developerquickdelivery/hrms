frappe.ui.form.on("Employee Promotion", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.promotion_date) {
			frm.set_value("promotion_date", frappe.datetime.get_today());
		}
	},

	setup(frm) {
		frm.set_query("custom_qd_new_position", () => ({
			filters: { active: 1 },
		}));
		frm.set_query("custom_qd_new_grade", () => ({
			filters: { custom_qd_is_active: 1 },
		}));
		frm.set_query("custom_qd_new_department", () => ({
			filters: frm.doc.company ? { company: frm.doc.company } : {},
		}));
		frm.set_query("custom_qd_new_manager", () => ({
			filters: {
				status: "Active",
				name: ["!=", frm.doc.employee || ""],
			},
		}));
		frm.set_query("custom_qd_new_salary_structure", () => ({
			filters: {
				docstatus: 1,
				is_active: "Yes",
				...(frm.doc.company ? { company: frm.doc.company } : {}),
			},
		}));
	},

	async custom_qd_new_position(frm) {
		if (!frm.doc.custom_qd_new_position) return;
		const { message } = await frappe.call({
			method: "qd_hrms.promotions.get_position_defaults",
			args: { position: frm.doc.custom_qd_new_position },
		});
		if (!message) return;
		const values = {};
		if (message.department) values.custom_qd_new_department = message.department;
		if (message.grade) values.custom_qd_new_grade = message.grade;
		if (message.manager) values.custom_qd_new_manager = message.manager;
		if (message.salary_structure) {
			values.custom_qd_new_salary_structure = message.salary_structure;
		}
		if (message.base) values.custom_qd_new_base_salary = message.base;
		await frm.set_value(values);
	},

	async custom_qd_new_grade(frm) {
		if (!frm.doc.custom_qd_new_grade) return;
		const { message } = await frappe.db.get_value(
			"Employee Grade",
			frm.doc.custom_qd_new_grade,
			["default_salary_structure", "default_base_pay"]
		);
		if (!message) return;
		const values = {};
		if (message.default_salary_structure && !frm.doc.custom_qd_new_salary_structure) {
			values.custom_qd_new_salary_structure = message.default_salary_structure;
		}
		if (message.default_base_pay && !frm.doc.custom_qd_new_base_salary) {
			values.custom_qd_new_base_salary = message.default_base_pay;
		}
		await frm.set_value(values);
	},

	refresh(frm) {
		frm.set_intro(
			__(
				"Final action “Make Effective” submits the standard Employee Promotion, updates Employee fields, and creates the Salary Structure Assignment."
			),
			"blue"
		);
	},
});

