"""Validation for the customized standard Employee Grade."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


def validate_employee_grade(doc, method=None):
	minimum = flt(doc.get("custom_qd_minimum_base_pay"))
	midpoint = flt(doc.get("custom_qd_midpoint_base_pay"))
	maximum = flt(doc.get("custom_qd_maximum_base_pay"))
	default = flt(doc.get("default_base_pay"))

	if minimum and maximum and minimum > maximum:
		frappe.throw(_("Minimum Base Pay cannot exceed Maximum Base Pay."))
	if midpoint and minimum and midpoint < minimum:
		frappe.throw(_("Midpoint Base Pay cannot be below Minimum Base Pay."))
	if midpoint and maximum and midpoint > maximum:
		frappe.throw(_("Midpoint Base Pay cannot exceed Maximum Base Pay."))
	if default and minimum and default < minimum:
		frappe.throw(_("Default Base Pay cannot be below Minimum Base Pay."))
	if default and maximum and default > maximum:
		frappe.throw(_("Default Base Pay cannot exceed Maximum Base Pay."))

