import frappe
from qd_hrms.report_utils import (
	PAYROLL_REPORT_ROLES,
	assert_report_roles,
	col,
	date_between,
	employee_columns,
	employee_filter,
)

def execute(filters=None):
	assert_report_roles(PAYROLL_REPORT_ROLES)
	filters = employee_filter(filters or {})
	columns = employee_columns() + [
		col("Salary Slip", "name", "Link", "Salary Slip", 150),
		col("Start Date", "start_date", "Date", width=110),
		col("End Date", "end_date", "Date", width=110),
		col("Gross Pay", "gross_pay", "Currency", width=120),
		col("Total Deduction", "total_deduction", "Currency", width=120),
		col("Net Pay", "net_pay", "Currency", width=120),
		col("Status", "status", width=100),
	]
	conds = {"docstatus": 1}
	conds.update(date_between(filters, "start_date"))
	if filters.get("company"):
		conds["company"] = filters.get("company")
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("department"):
		conds["department"] = filters.get("department")
	if filters.get("employee") == "__none__":
		return columns, []
	data = frappe.get_all(
		"Salary Slip",
		fields=[
			"name", "employee", "employee_name", "department", "designation", "company",
			"start_date", "end_date", "gross_pay", "total_deduction", "net_pay", "status",
		],
		filters=conds,
		order_by="start_date desc",
	)
	return columns, data

