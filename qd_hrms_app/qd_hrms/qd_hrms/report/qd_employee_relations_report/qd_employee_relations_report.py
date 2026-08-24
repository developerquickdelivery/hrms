import frappe
from qd_hrms.report_utils import (
	ER_REPORT_ROLES,
	assert_report_roles,
	col,
	date_between,
	employee_columns,
)

def execute(filters=None):
	assert_report_roles(ER_REPORT_ROLES)
	filters = filters or {}
	if not frappe.db.exists("DocType", "QD HR Case"):
		return [col("Info", "info")], [{"info": "Employee Relations cases are not installed"}]
	columns = employee_columns() + [
		col("HR Case", "name", "Link", "QD HR Case", 140),
		col("Case Type", "case_type", width=130),
		col("Subject", "subject", width=200),
		col("Priority", "priority", width=100),
		col("Status", "case_status", width=130),
		col("Opened On", "opened_on", "Date", width=110),
		col("Decision", "decision_type", width=140),
	]
	conds = {}
	conds.update(date_between(filters, "opened_on"))
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("department"):
		conds["department"] = filters.get("department")
	data = frappe.get_all(
		"QD HR Case",
		fields=[
			"name", "employee", "employee_name", "department", "company", "case_type",
			"subject", "priority", "case_status", "opened_on", "decision_type",
		],
		filters=conds,
		order_by="opened_on desc",
	)
	for row in data:
		row.setdefault("designation", None)
	return columns, data

