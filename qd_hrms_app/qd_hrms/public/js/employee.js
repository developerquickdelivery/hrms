frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (frm.doc.custom_qd_is_acting) {
			frm.dashboard.set_headline_alert(
				__("Acting as {0}", [frm.doc.custom_qd_acting_designation || __("unspecified designation")]),
				"orange"
			);
		}

		if (frm.is_new()) return;
		if (frappe.boot.qd_is_self_service) return;

		frm.add_custom_button(
			__("Employment History"),
			() => {
				frappe.set_route("List", "Employee Employment History", {
					employee: frm.doc.name,
				});
			},
			__("History")
		);

		frm.add_custom_button(
			__("New Reporting Assignment"),
			() => {
				frappe.new_doc("Employee Reporting Assignment", {
					employee: frm.doc.name,
					primary_manager: frm.doc.reports_to,
					effective_from: frappe.datetime.get_today(),
				});
			},
			__("Reporting")
		);

		frm.add_custom_button(
			__("Reporting History"),
			() => {
				frappe.set_route("List", "Employee Reporting Assignment", {
					employee: frm.doc.name,
				});
			},
			__("Reporting")
		);

		frm.add_custom_button(
			__("New Salary Change"),
			() => {
				frappe.new_doc("Salary Structure Assignment", {
					employee: frm.doc.name,
					company: frm.doc.company,
					department: frm.doc.department,
					designation: frm.doc.designation,
				});
			},
			__("Salary")
		);

		frm.add_custom_button(
			__("Salary Change History"),
			() => {
				frappe.set_route("List", "Salary Structure Assignment", {
					employee: frm.doc.name,
				});
			},
			__("Salary")
		);

		if (frm.fields_dict.attendance_device_id) {
			frm.set_df_property(
				"attendance_device_id",
				"description",
				__("Must match the user ID on the hub biometric device so live punches map to this employee.")
			);
		}
	},

	custom_qd_is_acting(frm) {
		if (!frm.doc.custom_qd_is_acting) {
			frm.set_value("custom_qd_acting_designation", null);
			frm.set_value("custom_qd_acting_for", null);
			frm.set_value("custom_qd_acting_from", null);
			frm.set_value("custom_qd_acting_to", null);
			frm.set_value("custom_qd_acting_notes", null);
		} else if (!frm.doc.custom_qd_acting_from) {
			frm.set_value("custom_qd_acting_from", frappe.datetime.get_today());
		}
	},

	async designation(frm) {
		if (!frm.doc.designation || frm.doc.grade) return;
		const { message } = await frappe.db.get_value(
			"Designation",
			frm.doc.designation,
			"custom_qd_default_employee_grade"
		);
		if (message?.custom_qd_default_employee_grade) {
			await frm.set_value("grade", message.custom_qd_default_employee_grade);
		}
	},

	async custom_qd_position(frm) {
		if (!frm.doc.custom_qd_position) return;
		const { message } = await frappe.db.get_value(
			"QD Position",
			frm.doc.custom_qd_position,
			[
				"company",
				"branch",
				"business_unit",
				"department",
				"team",
				"designation",
				"employee_grade",
				"work_location",
			]
		);
		if (!message) return;

		const values = {};
		for (const [target, source] of Object.entries({
			company: "company",
			branch: "branch",
			custom_qd_business_unit: "business_unit",
			department: "department",
			custom_qd_team: "team",
			designation: "designation",
			grade: "employee_grade",
			custom_qd_work_location: "work_location",
		})) {
			if (message[source] && frm.fields_dict[target]) {
				values[target] = message[source];
			}
		}
		await frm.set_value(values);
	},

	setup(frm) {
		frm.set_query("custom_qd_position", () => ({
			filters: { active: 1 },
		}));
		frm.set_query("custom_qd_acting_designation", () => ({
			filters: { custom_qd_eligible_for_acting: 1 },
		}));
		frm.set_query("custom_qd_acting_for", () => ({
			filters: {
				name: ["!=", frm.doc.name || ""],
				status: "Active",
			},
		}));
	},
});
