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
