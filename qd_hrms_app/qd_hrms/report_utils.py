"""Shared helpers for QD HR Script Reports."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate


def company_filter(filters, fieldname="company"):
	value = filters.get("company") if filters else None
	return {fieldname: value} if value else {}


def date_between(filters, field, from_key="from_date", to_key="to_date"):
	conditions = {}
	if not filters:
		return conditions
	from_date = filters.get(from_key)
	to_date = filters.get(to_key)
	if from_date and to_date:
		conditions[field] = ["between", [getdate(from_date), getdate(to_date)]]
	elif from_date:
		conditions[field] = [">=", getdate(from_date)]
	elif to_date:
		conditions[field] = ["<=", getdate(to_date)]
	return conditions


def standard_filters(filters=None):
	"""Common company / department / employee filters."""
	out = {}
	if not filters:
		return out
	for key in ("company", "department", "employee", "branch", "designation"):
		if filters.get(key):
			out[key] = filters.get(key)
	return out


def col(label, fieldname, fieldtype="Data", options=None, width=120):
	column = {
		"label": _(label),
		"fieldname": fieldname,
		"fieldtype": fieldtype,
		"width": width,
	}
	if options:
		column["options"] = options
	return column


def employee_columns():
	return [
		col("Employee", "employee", "Link", "Employee", 120),
		col("Employee Name", "employee_name", "Data", width=160),
		col("Department", "department", "Link", "Department", 140),
		col("Designation", "designation", "Link", "Designation", 140),
		col("Company", "company", "Link", "Company", 140),
	]


HR_REPORT_ROLES = frozenset({"System Manager", "HR Manager", "HR User"})
PAYROLL_REPORT_ROLES = frozenset({"System Manager", "HR Manager", "Payroll Manager"})
PERFORMANCE_REPORT_ROLES = frozenset({"System Manager", "HR Manager", "HR User", "Leave Approver"})
ER_REPORT_ROLES = frozenset({"System Manager", "HR Manager", "HR User"})


def assert_report_roles(*role_sets):
	"""Restrict script reports to explicit role groups."""
	if frappe.session.user == "Administrator":
		return
	roles = set(frappe.get_roles())
	if "System Manager" in roles:
		return
	allowed = set().union(*role_sets)
	if not roles.intersection(allowed):
		frappe.throw(_("Not permitted to run this report."), frappe.PermissionError)


def permitted_employees(filters=None):
	"""Return employee names the current user may see in reports."""
	filters = filters or {}
	if frappe.session.user == "Administrator" or set(frappe.get_roles()) & {
		"System Manager",
		"HR Manager",
		"HR User",
		"Payroll Manager",
	}:
		return None
	from qd_hrms.self_service import get_session_employee

	employee = get_session_employee()
	return [employee] if employee else []


def employee_filter(filters=None):
	"""Merge report filters with the current user's employee scope."""
	filters = dict(filters or {})
	allowed = permitted_employees(filters)
	if allowed is None:
		return filters
	if not allowed:
		filters["employee"] = "__none__"
	elif filters.get("employee") and filters["employee"] not in allowed:
		filters["employee"] = "__none__"
	elif not filters.get("employee"):
		filters["employee"] = allowed[0]
	return filters


def default_js_filters():
	return """
frappe.query_reports["{name}"] = {{
	filters: [
		{{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		}},
		{{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
		}},
		{{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		}},
		{{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		}},
	],
}};
"""
