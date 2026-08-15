import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	columns = employee_columns() + [
		col("Leave Type", "leave_type", "Link", "Leave Type", 130),
		col("From Date", "from_date", "Date", width=110),
		col("To Date", "to_date", "Date", width=110),
		col("Total Leave Days", "total_leave_days", "Float", width=120),
		col("Status", "status", width=100),
		col("Leave Application", "name", "Link", "Leave Application", 150),
	]
	conds = {"docstatus": ["<", 2]}
	conds.update(date_between(filters, "from_date"))
	if filters.get("company"):
		conds["company"] = filters.get("company")
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("department"):
		conds["department"] = filters.get("department")
	data = frappe.get_all(
		"Leave Application",
		fields=[
			"name", "employee", "employee_name", "department", "company", "leave_type",
			"from_date", "to_date", "total_leave_days", "status",
		],
		filters=conds,
		order_by="from_date desc",
	)
	for row in data:
		row.setdefault("designation", None)
	return columns, data

