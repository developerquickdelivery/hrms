frappe.ui.form.on("Salary Structure Assignment", {
	onload(frm) {
		// Single company: Quick Delivery — always default PAYE slab / company.
		if (frm.is_new()) {
			if (!frm.doc.company) {
				frm.set_value("company", "Quick Delivery");
			}
			if (!frm.doc.income_tax_slab) {
				frm.set_value(
					"income_tax_slab",
					"Ethiopia Employment Income Tax 2025"
				);
			}
		}
	},

	refresh(frm) {
		frm.set_intro(
			__(
				"QD Ethiopia payroll: use Basic (B), Employee Pension (7%) (PEN), Employer Pension (11%) (EPEN), and Income Tax (IT). Keep Basic before pension rows so formula B is available."
			),
			"blue"
		);
		if (!frm.is_new() && frm.doc.employee) {
			frm.add_custom_button(__("Open Employee"), () => {
				frappe.set_route("Form", "Employee", frm.doc.employee);
			});
		}
	},
});
