"""Safe Python-expression rules for leave carry-forward and encashment."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate
from hrms.payroll.utils import sanitize_expression

SAFE_GLOBALS = {
	"min": min,
	"max": max,
	"round": round,
	"abs": abs,
}


def set_default_tax_slab(doc, method=None):
	"""Single-company site: always default the Ethiopia PAYE slab when blank."""
	if doc.income_tax_slab:
		return
	if frappe.db.exists("Income Tax Slab", "Ethiopia Employment Income Tax 2025"):
		doc.income_tax_slab = "Ethiopia Employment Income Tax 2025"
		if not doc.company:
			doc.company = "Quick Delivery"


def evaluate(expression: str, values: dict) -> float:
	expression = sanitize_expression(expression)
	if not expression:
		return 0
	try:
		return flt(frappe.safe_eval(expression, SAFE_GLOBALS.copy(), values))
	except Exception as exc:
		frappe.throw(
			_("Invalid QD leave formula: {0}").format(frappe.bold(str(exc))),
			title=_("Formula Error"),
		)


def validate_leave_type(doc, method=None):
	"""Validate expressions when HR saves Leave Type."""
	samples = {
		"unused_leaves": 20.0,
		"leave_balance": 20.0,
		"maximum_carry_forwarded_leaves": flt(doc.maximum_carry_forwarded_leaves),
		"max_encashable_leaves": flt(doc.max_encashable_leaves),
		"non_encashable_leaves": flt(doc.non_encashable_leaves),
		"encashment_days": 10.0,
		"daily_rate": 100.0,
		"base": 2600.0,
		"years_of_service": 3.0,
	}
	for fieldname in (
		"custom_qd_carry_forward_formula",
		"custom_qd_encashment_days_formula",
		"custom_qd_encashment_amount_formula",
	):
		expression = doc.get(fieldname)
		if expression:
			evaluate(expression, samples)


def apply_carry_forward_formula(doc, method=None):
	"""Run after core Leave Allocation has calculated unused leaves."""
	if not doc.carry_forward or not doc.leave_type:
		return
	leave_type = frappe.get_cached_doc("Leave Type", doc.leave_type)
	expression = leave_type.get("custom_qd_carry_forward_formula")
	if not expression:
		return

	years = _years_of_service(doc.employee, doc.from_date)
	values = {
		"unused_leaves": flt(doc.unused_leaves),
		"new_leaves_allocated": flt(doc.new_leaves_allocated),
		"total_leaves_allocated": flt(doc.total_leaves_allocated),
		"maximum_carry_forwarded_leaves": flt(leave_type.maximum_carry_forwarded_leaves),
		"max_leaves_allowed": flt(leave_type.max_leaves_allowed),
		"years_of_service": years,
	}
	allowed = max(evaluate(expression, values), 0)
	# A custom expression may reduce carry-forward, never create leave.
	doc.unused_leaves = min(allowed, max(flt(doc.unused_leaves), 0))
	doc.total_leaves_allocated = flt(doc.new_leaves_allocated) + flt(doc.unused_leaves)
	if leave_type.max_leaves_allowed:
		doc.total_leaves_allocated = min(doc.total_leaves_allocated, leave_type.max_leaves_allowed)
		doc.unused_leaves = max(doc.total_leaves_allocated - flt(doc.new_leaves_allocated), 0)


def apply_encashment_formula(doc, method=None):
	"""Apply configured exit-only encashment days and amount after core validation."""
	if not doc.employee or not doc.leave_type:
		return
	leave_type = frappe.get_cached_doc("Leave Type", doc.leave_type)

	if leave_type.get("custom_qd_encashment_only_on_exit"):
		status = frappe.db.get_value("Employee", doc.employee, "status")
		if status != "Left":
			frappe.throw(
				_(
					"Annual leave cannot be encashed while the employee is active. "
					"Use Leave Encashment after the Employee status is set to Left."
				),
				title=_("Exit-only Leave Encashment"),
			)

	years = _years_of_service(doc.employee, doc.encashment_date)
	daily_rate = flt(doc.encashment_amount) / flt(doc.encashment_days) if doc.encashment_days else 0
	days_formula = leave_type.get("custom_qd_encashment_days_formula")
	if days_formula:
		values = {
			"leave_balance": flt(doc.leave_balance),
			"actual_encashable_days": flt(doc.actual_encashable_days),
			"encashment_days": flt(doc.encashment_days),
			"max_encashable_leaves": flt(leave_type.max_encashable_leaves),
			"non_encashable_leaves": flt(leave_type.non_encashable_leaves),
			"years_of_service": years,
		}
		calculated_days = max(evaluate(days_formula, values), 0)
		doc.actual_encashable_days = min(calculated_days, flt(doc.leave_balance))
		doc.encashment_days = min(
			flt(doc.encashment_days) if doc.encashment_days else calculated_days,
			doc.actual_encashable_days,
		)

	amount_formula = leave_type.get("custom_qd_encashment_amount_formula")
	if amount_formula:
		if not daily_rate:
			daily_rate = _get_daily_rate(doc)
		doc.encashment_amount = evaluate(
			amount_formula,
			{
				"leave_balance": flt(doc.leave_balance),
				"encashment_days": flt(doc.encashment_days),
				"daily_rate": daily_rate,
				"base": _get_base(doc.employee, doc.encashment_date),
				"years_of_service": years,
			},
		)


def _years_of_service(employee: str, on_date) -> float:
	date_of_joining = frappe.db.get_value("Employee", employee, "date_of_joining")
	if not date_of_joining or not on_date:
		return 0
	return max((getdate(on_date) - getdate(date_of_joining)).days / 365.25, 0)


def _get_base(employee: str, on_date) -> float:
	return flt(
		frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": employee, "docstatus": 1, "from_date": ("<=", on_date)},
			"base",
			order_by="from_date desc",
		)
	)


def _get_daily_rate(doc) -> float:
	rate = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": doc.employee, "docstatus": 1, "from_date": ("<=", doc.encashment_date)},
		"leave_encashment_amount_per_day",
		order_by="from_date desc",
	)
	return flt(rate) or (_get_base(doc.employee, doc.encashment_date) / 26)
