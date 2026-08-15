from qd_hrms.report_utils import col, date_between, employee_columns, standard_filters
import frappe

def execute(filters=None):
	filters = filters or {}
	columns = employee_columns() + [
		col("Status", "status", width=100),
		col("Date of Joining", "date_of_joining", "Date", width=120),
		col("Relieving Date", "relieving_date", "Date", width=120),
		col("Employment Type", "employment_type", "Link", "Employment Type", 130),
		col("Grade", "grade", "Link", "Employee Grade", 120),
		col("Branch", "branch", "Link", "Branch", 120),
		col("Reports To", "reports_to", "Link", "Employee", 120),
	]
	conds = standard_filters(filters)
	conds.update(date_between(filters, "date_of_joining"))
	if filters.get("status"):
		conds["status"] = filters.get("status")
	data = frappe.get_all(
		"Employee",
		fields=[
			"name as employee", "employee_name", "department", "designation", "company",
			"status", "date_of_joining", "relieving_date", "employment_type", "grade",
			"branch", "reports_to",
		],
		filters=conds,
		order_by="date_of_joining desc",
	)
	return columns, data

