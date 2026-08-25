from collections import Counter

import frappe
from qd_hrms.report_utils import assert_report_roles, col, date_between, HR_REPORT_ROLES


def execute(filters=None):
	assert_report_roles(HR_REPORT_ROLES)
	filters = filters or {}
	columns = [
		col("Stage", "stage", width=160),
		col("Count", "count", "Int", width=100),
	]

	opening_filters = {}
	if filters.get("company"):
		opening_filters["company"] = filters.get("company")
	if filters.get("department"):
		opening_filters["department"] = filters.get("department")

	openings = frappe.get_all(
		"Job Opening",
		filters=opening_filters,
		pluck="name",
	)
	if not openings:
		return columns, [], None, None

	applicant_filters = {"job_title": ["in", openings]}
	applicant_filters.update(date_between(filters, "creation"))
	rows = frappe.get_all("Job Applicant", fields=["status"], filters=applicant_filters)
	counter = Counter([row.status or "Open" for row in rows])
	order = ["Open", "Replied", "Rejected", "Accepted", "Hold"]
	data = [{"stage": stage, "count": counter.get(stage, 0)} for stage in order]
	for stage, count in counter.items():
		if stage not in order:
			data.append({"stage": stage, "count": count})

	open_vacancies = frappe.db.count(
		"Job Opening",
		{**opening_filters, "status": "Open"},
	)
	offer_filters = {"docstatus": 1}
	offer_filters.update(date_between(filters, "offer_date"))
	if filters.get("company"):
		offer_filters["company"] = filters.get("company")
	offers = frappe.db.count("Job Offer", offer_filters)

	data = [
		{"stage": "Open Vacancies", "count": open_vacancies},
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
