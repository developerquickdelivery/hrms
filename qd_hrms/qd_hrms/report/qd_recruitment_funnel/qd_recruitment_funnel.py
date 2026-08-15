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

