frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (frm.doc.custom_qd_is_acting) {
			frm.dashboard.set_headline_alert(
				__("Acting as {0}", [frm.doc.custom_qd_acting_designation || __("unspecified designation")]),
				"orange"
			);
		}

		if (frm.is_new()) return;

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

	setup(frm) {
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
