import frappe
from frappe.utils import date_diff, today

from qd_hrms.report_utils import assert_report_roles, col, date_between, employee_columns, HR_REPORT_ROLES


def execute(filters=None):
	assert_report_roles(HR_REPORT_ROLES)
	filters = filters or {}
	if not frappe.db.exists("DocType", "QD Employee License"):
		return [col("Info", "info")], [{"info": "Employee License is not installed"}]
	columns = employee_columns() + [
		col("License", "name", "Link", "QD Employee License", 140),
		col("Type", "license_type", "Link", "QD License Type", 160),
		col("Category", "category", width=110),
		col("Expiry Date", "expiry_date", "Date", width=110),
		col("Days to Expiry", "days_to_expiry", "Int", width=120),
		col("Status", "status", width=140),
		col("Required", "required_for_work", "Check", width=90),
		col("Auto Renew", "auto_renew", "Check", width=100),
		col("Renewal Request", "renewal_request", "Link", "QD Employee Request", 150),
	]
	conds = {}
	conds.update(date_between(filters, "expiry_date"))
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("status"):
		conds["status"] = filters.get("status")
	if filters.get("license_type"):
		conds["license_type"] = filters.get("license_type")
	if filters.get("company"):
		conds["company"] = filters.get("company")
	if filters.get("department"):
		conds["department"] = filters.get("department")
	data = frappe.get_all(
		"QD Employee License",
		fields=[
			"name",
			"employee",
			"employee_name",
			"department",
			"company",
			"license_type",
			"category",
			"expiry_date",
			"days_to_expiry",
			"status",
			"required_for_work",
			"auto_renew",
			"renewal_request",
		],
		filters=conds,
		order_by="expiry_date asc",
	)
	for row in data:
		row.setdefault("designation", None)
		if row.get("expiry_date") is not None and row.get("days_to_expiry") is None:
			row["days_to_expiry"] = date_diff(row.expiry_date, today())
	return columns, data
