import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	# Prefer Employee Benefit Application; fall back to Additional Salary benefit-like rows
	if frappe.db.exists("DocType", "Employee Benefit Application"):
		columns = employee_columns() + [
			col("Benefit Application", "name", "Link", "Employee Benefit Application", 170),
			col("Payroll Period", "payroll_period", "Link", "Payroll Period", 140),
			col("Max Benefit Amount", "max_benefits", "Currency", width=140),
			col("Remaining Benefit", "remaining_benefit", "Currency", width=140),
			col("Docstatus", "docstatus", "Int", width=90),
		]
		conds = {}
		if filters.get("employee"):
			conds["employee"] = filters.get("employee")
		if filters.get("company"):
			conds["company"] = filters.get("company")
		fields = ["name", "employee", "employee_name", "company", "docstatus"]
		meta = frappe.get_meta("Employee Benefit Application")
		for field in ("payroll_period", "max_benefits", "remaining_benefit", "department"):
			if meta.has_field(field):
				fields.append(field)
		data = frappe.get_all("Employee Benefit Application", fields=fields, filters=conds, order_by="modified desc")
		for row in data:
			row.setdefault("designation", None)
			row.setdefault("department", None)
		return columns, data

	columns = employee_columns() + [
		col("Additional Salary", "name", "Link", "Additional Salary", 150),
		col("Salary Component", "salary_component", "Link", "Salary Component", 150),
		col("Amount", "amount", "Currency", width=120),
		col("Payroll Date", "payroll_date", "Date", width=110),
		col("Docstatus", "docstatus", "Int", width=90),
	]
	conds = {"docstatus": ["<", 2]}
	conds.update(date_between(filters, "payroll_date"))
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("company"):
		conds["company"] = filters.get("company")
	data = frappe.get_all(
		"Additional Salary",
		fields=["name", "employee", "employee_name", "company", "salary_component", "amount", "payroll_date", "docstatus"],
		filters=conds,
		order_by="payroll_date desc",
	)
	for row in data:
		row.setdefault("department", None)
		row.setdefault("designation", None)
	return columns, data

