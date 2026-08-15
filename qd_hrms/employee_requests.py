"""Employee Request permission scoping."""

from __future__ import annotations

import frappe


def employee_request_query(user):
	from qd_hrms.self_service import get_session_employee, is_privileged

	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	conditions = [f"`tabQD Employee Request`.`approver` = {frappe.db.escape(user)}"]
	if employee:
		conditions.append(
			f"`tabQD Employee Request`.`employee` = {frappe.db.escape(employee)}"
		)
	return "(" + " or ".join(conditions) + ")"


def has_employee_request_permission(doc, ptype=None, user=None, debug=False):
	from qd_hrms.self_service import get_session_employee, is_privileged

	user = user or frappe.session.user
	if is_privileged(user):
		return None
	if doc.get("approver") == user:
		return True
	return doc.get("employee") == get_session_employee(user)
