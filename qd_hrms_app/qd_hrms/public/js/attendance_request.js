frappe.ui.form.on("Attendance Request", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.employee && frappe.session.user !== "Administrator") {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
				if (r.message && r.message.name) {
					frm.set_value("employee", r.message.name);
				}
			});
		}
	},

	refresh(frm) {
		frm.set_intro(
			__(
				"Attendance Correction: select the requested status and submit for approval. Locked periods must be formally reopened before any correction."
			),
			"blue"
		);
	},

	reason(frm) {
		if (frm.doc.reason === "Work From Home") {
			frm.set_value("custom_qd_requested_status", "Work From Home");
		} else if (!frm.doc.custom_qd_requested_status) {
			frm.set_value("custom_qd_requested_status", "Present");
		}
	},

	employee(frm) {
		frm.trigger("from_date");
	},

	from_date(frm) {
		if (!frm.doc.employee || !frm.doc.from_date) return;
		frappe.db
			.get_value("Attendance", { employee: frm.doc.employee, attendance_date: frm.doc.from_date, docstatus: 1 }, "status")
			.then((r) => {
				if (r.message && r.message.status) {
					frm.set_value("custom_qd_original_status", r.message.status);
				}
			});
	},
});
