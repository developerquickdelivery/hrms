"""HR executive metrics for ERPNext Number Cards (no custom reporting engine)."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, flt, get_first_day, get_last_day, getdate, today


def _company_filter(company=None):
	return {"company": company} if company else {}


def _ytd_bounds():
	today_date = getdate(today())
	return getdate(f"{today_date.year}-01-01"), today_date


def _month_bounds():
	today_date = getdate(today())
	return get_first_day(today_date), get_last_day(today_date)


def _card(value, fieldtype="Int"):
	return {"value": flt(value), "fieldtype": fieldtype}


@frappe.whitelist()
def total_employees():
	frappe.has_permission("Employee", throw=True)
	return _card(frappe.db.count("Employee", {"status": "Active"}))


@frappe.whitelist()
def new_hires_ytd():
	frappe.has_permission("Employee", throw=True)
	start, end = _ytd_bounds()
	return _card(
		frappe.db.count(
			"Employee",
			{"date_of_joining": ["between", [start, end]]},
		)
	)


@frappe.whitelist()
def exits_ytd():
	frappe.has_permission("Employee", throw=True)
	start, end = _ytd_bounds()
	return _card(
		frappe.db.count(
			"Employee",
			{"relieving_date": ["between", [start, end]]},
		)
	)


@frappe.whitelist()
def turnover_ytd():
	frappe.has_permission("Employee", throw=True)
	start, end = _ytd_bounds()
	active = frappe.db.count("Employee", {"status": "Active"}) or 0
	exits = frappe.db.count("Employee", {"relieving_date": ["between", [start, end]]}) or 0
	opening = active + exits
	return _card((exits / opening * 100.0) if opening else 0, "Percent")


@frappe.whitelist()
def open_vacancies():
	frappe.has_permission("Job Opening", throw=True)
	return _card(frappe.db.count("Job Opening", {"status": "Open"}))


@frappe.whitelist()
def attendance_present_mtd():
	frappe.has_permission("Attendance", throw=True)
	start, end = _month_bounds()
	return _card(
		frappe.db.count(
			"Attendance",
			{
				"attendance_date": ["between", [start, end]],
				"status": "Present",
				"docstatus": 1,
			},
		)
	)


@frappe.whitelist()
def attendance_absent_mtd():
	frappe.has_permission("Attendance", throw=True)
	start, end = _month_bounds()
	return _card(
		frappe.db.count(
			"Attendance",
			{
				"attendance_date": ["between", [start, end]],
				"status": "Absent",
				"docstatus": 1,
			},
		)
	)


@frappe.whitelist()
def leave_applications_mtd():
	frappe.has_permission("Leave Application", throw=True)
	start, end = _month_bounds()
	return _card(
		frappe.db.count(
			"Leave Application",
			{
				"from_date": ["<=", end],
				"to_date": [">=", start],
				"status": "Approved",
				"docstatus": 1,
			},
		)
	)


@frappe.whitelist()
def payroll_entries_mtd():
	frappe.has_permission("Salary Slip", throw=True)
	start, end = _month_bounds()
	return _card(
		frappe.db.count(
			"Salary Slip",
			{
				"start_date": ["<=", end],
				"end_date": [">=", start],
				"docstatus": 1,
			},
		)
	)


@frappe.whitelist()
def training_enrollments_ytd():
	doctype = (
		"QD Training Enrollment"
		if frappe.db.exists("DocType", "QD Training Enrollment")
		else "Training Event"
	)
	frappe.has_permission(doctype, throw=True)
	start, end = _ytd_bounds()
	if doctype == "QD Training Enrollment":
		return _card(
			frappe.db.count(
				doctype,
				{"enrollment_date": ["between", [start, end]]},
			)
		)
	return _card(
		frappe.db.count(
			doctype,
			{"start_time": ["between", [start, end]], "docstatus": ["<", 2]},
		)
	)


@frappe.whitelist()
def performance_appraisals_open():
	frappe.has_permission("Appraisal", throw=True)
	return _card(frappe.db.count("Appraisal", {"docstatus": 0}))


@frappe.whitelist()
def expiring_documents_30d():
	frappe.has_permission("QD Employee Document", throw=True)
	end = add_days(today(), 30)
	return _card(
		frappe.db.count(
			"QD Employee Document",
			{"expiry_date": ["between", [today(), end]]},
		)
	)


@frappe.whitelist()
def probation_expiry_30d():
	frappe.has_permission("Employee", throw=True)
	end = add_days(today(), 30)
	filters = {
		"status": "Active",
		"custom_qd_probation_end": ["between", [today(), end]],
	}
	if not frappe.get_meta("Employee").has_field("custom_qd_probation_end"):
		return _card(0)
	return _card(frappe.db.count("Employee", filters))


@frappe.whitelist()
def contract_expiry_30d():
	frappe.has_permission("Employee", throw=True)
	end = add_days(today(), 30)
	return _card(
		frappe.db.count(
			"Employee",
			{
				"status": "Active",
				"contract_end_date": ["between", [today(), end]],
			},
		)
	)
