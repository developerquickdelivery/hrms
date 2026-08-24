frappe.ui.form.on("Overtime Request", {
	onload(frm) {
		if (frm.is_new()) {
			if (!frm.doc.employee && frappe.boot.employee) {
				frm.set_value("employee", frappe.boot.employee);
			}
			if (!frm.doc.from_date) {
				frm.set_value("from_date", frappe.datetime.get_today());
			}
			if (!frm.doc.to_date) {
				frm.set_value("to_date", frm.doc.from_date || frappe.datetime.get_today());
			}
		}
	},

	setup(frm) {
		frm.set_query("attendance", () => ({
			filters: {
				employee: frm.doc.employee || "",
				docstatus: 1,
				attendance_date: ["between", [frm.doc.from_date, frm.doc.to_date]],
			},
		}));
	},

	requested_hours(frm) {
		if (
			frm.is_new() &&
			!frm.doc.approved_hours &&
			(frappe.user_roles.includes("HR Manager") ||
				frappe.user_roles.includes("HR User") ||
				frappe.user_roles.includes("Leave Approver"))
		) {
			frm.set_value("approved_hours", frm.doc.requested_hours);
		}
	},
});
