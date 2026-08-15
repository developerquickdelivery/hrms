"""Ethiopia leave, PAYE, and pension configuration for Quick Delivery."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

COMPANY = "Quick Delivery"
ANNUAL_LEAVE = "Annual Leave"
TAX_SLAB = "Ethiopia Employment Income Tax 2025"

# Income Tax Proclamation (Amendment) No. 1395/2025 monthly bands,
# annualized because HRMS calculates annual taxable earnings.
ANNUAL_PAYE_SLABS = (
	(0, 24_000, 0),
	(24_001, 48_000, 15),
	(48_001, 84_000, 20),
	(84_001, 120_000, 25),
	(120_001, 168_000, 30),
	(168_001, 0, 35),
)

CARRY_FORWARD_FORMULA = (
	"min(unused_leaves, maximum_carry_forwarded_leaves) "
	"if maximum_carry_forwarded_leaves else unused_leaves"
)
ENCASHMENT_DAYS_FORMULA = (
	"min(max(leave_balance - non_encashable_leaves, 0), max_encashable_leaves) "
	"if max_encashable_leaves else max(leave_balance - non_encashable_leaves, 0)"
)
ENCASHMENT_AMOUNT_FORMULA = "encashment_days * daily_rate"


def run():
	ensure_default_company()
	ensure_custom_fields()
	ensure_leave_encashment_component()
	ensure_annual_leave()
	ensure_pension_components()
	ensure_income_tax_component()
	ensure_income_tax_slab()
	frappe.clear_cache()
	return {
		"company": COMPANY,
		"annual_leave": ANNUAL_LEAVE,
		"income_tax_slab": TAX_SLAB,
		"employee_pension": "Employee Pension (7%)",
		"employer_pension": "Employer Pension (11%)",
	}


def ensure_default_company():
	"""Lock Global Defaults to the only legal entity: Quick Delivery."""
	if not frappe.db.exists("Company", COMPANY):
		return
	frappe.db.set_single_value("Global Defaults", "default_company", COMPANY)
	frappe.db.set_default("company", COMPANY)


def ensure_custom_fields():
	create_custom_fields(
		{
			"Leave Type": [
				{
					"fieldname": "custom_qd_formula_section",
					"fieldtype": "Section Break",
					"label": "QD Leave Formulas",
					"insert_after": "non_encashable_leaves",
					"collapsible": 1,
				},
				{
					"fieldname": "custom_qd_carry_forward_formula",
					"fieldtype": "Code",
					"label": "Carry-forward Formula",
					"options": "PythonExpression",
					"insert_after": "custom_qd_formula_section",
					"depends_on": "eval:doc.is_carry_forward",
					"description": (
						"Variables: unused_leaves, new_leaves_allocated, "
						"maximum_carry_forwarded_leaves, max_leaves_allowed, years_of_service."
					),
				},
				{
					"fieldname": "custom_qd_encashment_days_formula",
					"fieldtype": "Code",
					"label": "Encashment Days Formula",
					"options": "PythonExpression",
					"insert_after": "custom_qd_carry_forward_formula",
					"depends_on": "eval:doc.allow_encashment",
					"description": (
						"Variables: leave_balance, actual_encashable_days, "
						"max_encashable_leaves, non_encashable_leaves, years_of_service."
					),
				},
				{
					"fieldname": "custom_qd_formula_col",
					"fieldtype": "Column Break",
					"insert_after": "custom_qd_encashment_days_formula",
				},
				{
					"fieldname": "custom_qd_encashment_amount_formula",
					"fieldtype": "Code",
					"label": "Encashment Amount Formula",
					"options": "PythonExpression",
					"insert_after": "custom_qd_formula_col",
					"depends_on": "eval:doc.allow_encashment",
					"description": "Variables: encashment_days, daily_rate, base, years_of_service.",
				},
				{
					"fieldname": "custom_qd_encashment_only_on_exit",
					"fieldtype": "Check",
					"label": "Encashment Only on Exit",
					"default": "1",
					"insert_after": "custom_qd_encashment_amount_formula",
					"depends_on": "eval:doc.allow_encashment",
					"description": "Required for Ethiopian annual-leave compliance.",
				},
			]
		},
		ignore_validate=True,
		update=True,
	)


def ensure_annual_leave():
	if frappe.db.exists("Leave Type", ANNUAL_LEAVE):
		doc = frappe.get_doc("Leave Type", ANNUAL_LEAVE)
	else:
		doc = frappe.new_doc("Leave Type")
		doc.leave_type_name = ANNUAL_LEAVE

	doc.max_leaves_allowed = 48
	doc.applicable_after = 365
	doc.is_carry_forward = 1
	doc.maximum_carry_forwarded_leaves = 32
	doc.expire_carry_forwarded_leaves_after_days = 730
	doc.allow_encashment = 1
	doc.max_encashable_leaves = 32
	doc.non_encashable_leaves = 0
	doc.earning_component = "Leave Encashment"
	doc.custom_qd_carry_forward_formula = CARRY_FORWARD_FORMULA
	doc.custom_qd_encashment_days_formula = ENCASHMENT_DAYS_FORMULA
	doc.custom_qd_encashment_amount_formula = ENCASHMENT_AMOUNT_FORMULA
	doc.custom_qd_encashment_only_on_exit = 1
	doc.save(ignore_permissions=True)


def ensure_leave_encashment_component():
	_upsert_component(
		"Leave Encashment",
		abbr="LE",
		component_type="Earning",
		is_tax_applicable=1,
		depends_on_payment_days=0,
		description="Exit-only payment for eligible untaken annual leave.",
	)


def ensure_pension_components():
	_upsert_component(
		"Employee Pension (7%)",
		abbr="PEN",
		component_type="Deduction",
		formula="B * 0.07",
		amount_based_on_formula=1,
		exempted_from_income_tax=1,
		depends_on_payment_days=0,
		description="Employee pension: 7% of Basic (B), tax deductible.",
	)
	_upsert_component(
		"Employer Pension (11%)",
		abbr="EPEN",
		component_type="Earning",
		formula="B * 0.11",
		amount_based_on_formula=1,
		statistical_component=1,
		do_not_include_in_total=1,
		do_not_include_in_accounts=1,
		depends_on_payment_days=0,
		description="Employer pension: 11% of Basic (B), tracked as statistical employer cost.",
	)


def ensure_income_tax_component():
	_upsert_component(
		"Income Tax",
		abbr="IT",
		component_type="Deduction",
		variable_based_on_taxable_salary=1,
		is_income_tax_component=1,
		depends_on_payment_days=0,
		description=f"PAYE calculated by HRMS using {TAX_SLAB}.",
	)


def _upsert_component(name, abbr, component_type, **values):
	if frappe.db.exists("Salary Component", name):
		doc = frappe.get_doc("Salary Component", name)
	else:
		doc = frappe.new_doc("Salary Component")
		doc.salary_component = name
	doc.salary_component_abbr = abbr
	doc.type = component_type
	for fieldname, value in values.items():
		if doc.meta.has_field(fieldname):
			doc.set(fieldname, value)
	# Tax components cannot also have a direct formula.
	if values.get("variable_based_on_taxable_salary"):
		doc.amount_based_on_formula = 0
		doc.formula = None
		doc.amount = 0
	doc.save(ignore_permissions=True)
	return doc


def ensure_income_tax_slab():
	if not frappe.db.exists("Company", COMPANY):
		return
	if frappe.db.exists("Income Tax Slab", TAX_SLAB):
		doc = frappe.get_doc("Income Tax Slab", TAX_SLAB)
		if doc.docstatus == 1:
			return
		doc.set("slabs", [])
	else:
		doc = frappe.new_doc("Income Tax Slab")
		doc.name = TAX_SLAB

	doc.company = COMPANY
	doc.currency = frappe.db.get_value("Company", COMPANY, "default_currency") or "ETB"
	doc.effective_from = "2025-07-08"
	doc.standard_tax_exemption_amount = 0
	doc.allow_tax_exemption = 0
	doc.disabled = 0
	for from_amount, to_amount, percent in ANNUAL_PAYE_SLABS:
		doc.append(
			"slabs",
			{
				"from_amount": from_amount,
				"to_amount": to_amount or None,
				"percent_deduction": percent,
			},
		)
	doc.insert(ignore_permissions=True) if doc.is_new() else doc.save(ignore_permissions=True)
	doc.submit()
	frappe.db.commit()
