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

