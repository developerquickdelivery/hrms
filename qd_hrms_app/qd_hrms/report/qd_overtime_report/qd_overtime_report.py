import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	ref = "Overtime Request" if frappe.db.exists("DocType", "Overtime Request") else None
	if not ref:
		return [col("Info", "info")], [{"info": "Overtime Request DocType is not available"}]
	columns = employee_columns() + [
		col("Request", "name", "Link", "Overtime Request", 140),
		col("From", "from_date", "Date", width=110),
		col("To", "to_date", "Date", width=110),
		col("Hours", "overtime_hours", "Float", width=100),
		col("Status", "workflow_state", width=120),
		col("Docstatus", "docstatus", "Int", width=90),
	]
	meta = frappe.get_meta("Overtime Request")
	fields = ["name", "employee", "employee_name", "department", "company", "docstatus"]
	for candidate in ("from_date", "to_date", "overtime_hours", "workflow_state", "status", "hours"):
		if meta.has_field(candidate):
			fields.append(candidate)
	conds = {}
	date_field = "from_date" if meta.has_field("from_date") else "creation"
	conds.update(date_between(filters, date_field))
	if filters.get("company") and meta.has_field("company"):
		conds["company"] = filters.get("company")
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	data = frappe.get_all("Overtime Request", fields=fields, filters=conds, order_by="modified desc")
	for row in data:
		if "overtime_hours" not in row and row.get("hours") is not None:
			row["overtime_hours"] = row.get("hours")
		if "workflow_state" not in row:
			row["workflow_state"] = row.get("status")
		row.setdefault("designation", None)
	return columns, data

