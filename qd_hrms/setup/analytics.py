"""HR Executive Dashboard and analytics workspace using ERPNext Dashboard engine."""

from __future__ import annotations

import json

import frappe

DASHBOARD = "QD HR Executive Dashboard"
WORKSPACE = "HR Reports and Analytics"

CARD_METHODS = (
	("QD Total Employees", "Employee", "qd_hrms.analytics.total_employees", "#449CF0"),
	("QD New Hires YTD", "Employee", "qd_hrms.analytics.new_hires_ytd", "#28A745"),
	("QD Exits YTD", "Employee", "qd_hrms.analytics.exits_ytd", "#EC645E"),
	("QD Turnover YTD", "Employee", "qd_hrms.analytics.turnover_ytd", "#ED6396"),
	("QD Open Vacancies", "Job Opening", "qd_hrms.analytics.open_vacancies", "#EC864B"),
	("QD Attendance Present MTD", "Attendance", "qd_hrms.analytics.attendance_present_mtd", "#28A745"),
	("QD Absence MTD", "Attendance", "qd_hrms.analytics.attendance_absent_mtd", "#CB2929"),
	("QD Leave Applications MTD", "Leave Application", "qd_hrms.analytics.leave_applications_mtd", "#449CF0"),
	("QD Payroll Slips MTD", "Salary Slip", "qd_hrms.analytics.payroll_entries_mtd", "#761ACB"),
	("QD Training Enrollments YTD", "QD Training Enrollment", "qd_hrms.analytics.training_enrollments_ytd", "#4463F0"),
	("QD Open Appraisals", "Appraisal", "qd_hrms.analytics.performance_appraisals_open", "#EC864B"),
	("QD Expiring Documents 30d", "QD Employee Document", "qd_hrms.analytics.expiring_documents_30d", "#CB2929"),
	("QD Probation Expiry 30d", "Employee", "qd_hrms.analytics.probation_expiry_30d", "#ED6396"),
	("QD Contract Expiry 30d", "Employee", "qd_hrms.analytics.contract_expiry_30d", "#EC645E"),
)

REPORTS = (
	"QD Workforce Report",
	"QD Headcount Report",
	"QD Turnover Report",
	"QD Recruitment Funnel",
	"QD Recruitment Performance",
	"QD Attendance Report",
	"QD Overtime Report",
	"QD Leave Report",
	"QD Payroll Report",
	"QD Salary Report",
	"QD Benefits Report",
	"QD Performance Report",
	"QD Training Report",
	"QD Certification Report",
	"QD Employee Relations Report",
	"QD Compliance Report",
)


def run():
	ensure_number_cards()
	ensure_charts()
	ensure_dashboard()
	ensure_workspace()
	frappe.clear_cache()
	return verify()


def ensure_number_cards():
	for label, document_type, method, color in CARD_METHODS:
		if not frappe.db.exists("DocType", document_type):
			# Fall back document type for permission scoping when custom DocType missing.
			document_type = "Employee"
		doc = (
			frappe.get_doc("Number Card", label)
			if frappe.db.exists("Number Card", label)
			else frappe.new_doc("Number Card")
		)
		if doc.is_new():
			doc.label = label
			doc.name = label
		doc.type = "Custom"
		doc.method = method
		doc.document_type = document_type
		doc.is_public = 1
		doc.is_standard = 0
		doc.module = "QD HRMS"
		doc.color = color
		doc.show_percentage_stats = 0
		doc.filters_json = "null"
		doc.save(ignore_permissions=True)


def ensure_charts():
	charts = (
		{
			"chart_name": "QD Employees by Department",
			"chart_type": "Group By",
			"document_type": "Employee",
			"group_by_based_on": "department",
			"group_by_type": "Count",
			"filters_json": json.dumps([["Employee", "status", "=", "Active"]]),
			"type": "Donut",
			"is_public": 1,
		},
		{
			"chart_name": "QD Attendance Status MTD",
			"chart_type": "Group By",
			"document_type": "Attendance",
			"group_by_based_on": "status",
			"group_by_type": "Count",
			"filters_json": json.dumps(
				[
					["Attendance", "docstatus", "=", 1],
					["Attendance", "attendance_date", "Timespan", "this month"],
				]
			),
			"type": "Bar",
			"is_public": 1,
		},
		{
			"chart_name": "QD Leave by Type MTD",
			"chart_type": "Group By",
			"document_type": "Leave Application",
			"group_by_based_on": "leave_type",
			"group_by_type": "Count",
			"filters_json": json.dumps(
				[
					["Leave Application", "docstatus", "=", 1],
					["Leave Application", "from_date", "Timespan", "this month"],
				]
			),
			"type": "Pie",
			"is_public": 1,
		},
		{
			"chart_name": "QD Hiring Trend",
			"chart_type": "Count",
			"document_type": "Employee",
			"based_on": "date_of_joining",
			"timeseries": 1,
			"timespan": "Last Year",
			"time_interval": "Monthly",
			"filters_json": json.dumps([]),
			"type": "Line",
			"is_public": 1,
		},
	)
	for values in charts:
		name = values["chart_name"]
		doc = (
			frappe.get_doc("Dashboard Chart", name)
			if frappe.db.exists("Dashboard Chart", name)
			else frappe.new_doc("Dashboard Chart")
		)
		if doc.is_new():
			doc.chart_name = name
		doc.update(values)
		doc.module = "QD HRMS"
		doc.is_standard = 0
		doc.save(ignore_permissions=True)


def ensure_dashboard():
	doc = (
		frappe.get_doc("Dashboard", DASHBOARD)
		if frappe.db.exists("Dashboard", DASHBOARD)
		else frappe.new_doc("Dashboard")
	)
	if doc.is_new():
		doc.dashboard_name = DASHBOARD
	doc.module = "QD HRMS"
	doc.is_standard = 0
	doc.is_default = 0
	doc.charts = []
	doc.cards = []
	for chart in (
		"QD Employees by Department",
		"QD Attendance Status MTD",
		"QD Leave by Type MTD",
		"QD Hiring Trend",
	):
		if frappe.db.exists("Dashboard Chart", chart):
			doc.append("charts", {"chart": chart, "width": "Half"})
	for label, *_rest in CARD_METHODS:
		if frappe.db.exists("Number Card", label):
			doc.append("cards", {"card": label})
	doc.save(ignore_permissions=True)


def ensure_workspace():
	doc = (
		frappe.get_doc("Workspace", WORKSPACE)
		if frappe.db.exists("Workspace", WORKSPACE)
		else frappe.new_doc("Workspace")
	)
	if doc.is_new():
		doc.label = WORKSPACE
	doc.title = WORKSPACE
	doc.module = "QD HRMS"
	doc.icon = "chart"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>HR Reports and Analytics</b></span>', "col": 12},
		)
	]
	doc.append(
		"shortcuts",
		{
			"type": "Dashboard",
			"link_to": DASHBOARD,
			"label": "Executive Dashboard",
			"color": "Blue",
		},
	)
	content.append(_block("shortcut", {"shortcut_name": "Executive Dashboard", "col": 4}))

	for report in REPORTS:
		if not frappe.db.exists("Report", report):
			continue
		doc.append(
			"shortcuts",
			{
				"type": "Report",
				"link_to": report,
				"label": report.replace("QD ", ""),
				"color": "Grey",
			},
		)
		content.append(
			_block("shortcut", {"shortcut_name": report.replace("QD ", ""), "col": 3})
		)

	doc.content = json.dumps(content)
	doc.flags.ignore_links = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	missing_reports = [name for name in REPORTS if not frappe.db.exists("Report", name)]
	if missing_reports:
		raise frappe.ValidationError(f"Missing reports: {', '.join(missing_reports)}")
	if not frappe.db.exists("Dashboard", DASHBOARD):
		raise frappe.ValidationError("Executive Dashboard missing")
	missing_cards = [label for label, *_ in CARD_METHODS if not frappe.db.exists("Number Card", label)]
	if missing_cards:
		raise frappe.ValidationError(f"Missing number cards: {', '.join(missing_cards)}")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("HR Reports workspace missing")
	return {
		"engine": "ERPNext Dashboard / Script Report",
		"dashboard": DASHBOARD,
		"cards": len(CARD_METHODS),
		"reports": len(REPORTS),
		"workspace": WORKSPACE,
		"verified": True,
	}
