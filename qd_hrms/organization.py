"""Organization hierarchy validation for standard ERPNext records."""

from __future__ import annotations

import frappe
from frappe import _


def validate_cost_center(doc, method=None):
	"""Keep optional Cost Center hierarchy links internally consistent."""
	if doc.get("custom_qd_business_unit"):
		unit = frappe.db.get_value(
			"HR Business Unit",
			doc.custom_qd_business_unit,
			["company", "branch"],
			as_dict=True,
		)
		if unit:
			if unit.company and doc.company != unit.company:
				frappe.throw(_("Business Unit must belong to Cost Center company {0}.").format(doc.company))
			if unit.branch and doc.get("custom_qd_branch") and doc.custom_qd_branch != unit.branch:
				frappe.throw(_("Business Unit must belong to the selected Branch."))

	if doc.get("custom_qd_department"):
		department = frappe.db.get_value(
			"Department",
			doc.custom_qd_department,
			["company", "custom_qd_business_unit"],
			as_dict=True,
		)
		if department:
			if department.company and doc.company != department.company:
				frappe.throw(_("Department must belong to Cost Center company {0}.").format(doc.company))
			if (
				department.custom_qd_business_unit
				and doc.get("custom_qd_business_unit")
				and department.custom_qd_business_unit != doc.custom_qd_business_unit
			):
				frappe.throw(_("Department must belong to the selected Business Unit."))

