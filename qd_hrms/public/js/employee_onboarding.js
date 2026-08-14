frappe.ui.form.on("Employee Onboarding", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Use template <b>QD Standard Onboarding</b> for orientation and account/workspace tasks. Set <b>Onboarding Begins On</b> a few days before Date of Joining so policy e-signatures and Desk access complete before day one."
			),
			"blue"
		);

		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Issue Policy Acknowledgements"),
				() => {
					frappe.call({
						method: "qd_hrms.policy.issue_for_onboarding",
						args: { onboarding: frm.doc.name },
						freeze: true,
					}).then((r) => {
						frappe.show_alert({
							message: __("Policy acknowledgements ready to sign"),
							indicator: "green",
						});
						frappe.set_route("List", "QD Policy Acknowledgement", {
							employee_onboarding: frm.doc.name,
						});
					});
				},
				__("Policy")
			);

			frm.add_custom_button(
				__("Open Acknowledgements"),
				() => {
					frappe.set_route("List", "QD Policy Acknowledgement", {
						employee_onboarding: frm.doc.name,
					});
				},
				__("Policy")
			);
		}
	},
});
