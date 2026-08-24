app_name = "qd_hrms"
app_title = "Quick Delivery"
app_publisher = "Quick Delivery Service"
app_description = "Quick Delivery branding for ERPNext / Frappe HR"
app_email = "qd@quickdelivery.local"
app_license = "mit"
required_apps = ["erpnext", "hrms"]

app_logo_url = "/assets/qd_hrms/images/qd-favicon.png"
email_brand_image = "/assets/qd_hrms/images/qd-mark.svg"

# Absolute asset paths so Desk works even when esbuild/bench build is skipped.
app_include_css = ["/assets/qd_hrms/css/qd_hrms.css"]
app_include_js = [
	"/assets/qd_hrms/js/qd_hrms.bundle.js",
	"/assets/qd_hrms/js/self_service.js",
]

web_include_css = "/assets/qd_hrms/css/qd_login.css"
web_include_js = "/assets/qd_hrms/js/qd_login.js"

website_context = {
	"favicon": "/assets/qd_hrms/images/qd-favicon.png",
	"splash_image": "/assets/qd_hrms/images/qd-favicon.png",
	"app_name": "Quick Delivery",
	"brand_html": "Quick Delivery",
}

update_website_context = ["qd_hrms.setup.branding.update_website_context"]
extend_bootinfo = [
	"qd_hrms.setup.branding.extend_bootinfo",
	"qd_hrms.self_service.extend_bootinfo",
]
after_install = "qd_hrms.setup.install.after_install"
after_migrate = "qd_hrms.setup.install.after_migrate"

override_doctype_class = {
	"Attendance Request": "qd_hrms.overrides.attendance_request.QDAttendanceRequest",
}

override_doctype_dashboards = {
	"Attendance": "qd_hrms.attendance.dashboard.get_data",
}

doctype_js = {
	"Employee": "public/js/employee.js",
	"Designation": "public/js/designation.js",
	"Department": "public/js/department.js",
	"Cost Center": "public/js/cost_center.js",
	"Employee Grade": "public/js/employee_grade.js",
	"Employee Promotion": "public/js/employee_promotion.js",
	"Job Offer": "public/js/job_offer.js",
	"Salary Structure Assignment": "public/js/salary_structure_assignment.js",
	"Job Requisition": "public/js/job_requisition.js",
	"Employee Onboarding": "public/js/employee_onboarding.js",
	"Attendance Request": "public/js/attendance_request.js",
	"Appraisal": "public/js/appraisal.js",
	"Employee Performance Feedback": "public/js/employee_performance_feedback.js",
	"Goal": "public/js/goal.js",
	"Employee Separation": "public/js/employee_separation.js",
}

doctype_list_js = {
	"Employee": "public/js/employee_list.js",
}

permission_query_conditions = {
	"Asset": "qd_hrms.self_service.asset_query",
	"Training Event": "qd_hrms.self_service.training_event_query",
	"QD Training Request": "qd_hrms.learning.training_request_query",
	"QD Training Nomination": "qd_hrms.learning.training_nomination_query",
	"QD Training Enrollment": "qd_hrms.learning.training_enrollment_query",
	"QD Training Attendance": "qd_hrms.learning.training_attendance_query",
	"QD Training Assessment": "qd_hrms.learning.training_assessment_query",
	"QD Training Certification": "qd_hrms.learning.training_certification_query",
	"QD Employee License": "qd_hrms.licenses.license_query",
	"QD Employee Document": "qd_hrms.self_service.qd_employee_document_query",
	"QD Policy Acknowledgement": "qd_hrms.self_service.qd_policy_acknowledgement_query",
	"QD Grievance": "qd_hrms.employee_relations.grievance_query",
	"QD Complaint": "qd_hrms.employee_relations.complaint_query",
	"QD Employee Asset Assignment": "qd_hrms.employee_assets.assignment_query",
	"QD Asset Loss Damage Case": "qd_hrms.employee_assets.loss_damage_query",
	"QD Asset Recovery": "qd_hrms.employee_assets.recovery_query",
	"QD Employee Request": "qd_hrms.employee_requests.employee_request_query",
	"Employee Separation": "qd_hrms.separation.separation_query",
	"QD Exit Clearance": "qd_hrms.separation.clearance_query",
	"Energy Point Log": "qd_hrms.self_service.energy_point_log_query",
	"QD Performance Improvement Plan": "qd_hrms.performance_permissions.pip_query",
	"QD Recognition Award": "qd_hrms.performance_permissions.recognition_query",
}

has_permission = {
	"Asset": "qd_hrms.self_service.has_asset_permission",
	"Training Event": "qd_hrms.self_service.has_training_event_permission",
	"QD Training Request": "qd_hrms.learning.has_training_record_permission",
	"QD Training Nomination": "qd_hrms.learning.has_training_record_permission",
	"QD Training Enrollment": "qd_hrms.learning.has_training_record_permission",
	"QD Training Attendance": "qd_hrms.learning.has_training_record_permission",
	"QD Training Assessment": "qd_hrms.learning.has_training_record_permission",
	"QD Training Certification": "qd_hrms.learning.has_training_record_permission",
	"QD Employee License": "qd_hrms.licenses.has_license_permission",
	"QD Employee Document": "qd_hrms.self_service.has_employee_document_permission",
	"QD Policy Acknowledgement": "qd_hrms.self_service.has_policy_acknowledgement_permission",
	"QD Grievance": "qd_hrms.employee_relations.has_er_record_permission",
	"QD Complaint": "qd_hrms.employee_relations.has_er_record_permission",
	"QD Employee Asset Assignment": "qd_hrms.employee_assets.has_employee_asset_permission",
	"QD Asset Loss Damage Case": "qd_hrms.employee_assets.has_employee_asset_permission",
	"QD Asset Recovery": "qd_hrms.employee_assets.has_employee_asset_permission",
	"QD Employee Request": "qd_hrms.employee_requests.has_employee_request_permission",
	"Employee Separation": "qd_hrms.separation.has_separation_permission",
	"QD Exit Clearance": "qd_hrms.separation.has_separation_permission",
	"Energy Point Log": "qd_hrms.self_service.has_energy_point_log_permission",
	"QD Performance Improvement Plan": "qd_hrms.performance_permissions.has_pip_permission",
	"QD Recognition Award": "qd_hrms.performance_permissions.has_recognition_permission",
}

doc_events = {
	"Cost Center": {
		"validate": "qd_hrms.organization.validate_cost_center",
	},
	"Employee Grade": {
		"validate": "qd_hrms.job_grades.validate_employee_grade",
	},
	"Employee Promotion": {
		"validate": "qd_hrms.promotions.validate_promotion",
		"on_submit": "qd_hrms.promotions.on_promotion_submit",
		"on_cancel": "qd_hrms.promotions.on_promotion_cancel",
	},
	"Job Offer": {
		"validate": "qd_hrms.job_offer.validate",
	},
	"Employee": {
		"validate": "qd_hrms.employee.validate",
		"before_insert": "qd_hrms.policy.validate_before_employee_insert",
		"after_insert": "qd_hrms.employment_history.on_employee_insert",
		"on_update": "qd_hrms.employment_history.on_employee_update",
	},
	"Employee Onboarding": {
		"on_submit": "qd_hrms.policy.on_onboarding_submit",
		"validate": "qd_hrms.policy.validate_onboarding",
	},
	"Leave Type": {
		"validate": "qd_hrms.leave_payroll.validate_leave_type",
	},
	"Leave Allocation": {
		"validate": "qd_hrms.leave_payroll.apply_carry_forward_formula",
	},
	"Leave Encashment": {
		"validate": "qd_hrms.leave_payroll.apply_encashment_formula",
	},
	"Leave Application": {
		"validate": "qd_hrms.leave.validate_leave_application",
		"before_submit": "qd_hrms.leave.before_submit_leave_application",
		"before_cancel": "qd_hrms.leave.before_cancel_leave_application",
		"on_trash": "qd_hrms.leave.validate_leave_application",
	},
	"Leave Adjustment Request": {
		"validate": "qd_hrms.leave.validate_leave_adjustment",
		"before_submit": "qd_hrms.leave.validate_leave_adjustment",
		"before_cancel": "qd_hrms.leave.validate_leave_adjustment",
		"on_trash": "qd_hrms.leave.validate_leave_adjustment",
	},
	"Appraisal": {
		"before_validate": "qd_hrms.performance.before_validate_appraisal",
		"validate": "qd_hrms.performance.validate_appraisal",
		"before_submit": "qd_hrms.performance.before_submit_appraisal",
	},
	"Employee Performance Feedback": {
		"validate": "qd_hrms.performance.validate_performance_feedback",
	},
	"Goal": {
		"validate": "qd_hrms.goal_metrics.validate_goal_metrics",
	},
	"Task": {
		"on_update": [
			"qd_hrms.goal_metrics.on_task_update",
			"qd_hrms.separation.sync_clearance_from_task",
		],
	},
	"Project": {
		"on_update": "qd_hrms.goal_metrics.on_project_update",
	},
	"Training Event": {
		"validate": "qd_hrms.learning.validate_training_event",
		"on_submit": "qd_hrms.learning.sync_session_enrollments",
		"on_update_after_submit": "qd_hrms.learning.sync_session_enrollments",
	},
	"Employee Separation": {
		"validate": "qd_hrms.separation.validate_employee_separation",
		"on_submit": "qd_hrms.separation.on_employee_separation_submit",
		"on_cancel": "qd_hrms.separation.on_employee_separation_cancel",
	},
	"Salary Structure Assignment": {
		"validate": "qd_hrms.leave_payroll.set_default_tax_slab",
		"on_submit": "qd_hrms.employment_history.on_salary_structure_assignment_submit",
	},
	"Attendance": {
		"validate": "qd_hrms.attendance.period_lock.validate_attendance",
		"before_submit": "qd_hrms.attendance.period_lock.validate_attendance",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_attendance",
		"on_update_after_submit": "qd_hrms.attendance.period_lock.validate_attendance",
		"on_trash": "qd_hrms.attendance.period_lock.validate_attendance",
	},
	"Attendance Request": {
		"validate": "qd_hrms.attendance.period_lock.validate_attendance_request",
		"before_submit": "qd_hrms.attendance.period_lock.validate_attendance_request",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_attendance_request",
		"on_update_after_submit": "qd_hrms.attendance.period_lock.validate_attendance_request",
		"on_trash": "qd_hrms.attendance.period_lock.validate_attendance_request",
	},
	"Employee Checkin": {
		"validate": "qd_hrms.attendance.period_lock.validate_checkin",
		"on_trash": "qd_hrms.attendance.period_lock.validate_checkin",
		"after_insert": "qd_hrms.integrations.biometric.on_checkin",
	},
	"Energy Point Log": {
		"after_insert": "qd_hrms.performance.sync_recognition_badge",
		"after_delete": "qd_hrms.performance.sync_recognition_badge",
	},
	"Overtime Request": {
		"validate": "qd_hrms.attendance.period_lock.validate_overtime_request",
		"before_submit": "qd_hrms.attendance.period_lock.validate_overtime_request",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_overtime_request",
		"on_trash": "qd_hrms.attendance.period_lock.validate_overtime_request",
	},
	"Payroll Entry": {
		"validate": "qd_hrms.attendance.period_lock.validate_payroll_entry",
		"before_submit": "qd_hrms.attendance.period_lock.validate_payroll_entry",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_payroll_entry",
		"on_trash": "qd_hrms.attendance.period_lock.validate_payroll_entry",
	},
	"Salary Slip": {
		"validate": "qd_hrms.attendance.period_lock.validate_salary_slip",
		"before_submit": "qd_hrms.attendance.period_lock.validate_salary_slip",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_salary_slip",
		"on_trash": "qd_hrms.attendance.period_lock.validate_salary_slip",
	},
	"Additional Salary": {
		"validate": "qd_hrms.attendance.period_lock.validate_additional_salary",
		"before_submit": "qd_hrms.attendance.period_lock.validate_additional_salary",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_additional_salary",
		"on_trash": "qd_hrms.attendance.period_lock.validate_additional_salary",
	},
	"Timesheet": {
		"validate": "qd_hrms.attendance.period_lock.validate_timesheet",
		"before_submit": "qd_hrms.attendance.period_lock.validate_timesheet",
		"before_cancel": "qd_hrms.attendance.period_lock.validate_timesheet",
		"on_trash": "qd_hrms.attendance.period_lock.validate_timesheet",
	},
}

before_request = ["qd_hrms.api.biometric.ignore_csrf_for_biometric"]

scheduler_events = {
	"daily": [
		"qd_hrms.reporting.sync_all_reporting_assignments",
		"qd_hrms.goal_metrics.reconcile_all_goal_metrics",
		"qd_hrms.learning.process_certification_expiry_notifications",
		"qd_hrms.licenses.process_license_renewals",
		"qd_hrms.employee_assets.mark_overdue_assignments",
		"qd_hrms.performance.reconcile_recognition_badges",
	],
	"cron": {
		"*/5 * * * *": [
			"qd_hrms.integrations.biometric.poll_active_devices",
			"qd_hrms.integrations.runtime.retry_failed_requests",
		],
	},
}
