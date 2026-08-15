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

