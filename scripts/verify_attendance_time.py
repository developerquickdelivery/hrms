"""Run with: bench --site qd.local console < scripts/verify_attendance_time.py"""

import frappe
from frappe.utils import add_days, nowdate, now_datetime

required_doctypes = {
	"Attendance Period",
	"Overtime Request",
	"QD Biometric Connector",
	"QD Biometric Employee Mapping",
	"QD Raw Checkin",
}
for doctype in required_doctypes:
	assert frappe.db.exists("DocType", doctype), doctype

assert not frappe.db.exists("DocType", "QD Attendance Period Lock")
assert frappe.db.get_value("Workflow", "QD Overtime Approval", "is_active") == 1
assert frappe.db.exists("Workspace", "Attendance Dashboard")
assert frappe.db.exists("Custom Field", "Attendance Request-custom_qd_requested_status")

hooks = frappe.get_hooks("override_doctype_class")
assert hooks.get("Attendance Request") == [
	"qd_hrms.overrides.attendance_request.QDAttendanceRequest"
]

company = frappe.db.get_value("Company", {}, "name")
lock_enforced = "skipped-no-company"
if company:
	from qd_hrms.attendance.period_lock import assert_period_open

	start = add_days(nowdate(), 3650)
	end = add_days(start, 6)
	period = frappe.get_doc(
		{
			"doctype": "Attendance Period",
			"period": f"VERIFY-{now_datetime()}",
			"company": company,
			"start_date": start,
			"end_date": end,
		}
	).insert(ignore_permissions=True)
	period.submit()
	try:
		assert_period_open(company, start, "verification")
		raise AssertionError("Period lock did not block")
	except frappe.ValidationError:
		lock_enforced = True

frappe.db.rollback()
print(
	{
		"doctypes": sorted(required_doctypes),
		"legacy_removed": True,
		"overtime_workflow": "active",
		"workspace": "Attendance Dashboard",
		"correction_override": True,
		"period_lock_enforced": lock_enforced,
	}
)
