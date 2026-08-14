app_name = "qd_hrms"
app_title = "Quick Delivery"
app_publisher = "Quick Delivery Service"
app_description = "Quick Delivery branding for ERPNext / Frappe HR"
app_email = "qd@quickdelivery.local"
app_license = "mit"

app_logo_url = "/assets/qd_hrms/images/qd-logo.png"
email_brand_image = "/assets/qd_hrms/images/qd-mark.svg"

app_include_css = ["qd_hrms.bundle.css", "/assets/qd_hrms/css/qd_hrms.css"]
app_include_js = ["qd_hrms.bundle.js", "/assets/qd_hrms/js/qd_hrms.js"]

web_include_css = "/assets/qd_hrms/css/qd_login.css"
web_include_js = "/assets/qd_hrms/js/qd_login.js"

website_context = {
	"favicon": "/assets/qd_hrms/images/qd-favicon.png",
	"splash_image": "/assets/qd_hrms/images/qd-splash.png",
	"app_name": "Quick Delivery",
	"brand_html": "Quick Delivery",
}

update_website_context = ["qd_hrms.setup.branding.update_website_context"]
extend_bootinfo = "qd_hrms.setup.branding.extend_bootinfo"
after_install = "qd_hrms.setup.install.after_install"
after_migrate = "qd_hrms.setup.install.after_migrate"

doctype_js = {
	"Employee": "public/js/employee.js",
	"Designation": "public/js/designation.js",
	"Salary Structure Assignment": "public/js/salary_structure_assignment.js",
	"Job Requisition": "public/js/job_requisition.js",
	"Employee Onboarding": "public/js/employee_onboarding.js",
	"Attendance Request": "public/js/attendance_request.js",
}

doc_events = {
	"Employee": {
		"validate": "qd_hrms.employee.validate",
		"before_insert": "qd_hrms.policy.validate_before_employee_insert",
	},
	"Employee Onboarding": {
		"on_submit": "qd_hrms.policy.on_onboarding_submit",
		"validate": "qd_hrms.policy.validate_onboarding",
	},
	"Attendance": {
		"validate": "qd_hrms.attendance.period_lock.validate_attendance",
		"before_submit": "qd_hrms.attendance.period_lock.validate_attendance",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_attendance",
	},
	"Attendance Request": {
		"validate": "qd_hrms.attendance.period_lock.validate_attendance_request",
		"before_submit": "qd_hrms.attendance.period_lock.validate_attendance_request",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_attendance_request",
	},
	"Employee Checkin": {
		"validate": "qd_hrms.attendance.period_lock.validate_checkin",
		"after_insert": "qd_hrms.integrations.biometric.on_checkin",
	},
}

before_request = ["qd_hrms.api.biometric.ignore_csrf_for_biometric"]

scheduler_events = {
	"cron": {
		"*/5 * * * *": ["qd_hrms.integrations.biometric.poll_active_devices"],
	}
}
