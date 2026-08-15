import frappe
from frappe.utils import getdate
from qd_hrms.report_utils import col, date_between, standard_filters

def execute(filters=None):
	filters = filters or {}
	columns = [
		col("Department", "department", "Link", "Department", 160),
		col("Opening Headcount", "opening", "Int", width=130),
		col("New Hires", "hires", "Int", width=100),
		col("Exits", "exits", "Int", width=100),
		col("Closing Headcount", "closing", "Int", width=130),
		col("Turnover %", "turnover", "Percent", width=110),
	]
	conds = standard_filters(filters)
	from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
	to_date = getdate(filters.get("to_date")) if filters.get("to_date") else None
	employees = frappe.get_all(
		"Employee",
		fields=["department", "status", "date_of_joining", "relieving_date"],
		filters=conds,
	)
	by_dept = {}
	for emp in employees:
		dept = emp.department or "Not Set"
		row = by_dept.setdefault(dept, {"opening": 0, "hires": 0, "exits": 0, "closing": 0})
		joined = getdate(emp.date_of_joining) if emp.date_of_joining else None
		relieved = getdate(emp.relieving_date) if emp.relieving_date else None
		was_active_at_start = bool(joined and (not from_date or joined < from_date) and (not relieved or relieved >= from_date))
		if was_active_at_start:
			row["opening"] += 1
		if joined and from_date and to_date and from_date <= joined <= to_date:
			row["hires"] += 1
		if relieved and from_date and to_date and from_date <= relieved <= to_date:
			row["exits"] += 1
		is_active_now = emp.status == "Active"
		if is_active_now:
			row["closing"] += 1
	data = []
	for dept, vals in sorted(by_dept.items()):
		base = vals["opening"] or vals["closing"]
		turnover = (vals["exits"] / base * 100.0) if base else 0
		data.append({"department": dept, "turnover": turnover, **vals})
	return columns, data

