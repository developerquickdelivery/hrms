import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	if not frappe.db.exists("DocType", "QD Training Enrollment"):
		return [col("Info", "info")], [{"info": "Training Enrollment is not installed"}]
	columns = employee_columns() + [
		col("Enrollment", "name", "Link", "QD Training Enrollment", 150),
		col("Course", "course", "Link", "QD Training Course", 160),
		col("Program", "training_program", "Link", "Training Program", 160),
		col("Session", "training_session", "Link", "Training Event", 150),
		col("Enrollment Date", "enrollment_date", "Date", width=120),
		col("Status", "status", width=110),
		col("Attendance %", "attendance_percentage", "Percent", width=110),
	]
	conds = {}
	conds.update(date_between(filters, "enrollment_date"))
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	data = frappe.get_all(
		"QD Training Enrollment",
		fields=[
			"name", "employee", "employee_name", "department", "company", "course",
			"training_program", "training_session", "enrollment_date", "status",
			"attendance_percentage",
		],
		filters=conds,
		order_by="enrollment_date desc",
	)
	for row in data:
		row.setdefault("designation", None)
		row.setdefault("company", None)
	return columns, data

