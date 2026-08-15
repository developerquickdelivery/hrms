import frappe
from frappe.utils import add_days, getdate, today
from qd_hrms.report_utils import col, employee_columns, standard_filters

def execute(filters=None):
	filters = filters or {}
	columns = [
		col("Compliance Item", "item", width=180),
		col("Reference", "reference", "Data", width=160),
		col("Type", "reference_doctype", "Data", width=140),
		col("Employee", "employee", "Link", "Employee", 120),
		col("Employee Name", "employee_name", width=150),
		col("Due / Expiry", "due_date", "Date", width=120),
		col("Days Remaining", "days_remaining", "Int", width=120),
		col("Status", "status", width=110),
	]
	horizon = add_days(today(), int(filters.get("days") or 60))
	data = []
	# Probation
	if frappe.get_meta("Employee").has_field("custom_qd_probation_end"):
		for row in frappe.get_all(
			"Employee",
			fields=["name", "employee_name", "custom_qd_probation_end", "status"],
			filters={
				"status": "Active",
				"custom_qd_probation_end": ["between", [today(), horizon]],
				**standard_filters(filters),
			},
		):
			data.append({
				"item": "Probation Expiry",
				"reference": row.name,
				"reference_doctype": "Employee",
				"employee": row.name,
				"employee_name": row.employee_name,
				"due_date": row.custom_qd_probation_end,
				"days_remaining": (getdate(row.custom_qd_probation_end) - getdate(today())).days,
				"status": row.status,
			})
	# Contracts
	for row in frappe.get_all(
		"Employee",
		fields=["name", "employee_name", "contract_end_date", "status"],
		filters={
			"status": "Active",
			"contract_end_date": ["between", [today(), horizon]],
			**standard_filters(filters),
		},
	):
		data.append({
			"item": "Contract Expiry",
			"reference": row.name,
			"reference_doctype": "Employee",
			"employee": row.name,
			"employee_name": row.employee_name,
			"due_date": row.contract_end_date,
			"days_remaining": (getdate(row.contract_end_date) - getdate(today())).days,
			"status": row.status,
		})
	# Documents
	if frappe.db.exists("DocType", "QD Employee Document"):
		for row in frappe.get_all(
			"QD Employee Document",
			fields=["name", "employee", "employee_name", "expiry_date", "document_type", "title"],
			filters={"expiry_date": ["between", [today(), horizon]]},
		):
			data.append({
				"item": f"Document: {row.document_type}",
				"reference": row.name,
				"reference_doctype": "QD Employee Document",
				"employee": row.employee,
				"employee_name": row.employee_name,
				"due_date": row.expiry_date,
				"days_remaining": (getdate(row.expiry_date) - getdate(today())).days,
				"status": row.title,
			})
	# Certifications
	if frappe.db.exists("DocType", "QD Training Certification"):
		for row in frappe.get_all(
			"QD Training Certification",
			fields=["name", "employee", "employee_name", "expiry_date", "status", "course"],
			filters={"expiry_date": ["between", [today(), horizon]]},
		):
			data.append({
				"item": f"Certification: {row.course}",
				"reference": row.name,
				"reference_doctype": "QD Training Certification",
				"employee": row.employee,
				"employee_name": row.employee_name,
				"due_date": row.expiry_date,
				"days_remaining": (getdate(row.expiry_date) - getdate(today())).days,
				"status": row.status,
			})
	data.sort(key=lambda row: row.get("due_date") or today())
	return columns, data

