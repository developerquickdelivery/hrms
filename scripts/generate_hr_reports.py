"""Generate QD HR Script Reports under qd_hrms/qd_hrms/report/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "qd_hrms_app" / "qd_hrms" / "qd_hrms" / "report"

REPORTS = [
	(
		"QD Workforce Report",
		"Employee",
		'''
from qd_hrms.report_utils import col, date_between, employee_columns, standard_filters
import frappe

def execute(filters=None):
	filters = filters or {}
	columns = employee_columns() + [
		col("Status", "status", width=100),
		col("Date of Joining", "date_of_joining", "Date", width=120),
		col("Relieving Date", "relieving_date", "Date", width=120),
		col("Employment Type", "employment_type", "Link", "Employment Type", 130),
		col("Grade", "grade", "Link", "Employee Grade", 120),
		col("Branch", "branch", "Link", "Branch", 120),
		col("Reports To", "reports_to", "Link", "Employee", 120),
	]
	conds = standard_filters(filters)
	conds.update(date_between(filters, "date_of_joining"))
	if filters.get("status"):
		conds["status"] = filters.get("status")
	data = frappe.get_all(
		"Employee",
		fields=[
			"name as employee", "employee_name", "department", "designation", "company",
			"status", "date_of_joining", "relieving_date", "employment_type", "grade",
			"branch", "reports_to",
		],
		filters=conds,
		order_by="date_of_joining desc",
	)
	return columns, data
''',
	),
	(
		"QD Headcount Report",
		"Employee",
		'''
from collections import defaultdict
import frappe
from qd_hrms.report_utils import col, standard_filters

def execute(filters=None):
	filters = filters or {}
	group_by = filters.get("group_by") or "department"
	field_map = {
		"department": ("department", "Department"),
		"designation": ("designation", "Designation"),
		"branch": ("branch", "Branch"),
		"company": ("company", "Company"),
		"employment_type": ("employment_type", "Employment Type"),
	}
	field, label = field_map.get(group_by, ("department", "Department"))
	columns = [
		col(label, "group_value", "Data", width=180),
		col("Active", "active", "Int", width=100),
		col("Left", "left_count", "Int", width=100),
		col("Total", "total", "Int", width=100),
	]
	conds = standard_filters(filters)
	rows = frappe.get_all(
		"Employee",
		fields=[field, "status"],
		filters=conds,
	)
	bucket = defaultdict(lambda: {"active": 0, "left_count": 0, "total": 0})
	for row in rows:
		key = row.get(field) or "Not Set"
		bucket[key]["total"] += 1
		if row.status == "Active":
			bucket[key]["active"] += 1
		elif row.status == "Left":
			bucket[key]["left_count"] += 1
	data = [
		{"group_value": key, **vals}
		for key, vals in sorted(bucket.items(), key=lambda item: item[0] or "")
	]
	chart = {
		"data": {
			"labels": [d["group_value"] for d in data],
			"datasets": [{"name": "Active", "values": [d["active"] for d in data]}],
		},
		"type": "bar",
	}
	return columns, data, None, chart
''',
	),
	(
		"QD Turnover Report",
		"Employee",
		'''
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
''',
	),
	(
		"QD Recruitment Funnel",
		"Job Applicant",
		'''
from collections import Counter
import frappe
from qd_hrms.report_utils import col, date_between, standard_filters

def execute(filters=None):
	filters = filters or {}
	columns = [
		col("Stage", "stage", width=160),
		col("Count", "count", "Int", width=100),
	]
	conds = {}
	conds.update(date_between(filters, "creation"))
	if filters.get("company"):
		# Job Applicant may not have company; filter openings via job_title when needed
		pass
	if filters.get("job_title"):
		conds["job_title"] = filters.get("job_title")
	rows = frappe.get_all("Job Applicant", fields=["status"], filters=conds)
	counter = Counter([row.status or "Open" for row in rows])
	order = ["Open", "Replied", "Rejected", "Accepted", "Hold"]
	data = [{"stage": stage, "count": counter.get(stage, 0)} for stage in order]
	for stage, count in counter.items():
		if stage not in order:
			data.append({"stage": stage, "count": count})
	openings = frappe.db.count("Job Opening", {"status": "Open"})
	offers = frappe.db.count("Job Offer", {"docstatus": 1})
	data = [
		{"stage": "Open Vacancies", "count": openings},
		*data,
		{"stage": "Job Offers Issued", "count": offers},
	]
	chart = {
		"data": {
			"labels": [d["stage"] for d in data],
			"datasets": [{"name": "Count", "values": [d["count"] for d in data]}],
		},
		"type": "bar",
	}
	return columns, data, None, chart
''',
	),
	(
		"QD Recruitment Performance",
		"Job Opening",
		'''
import frappe
from qd_hrms.report_utils import col, date_between

def execute(filters=None):
	filters = filters or {}
	columns = [
		col("Job Opening", "job_opening", "Link", "Job Opening", 180),
		col("Designation", "designation", "Link", "Designation", 140),
		col("Department", "department", "Link", "Department", 140),
		col("Status", "status", width=100),
		col("Applicants", "applicants", "Int", width=100),
		col("Offers", "offers", "Int", width=90),
		col("Accepted Offers", "accepted", "Int", width=120),
	]
	conds = date_between(filters, "posted_on")
	if filters.get("company"):
		conds["company"] = filters.get("company")
	openings = frappe.get_all(
		"Job Opening",
		fields=["name", "designation", "department", "status", "company"],
		filters=conds,
		order_by="modified desc",
	)
	data = []
	for opening in openings:
		applicants = frappe.get_all("Job Applicant", filters={"job_title": opening.name}, pluck="name")
		applicant_filter = applicants or ["__none__"]
		offers = frappe.db.count("Job Offer", {"job_applicant": ["in", applicant_filter]})
		accepted = frappe.db.count(
			"Job Offer",
			{"job_applicant": ["in", applicant_filter], "status": "Accepted"},
		)
		data.append({
			"job_opening": opening.name,
			"designation": opening.designation,
			"department": opening.department,
			"status": opening.status,
			"applicants": len(applicants),
			"offers": offers,
			"accepted": accepted,
		})
	return columns, data
''',
	),
	(
		"QD Attendance Report",
		"Attendance",
		'''
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
''',
	),
	(
		"QD Overtime Report",
		"Overtime Request",
		'''
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
''',
	),
	(
		"QD Leave Report",
		"Leave Application",
		'''
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
''',
	),
	(
		"QD Payroll Report",
		"Payroll Entry",
		'''
import frappe
from qd_hrms.report_utils import col, date_between

def execute(filters=None):
	filters = filters or {}
	columns = [
		col("Payroll Entry", "name", "Link", "Payroll Entry", 160),
		col("Company", "company", "Link", "Company", 140),
		col("Posting Date", "posting_date", "Date", width=110),
		col("Start Date", "start_date", "Date", width=110),
		col("End Date", "end_date", "Date", width=110),
		col("Employees", "number_of_employees", "Int", width=100),
		col("Status", "status", width=110),
		col("Docstatus", "docstatus", "Int", width=90),
	]
	conds = {}
	conds.update(date_between(filters, "posting_date"))
	if filters.get("company"):
		conds["company"] = filters.get("company")
	data = frappe.get_all(
		"Payroll Entry",
		fields=[
			"name", "company", "posting_date", "start_date", "end_date",
			"number_of_employees", "status", "docstatus",
		],
		filters=conds,
		order_by="posting_date desc",
	)
	return columns, data
''',
	),
	(
		"QD Salary Report",
		"Salary Slip",
		'''
import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	columns = employee_columns() + [
		col("Salary Slip", "name", "Link", "Salary Slip", 150),
		col("Start Date", "start_date", "Date", width=110),
		col("End Date", "end_date", "Date", width=110),
		col("Gross Pay", "gross_pay", "Currency", width=120),
		col("Total Deduction", "total_deduction", "Currency", width=120),
		col("Net Pay", "net_pay", "Currency", width=120),
		col("Status", "status", width=100),
	]
	conds = {"docstatus": 1}
	conds.update(date_between(filters, "start_date"))
	if filters.get("company"):
		conds["company"] = filters.get("company")
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("department"):
		conds["department"] = filters.get("department")
	data = frappe.get_all(
		"Salary Slip",
		fields=[
			"name", "employee", "employee_name", "department", "designation", "company",
			"start_date", "end_date", "gross_pay", "total_deduction", "net_pay", "status",
		],
		filters=conds,
		order_by="start_date desc",
	)
	return columns, data
''',
	),
	(
		"QD Benefits Report",
		"Employee Benefit Application",
		'''
import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
	filters = filters or {}
	# Prefer Employee Benefit Application; fall back to Additional Salary benefit-like rows
	if frappe.db.exists("DocType", "Employee Benefit Application"):
		columns = employee_columns() + [
			col("Benefit Application", "name", "Link", "Employee Benefit Application", 170),
			col("Payroll Period", "payroll_period", "Link", "Payroll Period", 140),
			col("Max Benefit Amount", "max_benefits", "Currency", width=140),
			col("Remaining Benefit", "remaining_benefit", "Currency", width=140),
			col("Docstatus", "docstatus", "Int", width=90),
		]
		conds = {}
		if filters.get("employee"):
			conds["employee"] = filters.get("employee")
		if filters.get("company"):
			conds["company"] = filters.get("company")
		fields = ["name", "employee", "employee_name", "company", "docstatus"]
		meta = frappe.get_meta("Employee Benefit Application")
		for field in ("payroll_period", "max_benefits", "remaining_benefit", "department"):
			if meta.has_field(field):
				fields.append(field)
		data = frappe.get_all("Employee Benefit Application", fields=fields, filters=conds, order_by="modified desc")
		for row in data:
			row.setdefault("designation", None)
			row.setdefault("department", None)
		return columns, data

	columns = employee_columns() + [
		col("Additional Salary", "name", "Link", "Additional Salary", 150),
		col("Salary Component", "salary_component", "Link", "Salary Component", 150),
		col("Amount", "amount", "Currency", width=120),
		col("Payroll Date", "payroll_date", "Date", width=110),
		col("Docstatus", "docstatus", "Int", width=90),
	]
	conds = {"docstatus": ["<", 2]}
	conds.update(date_between(filters, "payroll_date"))
	if filters.get("employee"):
		conds["employee"] = filters.get("employee")
	if filters.get("company"):
		conds["company"] = filters.get("company")
	data = frappe.get_all(
		"Additional Salary",
		fields=["name", "employee", "employee_name", "company", "salary_component", "amount", "payroll_date", "docstatus"],
		filters=conds,
		order_by="payroll_date desc",
	)
	for row in data:
		row.setdefault("department", None)
		row.setdefault("designation", None)
	return columns, data
''',
	),
	(
		"QD Performance Report",
		"Appraisal",
		'''
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
''',
	),
	(
		"QD Training Report",
		"QD Training Enrollment",
		'''
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
''',
	),
	(
		"QD Certification Report",
		"QD Training Certification",
		'''
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
''',
	),
	(
		"QD Employee Relations Report",
		"QD HR Case",
		'''
import frappe
from qd_hrms.report_utils import col, date_between, employee_columns

def execute(filters=None):
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
''',
	),
	(
		"QD Compliance Report",
		"Employee",
		'''
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
''',
	),
]


def snake(name: str) -> str:
	return name.lower().replace(" ", "_")


def report_json(name: str, ref_doctype: str) -> dict:
	return {
		"add_total_row": 0,
		"columns": [],
		"creation": "2026-08-15 00:00:00",
		"disabled": 0,
		"docstatus": 0,
		"doctype": "Report",
		"filters": [],
		"is_standard": "Yes",
		"modified": "2026-08-15 00:00:00",
		"modified_by": "Administrator",
		"module": "QD HRMS",
		"name": name,
		"owner": "Administrator",
		"prepared_report": 0,
		"ref_doctype": ref_doctype,
		"report_name": name,
		"report_type": "Script Report",
		"roles": [
			{"role": "System Manager"},
			{"role": "HR Manager"},
			{"role": "HR User"},
		],
	}


def report_js(name: str) -> str:
	return f'''frappe.query_reports["{name}"] = {{
	filters: [
		{{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		}},
		{{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
		}},
		{{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		}},
		{{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		}},
		{{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		}},
	],
}};
'''


def main():
	ROOT.mkdir(parents=True, exist_ok=True)
	(ROOT / "__init__.py").write_text("", encoding="utf-8")
	for name, ref, code in REPORTS:
		folder = ROOT / snake(name)
		folder.mkdir(parents=True, exist_ok=True)
		(folder / "__init__.py").write_text("", encoding="utf-8")
		(folder / f"{snake(name)}.json").write_text(
			json.dumps(report_json(name, ref), indent=1) + "\n", encoding="utf-8"
		)
		(folder / f"{snake(name)}.py").write_text(code.lstrip() + "\n", encoding="utf-8")
		(folder / f"{snake(name)}.js").write_text(report_js(name), encoding="utf-8")
		print("created", name)
	print(f"total={len(REPORTS)} path={ROOT}")


if __name__ == "__main__":
	main()
