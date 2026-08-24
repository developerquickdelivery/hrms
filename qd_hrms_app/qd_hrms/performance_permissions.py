"""Record-level access for sensitive performance documents."""

from __future__ import annotations

import frappe

from qd_hrms.self_service import get_session_employee, is_privileged


def _employee_field_query(doctype: str, user: str | None = None) -> str:
	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	return f"`tab{doctype}`.employee = {frappe.db.escape(employee)}"


def pip_query(user):
	return _employee_field_query("QD Performance Improvement Plan", user)


def recognition_query(user):
	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	escaped = frappe.db.escape(employee)
	return (
		f"(`tabQD Recognition Award`.employee = {escaped} "
		f"OR (`tabQD Recognition Award`.visibility != 'Private' "
		f"AND `tabQD Recognition Award`.docstatus = 1))"
	)


def _manager_of_employee(employee: str | None, user: str | None = None) -> bool:
	if not employee:
		return False
	user = user or frappe.session.user
	manager_user = frappe.db.get_value(
		"Employee",
		frappe.db.get_value("Employee", employee, "reports_to"),
		"user_id",
	)
	return bool(manager_user and manager_user == user)


def has_pip_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	user = user or frappe.session.user
	employee = get_session_employee(user)
	if not employee:
		return False
	if doc.employee != employee and not _manager_of_employee(doc.employee, user):
		return False
	if ptype in ("write", "create", "delete", "submit", "cancel", "amend"):
		return False
	return True


def has_recognition_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	user = user or frappe.session.user
	employee = get_session_employee(user)
	if not employee:
		return False
	if doc.employee == employee:
		if ptype == "delete":
			return doc.docstatus == 0 and doc.owner == user
		if ptype in ("write", "submit") and doc.docstatus == 0:
			return doc.owner == user or doc.get("recognized_by") == user
		return True
	if doc.get("visibility") == "Private" or doc.docstatus != 1:
		return False
	if ptype in ("write", "create", "delete", "submit", "cancel", "amend"):
		return False
	return True
