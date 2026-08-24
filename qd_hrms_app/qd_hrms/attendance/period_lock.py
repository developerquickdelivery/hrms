"""Block attendance and payroll changes while an Attendance Period is locked."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate


def get_lock(company: str, start_date, end_date=None) -> str | None:
	if not company or not start_date:
		return None
	start = getdate(start_date)
	end = getdate(end_date or start_date)
	return frappe.db.exists(
		"Attendance Period",
		{
			"company": company,
			"docstatus": 1,
			"status": "Locked",
			"start_date": ("<=", end),
			"end_date": (">=", start),
		},
	)


def assert_period_open(company: str, start_date, action: str = "change attendance", end_date=None):
	"""There is intentionally no role bypass: reopen first, then modify."""
	lock = get_lock(company, start_date, end_date)
	if not lock:
		return
	frappe.throw(
		_(
			"Attendance period is locked ({0}). {1} is not allowed. "
			"An HR Manager or System Manager must reopen the period first."
		).format(lock, action),
		title=_("Period Locked"),
	)


def validate_attendance(doc, method=None):
	assert_period_open(doc.company, doc.attendance_date, _("submit or change Attendance"))


def validate_attendance_request(doc, method=None):
	if not doc.from_date or not doc.to_date:
		return
	assert_period_open(
		doc.company,
		doc.from_date,
		_("submit or change an Attendance Correction"),
		doc.to_date,
	)


def validate_checkin(doc, method=None):
	company = None
	if doc.employee:
		company = frappe.db.get_value("Employee", doc.employee, "company")
	stamp = doc.time or frappe.utils.now_datetime()
	assert_period_open(company, stamp, _("record Employee Checkin"))


def validate_overtime_request(doc, method=None):
	assert_period_open(
		doc.company,
		doc.from_date,
		_("submit or change an Overtime Request"),
		doc.to_date or doc.from_date,
	)


def validate_payroll_entry(doc, method=None):
	assert_period_open(
		doc.company,
		doc.start_date,
		_("create or change Payroll Entry"),
		doc.end_date,
	)


def validate_salary_slip(doc, method=None):
	assert_period_open(
		doc.company,
		doc.start_date,
		_("create or change Salary Slip"),
		doc.end_date,
	)


def validate_additional_salary(doc, method=None):
	start = doc.get("payroll_date") or doc.get("from_date")
	end = doc.get("to_date") or start
	assert_period_open(doc.company, start, _("create or change Additional Salary"), end)


def validate_timesheet(doc, method=None):
	company = doc.get("company")
	for row in doc.get("time_logs") or []:
		start = row.get("from_time")
		end = row.get("to_time") or start
		assert_period_open(company, start, _("create or change Timesheet"), end)
