"""Employee asset custody helpers and employee-scoped permissions."""

from __future__ import annotations

import frappe
from frappe.utils import nowdate


def assignment_query(user):
	return _employee_query("QD Employee Asset Assignment", user)


def loss_damage_query(user):
	return _employee_query("QD Asset Loss Damage Case", user)


def recovery_query(user):
	return _employee_query("QD Asset Recovery", user)


def _employee_query(doctype, user):
	from qd_hrms.self_service import get_session_employee, is_privileged

	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	return f"`tab{doctype}`.`employee` = {frappe.db.escape(employee)}"


def has_employee_asset_permission(doc, ptype=None, user=None, debug=False):
	from qd_hrms.self_service import get_session_employee, is_privileged

	user = user or frappe.session.user
	if is_privileged(user):
		return None
	return doc.get("employee") == get_session_employee(user)


def mark_overdue_assignments():
	"""Mark active assignments overdue after their expected return date."""
	frappe.db.sql(
		"""
		UPDATE `tabQD Employee Asset Assignment`
		SET status = 'Overdue'
		WHERE docstatus = 1
		  AND status = 'Assigned'
		  AND expected_return IS NOT NULL
		  AND expected_return < %s
		""",
		nowdate(),
	)
