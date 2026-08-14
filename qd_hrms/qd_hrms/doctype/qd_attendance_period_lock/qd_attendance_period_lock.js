frappe.ui.form.on("QD Attendance Period Lock", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Submit to lock Attendance, Attendance Requests, and Checkins in this date range. Only HR Manager / System Manager can still post. Cancel to unlock."
			),
			"blue"
		);
	},
});
