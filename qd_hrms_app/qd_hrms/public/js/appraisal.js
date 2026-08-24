frappe.ui.form.on("Appraisal", {
	refresh(frm) {
		if (
			frm.doc.custom_qd_pip_required &&
			!frm.doc.custom_qd_pip &&
			frappe.model.can_create("QD Performance Improvement Plan")
		) {
			frm.add_custom_button(__("Start PIP"), () => {
				frappe.call({
					method: "qd_hrms.performance.start_pip_from_appraisal",
					args: { appraisal: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "QD Performance Improvement Plan", r.message);
						}
					},
				});
			});
		}
		if (frm.doc.custom_qd_pip) {
			frm.add_custom_button(__("Open PIP"), () => {
				frappe.set_route("Form", "QD Performance Improvement Plan", frm.doc.custom_qd_pip);
			});
		}
		if (!frm.is_new() && frm.doc.docstatus === 0 && frappe.model.can_create("Employee Performance Feedback")) {
			frm.add_custom_button(__("Request Peer / 360 Feedback"), () => {
				const dialog = new frappe.ui.Dialog({
					title: __("Request Peer / 360 Feedback"),
					fields: [
						{
							fieldname: "scope",
							fieldtype: "Select",
							label: __("Scope"),
							options: "Peer\n360",
							default: "Peer",
							reqd: 1,
						},
						{
							fieldname: "reviewers",
							fieldtype: "Table",
							label: __("Reviewers"),
							reqd: 1,
							cannot_add_rows: false,
							in_place_edit: true,
							fields: [
								{
									fieldname: "employee",
									fieldtype: "Link",
									options: "Employee",
									in_list_view: 1,
									reqd: 1,
									label: __("Employee"),
									get_query: () => ({
										filters: {
											name: ["!=", frm.doc.employee || ""],
											status: "Active",
										},
									}),
								},
							],
						},
					],
					primary_action_label: __("Request"),
					primary_action(values) {
						const reviewers = (values.reviewers || [])
							.map((row) => row.employee)
							.filter(Boolean);
						if (!reviewers.length) {
							frappe.msgprint(__("Select at least one reviewer."));
							return;
						}
						frappe.call({
							method: "qd_hrms.performance.request_peer_feedback",
							args: {
								appraisal: frm.doc.name,
								reviewers,
								scope: values.scope,
							},
							freeze: true,
							callback(r) {
								dialog.hide();
								if (r.message) {
									frappe.show_alert({
										message: __("Requested {0} feedback form(s).", [r.message.length]),
										indicator: "green",
									});
								}
							},
						});
					},
				});
				dialog.show();
			});
		}
	},
});
