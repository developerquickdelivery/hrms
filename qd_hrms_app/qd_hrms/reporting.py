"""Effective-dated reporting history synchronized to Employee.reports_to."""

from __future__ import annotations

import frappe
from frappe.utils import getdate, nowdate


def assignment_status(effective_from, effective_to=None, on_date=None) -> str:
	on_date = getdate(on_date or nowdate())
	if getdate(effective_from) > on_date:
		return "Scheduled"
	if effective_to and getdate(effective_to) < on_date:
		return "Expired"
	return "Current"


def sync_employee_reports_to(employee: str, clear_manager: str | None = None):
	"""Apply the current assignment to standard Reports To."""
	today = getdate(nowdate())
	current = frappe.db.sql(
		"""
		select primary_manager, acting_manager
		from `tabEmployee Reporting Assignment`
		where employee = %s
			and docstatus = 1
			and effective_from <= %s
			and (effective_to is null or effective_to >= %s)
		order by effective_from desc, creation desc
		limit 1
		""",
		(employee, today, today),
		as_dict=True,
	)
	manager = None
	if current:
		manager = current[0].acting_manager or current[0].primary_manager

	existing = frappe.db.get_value("Employee", employee, "reports_to")
	if manager and manager != existing:
		frappe.db.set_value("Employee", employee, "reports_to", manager)
		_record_manager_history(employee, existing, manager)
	elif not manager and clear_manager and existing == clear_manager:
		frappe.db.set_value("Employee", employee, "reports_to", None)
		_record_manager_history(employee, existing, None)


def _record_manager_history(employee, from_value, to_value):
	from qd_hrms.employment_history import record_event

	record_event(
		employee=employee,
		event_type="Manager Change",
		from_value=from_value,
		to_value=to_value,
		reference_doctype="Employee",
		reference_name=employee,
		remarks="Synced from Employee Reporting Assignment.",
	)


def sync_all_reporting_assignments():
	"""Daily status refresh and effective-date synchronization."""
	today = getdate(nowdate())
	assignments = frappe.get_all(
		"Employee Reporting Assignment",
		filters={"docstatus": 1},
		fields=[
			"name",
			"employee",
			"primary_manager",
			"acting_manager",
			"effective_from",
			"effective_to",
			"status",
		],
		order_by="effective_from asc, creation asc",
	)
	employees = set()
	expired_managers = {}
	for row in assignments:
		status = assignment_status(row.effective_from, row.effective_to, today)
		if row.status != status:
			frappe.db.set_value("Employee Reporting Assignment", row.name, "status", status)
		employees.add(row.employee)
		if status == "Expired":
			expired_managers[row.employee] = row.acting_manager or row.primary_manager

	for employee in employees:
		sync_employee_reports_to(employee, clear_manager=expired_managers.get(employee))

