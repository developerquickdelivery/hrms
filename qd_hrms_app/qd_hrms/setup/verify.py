"""Release smoke checks for installed QD HRMS configuration."""

from __future__ import annotations

import frappe

VERIFY_METHODS = (
	"qd_hrms.setup.attendance_time.verify",
	"qd_hrms.setup.leave.verify",
	"qd_hrms.setup.performance.verify",
	"qd_hrms.setup.learning.verify",
	"qd_hrms.setup.licenses.verify",
	"qd_hrms.setup.employee_relations.verify",
	"qd_hrms.setup.employee_assets.verify",
	"qd_hrms.setup.employee_requests.verify",
	"qd_hrms.setup.separation.verify",
	"qd_hrms.setup.analytics.verify",
	"qd_hrms.setup.notifications.verify",
	"qd_hrms.setup.integrations.verify",
	"qd_hrms.setup.hr_admin.verify",
)

REQUIRED_DOCTYPES = (
	"Attendance Period",
	"Overtime Request",
	"Leave Adjustment Request",
	"QD Performance Improvement Plan",
	"QD Training Course",
	"QD License Type",
	"QD Employee License",
	"QD HR Case",
	"QD Employee Asset Assignment",
	"QD Employee Request",
	"QD Exit Clearance",
	"QD HR Integration",
	"QD Document Settings",
	"QD Retention Settings",
)

REQUIRED_APPS = {"frappe", "erpnext", "hrms", "qd_hrms"}


def run():
	installed_apps = set(frappe.get_installed_apps())
	missing_apps = sorted(REQUIRED_APPS - installed_apps)
	if missing_apps:
		raise frappe.ValidationError(f"Missing required apps: {', '.join(missing_apps)}")

	missing_doctypes = [
		doctype for doctype in REQUIRED_DOCTYPES if not frappe.db.exists("DocType", doctype)
	]
	if missing_doctypes:
		raise frappe.ValidationError(f"Missing DocTypes: {', '.join(missing_doctypes)}")

	results = {}
	for method in VERIFY_METHODS:
		results[method] = frappe.get_attr(method)()

	return {
		"verified": True,
		"apps": sorted(REQUIRED_APPS),
		"doctypes": len(REQUIRED_DOCTYPES),
		"checks": results,
	}
