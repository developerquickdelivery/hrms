import frappe
from frappe.utils import date_diff, today
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	if not frappe.db.exists("DocType", "QD Training Certification"):
		return [col("Info", "info")], [{"info": "Training Certification is not installed"}]
	columns = employee_columns() + [
		col("Certification", "name", "Link", "QD Training Certification", 150),
		col("Course", "course", "Link", "QD Training Course", 160),
		col("Issue Date", "issue_date", "Date", width=110),
		col("Expiry Date", "expiry_date", "Date", width=110),
		col("Days to Expiry", "days_to_expiry", "Int", width=120),
		col("Status", "status", width=100),
	]
	conds = {}
	conds.update(date_between(filters, "expiry_date"))
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("status"):
		conds["status"] = filters.get("status")
	data = frappe.get_all(
		"QD Training Certification",
		fields=[
			"name", "employee", "employee_name", "department", "company", "course",
			"issue_date", "expiry_date", "days_to_expiry", "status",
		],
		filters=conds,
		order_by="expiry_date asc",
	)
	for row in data:
		row.setdefault("designation", None)
		if row.get("expiry_date") is not None and row.get("days_to_expiry") is None:
			row["days_to_expiry"] = date_diff(row.expiry_date, today())
	return columns, data

