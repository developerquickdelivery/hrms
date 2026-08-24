"""Employee Relations case management: permission scoping for intake records.

QD HR Case and QD Disciplinary Case are HR-only (no Employee role permission).
QD Grievance and QD Complaint can be raised by employees, but each employee may
only see the records they raised or that concern them.
"""

from __future__ import annotations

import frappe


def grievance_query(user):
	return _own_record_query("QD Grievance", user)


def complaint_query(user):
	return _own_record_query("QD Complaint", user)


def _own_record_query(doctype, user):
	from qd_hrms.self_service import get_session_employee, is_privileged

	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	conditions = [f"`tab{doctype}`.`owner` = {frappe.db.escape(user)}"]
	if employee:
		conditions.append(f"`tab{doctype}`.`employee` = {frappe.db.escape(employee)}")
	return "(" + " or ".join(conditions) + ")"


def has_er_record_permission(doc, ptype=None, user=None, debug=False):
	from qd_hrms.self_service import get_session_employee, is_privileged

	user = user or frappe.session.user
	if is_privileged(user):
		return None
	if doc.get("owner") == user:
		return True
	return doc.get("employee") == get_session_employee(user)
