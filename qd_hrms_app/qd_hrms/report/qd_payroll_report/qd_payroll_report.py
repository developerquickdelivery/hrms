import frappe
from qd_hrms.report_utils import PAYROLL_REPORT_ROLES, assert_report_roles, col, date_between

def execute(filters=None):
	assert_report_roles(PAYROLL_REPORT_ROLES)
	filters = filters or {}
	columns = [
		col("Payroll Entry", "name", "Link", "Payroll Entry", 160),
		col("Company", "company", "Link", "Company", 140),
		col("Posting Date", "posting_date", "Date", width=110),
		col("Start Date", "start_date", "Date", width=110),
		col("End Date", "end_date", "Date", width=110),
		col("Employees", "number_of_employees", "Int", width=100),
		col("Status", "status", width=110),
		col("Docstatus", "docstatus", "Int", width=90),
	]
	conds = {}
	conds.update(date_between(filters, "posting_date"))
	if filters.get("company"):
		conds["company"] = filters.get("company")
	data = frappe.get_all(
		"Payroll Entry",
		fields=[
			"name", "company", "posting_date", "start_date", "end_date",
			"number_of_employees", "status", "docstatus",
		],
		filters=conds,
		order_by="posting_date desc",
	)
	return columns, data

