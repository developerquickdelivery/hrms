from collections import defaultdict
import frappe
from qd_hrms.report_utils import col, date_between, employee_columns, standard_filters

def execute(filters=None):
	filters = filters or {}
	columns = employee_columns() + [
		col("Present", "present", "Int", width=90),
		col("Absent", "absent", "Int", width=90),
		col("On Leave", "on_leave", "Int", width=90),
		col("Half Day", "half_day", "Int", width=90),
		col("Work From Home", "wfh", "Int", width=120),
	]
	conds = {"docstatus": 1}
	conds.update(date_between(filters, "attendance_date"))
	if filters.get("company"):
		conds["company"] = filters.get("company")
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("department"):
		emps = frappe.get_all(
			"Employee",
			filters={"department": filters.get("department")},
			pluck="name",
		)
		conds["employee"] = ["in", emps or ["__none__"]]
	rows = frappe.get_all(
		"Attendance",
		fields=["employee", "employee_name", "department", "status", "company"],
		filters=conds,
	)
	bucket = defaultdict(lambda: {
		"employee": None, "employee_name": None, "department": None, "designation": None,
		"company": None, "present": 0, "absent": 0, "on_leave": 0, "half_day": 0, "wfh": 0,
	})
	for row in rows:
		item = bucket[row.employee]
		item["employee"] = row.employee
		item["employee_name"] = row.employee_name
		item["department"] = row.department
		item["company"] = row.company
		key = {
			"Present": "present",
			"Absent": "absent",
			"On Leave": "on_leave",
			"Half Day": "half_day",
			"Work From Home": "wfh",
		}.get(row.status)
		if key:
			item[key] += 1
	return columns, list(bucket.values())

