(() => {
	const CONTACT_FIELDS = new Set([
		"image",
		"cell_number",
		"personal_email",
		"prefered_contact_email",
		"prefered_email",
		"current_address",
		"current_accommodation_type",
		"permanent_address",
		"permanent_accommodation_type",
		"person_to_be_contacted",
		"emergency_phone_number",
		"relation",
		"bio",
		"unsubscribed",
	]);
	const BREAK_TYPES = new Set([
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
		"Button",
		"Heading",
		"Fold",
	]);
	const EMPLOYEE_FILTER_DOCTYPES = {
		Employee: "name",
		"Leave Application": "employee",
		Attendance: "employee",
		"Attendance Request": "employee",
		"Shift Request": "employee",
		"Expense Claim": "employee",
		"Employee Advance": "employee",
		"Travel Request": "employee",
		"Leave Encashment": "employee",
		"Overtime Request": "employee",
		"Salary Slip": "employee",
		"Salary Structure Assignment": "employee",
		Appraisal: "employee",
		Goal: "employee",
		"Employee Performance Feedback": "employee",
		"QD Performance Improvement Plan": "employee",
		"QD Training Request": "employee",
		"QD Training Nomination": "employee",
		"QD Training Enrollment": "employee",
		"QD Training Attendance": "employee",
		"QD Training Assessment": "employee",
		"QD Training Certification": "employee",
		"QD Grievance": "employee",
		"QD Complaint": "employee",
		"QD Employee Asset Assignment": "employee",
		"QD Asset Loss Damage Case": "employee",
		"QD Asset Recovery": "employee",
		"QD Employee Request": "employee",
		"Employee Separation": "employee",
		"QD Exit Clearance": "employee",
		"Appointment Letter": "employee",
		"Employee Grievance": "employee",
		"Compensatory Leave Request": "employee",
		"Employee Tax Exemption Declaration": "employee",
		"Training Feedback": "employee",
		"Employee Referral": "employee",
		Timesheet: "employee",
		"Employee Checkin": "employee",
		"QD Employee Document": "employee",
		"QD Policy Acknowledgement": "employee",
		"Employee Employment History": "employee",
		"Employee Promotion": "employee",
		Asset: "custodian",
	};
	const HIDE_ON_CREATE = Object.keys(EMPLOYEE_FILTER_DOCTYPES).filter(
		(dt) => dt !== "Employee" && EMPLOYEE_FILTER_DOCTYPES[dt] !== "name"
	);

	frappe.provide("qd_hrms.self_service");

	function isSelfService() {
		if (frappe.boot && frappe.boot.qd_is_self_service) return true;
		const roles = frappe.user_roles || [];
		if (
			roles.includes("System Manager") ||
			roles.includes("HR Manager") ||
			roles.includes("HR User") ||
			roles.includes("Payroll Manager")
		) {
			return false;
		}
		return roles.includes("Employee Self Service") || roles.includes("Employee");
	}

	qd_hrms.self_service.is_self_service_user = isSelfService;

	function ownEmployee() {
		return (frappe.boot && frappe.boot.employee) || null;
	}

	function applyOwnFilter(listview) {
		if (!isSelfService()) return;
		const employee = ownEmployee();
		if (!employee) return;
		const field = EMPLOYEE_FILTER_DOCTYPES[listview.doctype];
		if (!field) return;
		listview.filters = listview.filters || [];
		const exists = listview.filters.some((f) => f[1] === field);
		if (exists) return;
		listview.filters.push([listview.doctype, field, "=", employee]);
	}

	function patchListView() {
		if (!frappe.views || !frappe.views.ListView || frappe.views.ListView.prototype._qdEssPatched) {
			return;
		}
		const orig = frappe.views.ListView.prototype.setup_defaults;
		frappe.views.ListView.prototype.setup_defaults = function () {
			const result = orig.apply(this, arguments);
			applyOwnFilter(this);
			return result;
		};
		frappe.views.ListView.prototype._qdEssPatched = true;
	}

	function lockEmployeeForm(frm) {
		(frm.meta.fields || []).forEach((df) => {
			if (BREAK_TYPES.has(df.fieldtype) || CONTACT_FIELDS.has(df.fieldname)) return;
			frm.set_df_property(df.fieldname, "read_only", 1);
		});
		frm.disable_save = false;
		["History", "Reporting", "Salary"].forEach((group) => {
			if (frm.page && frm.page.clear_custom_actions_of_group) {
				try {
					frm.page.clear_custom_actions_of_group(group);
				} catch (e) {
					/* ignore */
				}
			}
		});
	}

	function bindForms() {
		if (window._qdEssFormsBound) return;
		window._qdEssFormsBound = true;

		HIDE_ON_CREATE.forEach((dt) => {
			const field = EMPLOYEE_FILTER_DOCTYPES[dt];
			frappe.ui.form.on(dt, {
				onload(frm) {
					if (!isSelfService()) return;
					const employee = ownEmployee();
					if (frm.is_new() && employee && frm.fields_dict[field] && !frm.doc[field]) {
						frm.set_value(field, employee);
					}
					if (frm.fields_dict[field]) {
						frm.set_df_property(field, "read_only", 1);
						if (frm.is_new()) {
							frm.set_df_property(field, "hidden", 1);
						}
					}
				},
			});
		});

		frappe.ui.form.on("Employee", {
			refresh(frm) {
				if (!isSelfService()) return;
				lockEmployeeForm(frm);
			},
		});

		frappe.ui.form.on("QD Employee Document", {
			onload(frm) {
				if (frm.is_new() && !isSelfService()) {
					frm.set_value("issued_by_hr", 1);
				}
				if (isSelfService()) {
					frm.set_df_property("issued_by_hr", "read_only", 1);
					frm.set_df_property("employee", "read_only", 1);
				}
			},
		});
	}

	function boot() {
		patchListView();
		if (frappe.ui && frappe.ui.form) {
			bindForms();
		}
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}

	document.addEventListener("page-change", patchListView);
})();
