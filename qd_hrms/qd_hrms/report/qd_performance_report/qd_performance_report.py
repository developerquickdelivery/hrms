import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	columns = employee_columns() + [
		col("Appraisal", "name", "Link", "Appraisal", 140),
		col("Appraisal Cycle", "appraisal_cycle", "Link", "Appraisal Cycle", 150),
		col("Final Score", "final_score", "Float", width=110),
		col("Avg Goal Score", "avg_goal_score", "Float", width=120),
		col("Status", "status", width=120),
		col("Docstatus", "docstatus", "Int", width=90),
	]
	conds = {}
	if filters.get("company"):
		conds["company"] = filters.get("company")
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("department"):
		conds["department"] = filters.get("department")
	meta = frappe.get_meta("Appraisal")
	fields = ["name", "employee", "employee_name", "company", "department", "designation", "docstatus"]
	for field in ("appraisal_cycle", "final_score", "avg_goal_score", "status", "custom_qd_review_status"):
		if meta.has_field(field):
			fields.append(field)
	data = frappe.get_all("Appraisal", fields=fields, filters=conds, order_by="modified desc")
	for row in data:
		if not row.get("status") and row.get("custom_qd_review_status"):
			row["status"] = row.get("custom_qd_review_status")
	return columns, data

