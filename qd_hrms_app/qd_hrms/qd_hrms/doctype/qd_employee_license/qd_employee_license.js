frappe.ui.form.on("QD Employee License", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status === "Renewed" || frm.doc.status === "Revoked") {
			return;
		}
		if (frappe.model.can_write("QD Employee License")) {
			frm.add_custom_button(__("Record Renewal"), () => {
				const dialog = new frappe.ui.Dialog({
					title: __("Record License Renewal"),
					fields: [
						{
							fieldname: "license_number",
							fieldtype: "Data",
							label: __("New License / Certificate Number"),
							default: frm.doc.license_number,
						},
						{
							fieldname: "issue_date",
							fieldtype: "Date",
							label: __("Issue Date"),
							reqd: 1,
							default: frappe.datetime.get_today(),
						},
						{
							fieldname: "expiry_date",
							fieldtype: "Date",
							label: __("Expiry Date"),
							reqd: 1,
						},
						{
							fieldname: "attachment",
							fieldtype: "Attach",
							label: __("Renewed Certificate"),
						},
					],
					primary_action_label: __("Save Renewal"),
					primary_action(values) {
						frappe.call({
							method: "qd_hrms.licenses.record_license_renewal",
							args: {
								license: frm.doc.name,
								license_number: values.license_number,
								issue_date: values.issue_date,
								expiry_date: values.expiry_date,
								attachment: values.attachment,
							},
							freeze: true,
							callback(r) {
								dialog.hide();
								if (r.message) {
									frappe.set_route("Form", "QD Employee License", r.message);
								}
							},
						});
					},
				});
				dialog.show();
			});
		}
		if (frm.doc.renewal_request) {
			frm.add_custom_button(__("Open Renewal Request"), () => {
				frappe.set_route("Form", "QD Employee Request", frm.doc.renewal_request);
			});
		}
	},
	license_type(frm) {
		if (!frm.doc.license_type) {
			return;
		}
		frappe.db.get_value(
			"QD License Type",
			frm.doc.license_type,
			["renewal_lead_days", "auto_renew_default", "required_for_work", "default_validity_days"],
			(values) => {
				if (!values) {
					return;
				}
				if (!frm.doc.renewal_lead_days) {
					frm.set_value("renewal_lead_days", values.renewal_lead_days);
				}
				if (frm.is_new()) {
					frm.set_value("auto_renew", values.auto_renew_default);
					frm.set_value("required_for_work", values.required_for_work);
					if (frm.doc.issue_date && !frm.doc.expiry_date && values.default_validity_days) {
						frm.set_value(
							"expiry_date",
							frappe.datetime.add_days(frm.doc.issue_date, values.default_validity_days)
						);
					}
				}
			}
		);
	},
});
