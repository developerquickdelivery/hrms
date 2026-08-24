"""Quick Delivery defaults and validation for standard HRMS Job Offer."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_months, flt, formatdate, strip_html_tags

STANDARD_TEMPLATE = "QD Standard Offer Terms"


def validate(doc, method=None):
	"""Derive offer details and keep the standard offer-term table synchronized."""
	_apply_position(doc)
	_apply_grade(doc)
	_validate_dates(doc)
	_validate_salary_band(doc)
	_sync_offer_terms(doc)


def _apply_position(doc):
	if not doc.get("custom_qd_position"):
		return

	position = frappe.db.get_value(
		"QD Position",
		doc.custom_qd_position,
		["active", "designation", "employee_grade", "company"],
		as_dict=True,
	)
	if not position:
		frappe.throw(_("Position {0} does not exist.").format(doc.custom_qd_position))
	if not position.active:
		frappe.throw(_("Position {0} is inactive.").format(doc.custom_qd_position))

	if position.designation:
		doc.designation = position.designation
	if position.employee_grade:
		doc.custom_qd_employee_grade = position.employee_grade
	if position.company:
		doc.company = position.company


def _apply_grade(doc):
	if not doc.get("custom_qd_employee_grade"):
		return

	grade = frappe.db.get_value(
		"Employee Grade",
		doc.custom_qd_employee_grade,
		["currency", "default_base_pay"],
		as_dict=True,
	)
	if not grade:
		frappe.throw(_("Employee Grade {0} does not exist.").format(doc.custom_qd_employee_grade))

	if grade.currency and not doc.get("custom_qd_salary_currency"):
		doc.custom_qd_salary_currency = grade.currency
	if grade.default_base_pay and not flt(doc.get("custom_qd_base_salary")):
		doc.custom_qd_base_salary = grade.default_base_pay


def _validate_dates(doc):
	if doc.offer_date and doc.custom_qd_start_date and doc.custom_qd_start_date < doc.offer_date:
		frappe.throw(_("Start Date cannot be before Offer Date."))

	months = int(doc.get("custom_qd_probation_months") or 0)
	if months < 0:
		frappe.throw(_("Probation Period cannot be negative."))
	if doc.custom_qd_start_date and months:
		doc.custom_qd_probation_end_date = add_months(doc.custom_qd_start_date, months)
	else:
		doc.custom_qd_probation_end_date = None


def _validate_salary_band(doc):
	if not doc.get("custom_qd_employee_grade") or not flt(doc.get("custom_qd_base_salary")):
		return

	band = frappe.db.get_value(
		"Employee Grade",
		doc.custom_qd_employee_grade,
		["custom_qd_minimum_base_pay", "custom_qd_maximum_base_pay"],
		as_dict=True,
	)
	if not band:
		return

	salary = flt(doc.custom_qd_base_salary)
	minimum = flt(band.custom_qd_minimum_base_pay)
	maximum = flt(band.custom_qd_maximum_base_pay)
	if minimum and salary < minimum:
		frappe.throw(
			_("Base Salary must be at least {0} for grade {1}.").format(
				_format_money(minimum, doc.custom_qd_salary_currency),
				doc.custom_qd_employee_grade,
			)
		)
	if maximum and salary > maximum:
		frappe.throw(
			_("Base Salary cannot exceed {0} for grade {1}.").format(
				_format_money(maximum, doc.custom_qd_salary_currency),
				doc.custom_qd_employee_grade,
			)
		)


def _sync_offer_terms(doc):
	doc.job_offer_term_template = STANDARD_TEMPLATE
	values = {
		"Position": doc.custom_qd_position or doc.designation,
		"Grade": doc.custom_qd_employee_grade,
		"Salary": _format_money(doc.custom_qd_base_salary, doc.custom_qd_salary_currency),
		"Benefits": _plain_text(doc.custom_qd_benefits),
		"Start Date": formatdate(doc.custom_qd_start_date) if doc.custom_qd_start_date else "",
		"Probation": (
			_("{0} month(s), ending {1}").format(
				doc.custom_qd_probation_months,
				formatdate(doc.custom_qd_probation_end_date),
			)
			if doc.custom_qd_probation_end_date
			else _("No probation period")
		),
		"Conditions": _plain_text(doc.custom_qd_conditions),
	}

	existing = {row.offer_term: row for row in doc.offer_terms}
	for offer_term, value in values.items():
		row = existing.get(offer_term)
		if row:
			row.value = value
		else:
			doc.append("offer_terms", {"offer_term": offer_term, "value": value})


def _plain_text(value):
	return strip_html_tags(value or "").strip()


def _format_money(value, currency):
	if not value:
		return ""
	return frappe.utils.fmt_money(value, currency=currency or None)
