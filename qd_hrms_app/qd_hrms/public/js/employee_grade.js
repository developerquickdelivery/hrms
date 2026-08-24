frappe.ui.form.on("Employee Grade", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Employee Grade is the HR grade and salary-band master. Designation remains the employee's job title."
			),
			"blue"
		);
	},
});

