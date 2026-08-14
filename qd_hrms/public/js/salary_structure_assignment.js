frappe.ui.form.on("Salary Structure Assignment", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.employee) {
			frm.add_custom_button(__("Open Employee"), () => {
				frappe.set_route("Form", "Employee", frm.doc.employee);
			});
		}
	},
});
