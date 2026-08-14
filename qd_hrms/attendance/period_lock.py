"""Block attendance changes in a submitted (locked) period unless the user may override."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

OVERRIDE_ROLES = ("System Manager", "HR Manager")


def user_can_override() -> bool:
	if frappe.session.user in ("Administrator", "Guest"):
		# Guest never overrides; Administrator always does.
		return frappe.session.user == "Administrator"
	return bool(set(frappe.get_roles()) & set(OVERRIDE_ROLES))


def get_lock(company: str, date) -> str | None:
	if not company or not date:
		return None
	day = getdate(date)
	return frappe.db.exists(
		"QD Attendance Period Lock",
		{
			"company": company,
			"docstatus": 1,
			"from_date": ("<=", day),
			"to_date": (">=", day),
		},
	)


def assert_period_open(company: str, date, action: str = "change attendance"):
	if frappe.flags.get("qd_ignore_period_lock"):
		return
	lock = get_lock(company, date)
	if not lock:
		return
	if user_can_override():
		return
	frappe.throw(
		_(
			"Attendance period is locked ({0}). {1} is not allowed. "
			"HR Manager can unlock the period or post the exception."
		).format(lock, action),
		title=_("Period Locked"),
	)


def validate_attendance(doc, method=None):
	assert_period_open(doc.company, doc.attendance_date, _("submit or change Attendance"))


def validate_attendance_request(doc, method=None):
	if not doc.from_date or not doc.to_date:
		return
	day = getdate(doc.from_date)
	end = getdate(doc.to_date)
	while day <= end:
		assert_period_open(doc.company, day, _("submit an Attendance Request"))
		day = frappe.utils.add_days(day, 1)


def validate_checkin(doc, method=None):
	company = None
	if doc.employee:
		company = frappe.db.get_value("Employee", doc.employee, "company")
	stamp = doc.time or frappe.utils.now_datetime()
	assert_period_open(company, stamp, _("record Employee Checkin"))
