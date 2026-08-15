"""Performance helpers: reviewers, calibration loaders, and appraisal guards."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, today


def get_employee_user(employee: str | None) -> str | None:
	if not employee:
		return None
	return frappe.db.get_value("Employee", employee, "user_id")


def get_primary_manager_user(employee: str | None) -> str | None:
	if not employee:
		return None
	reports_to = frappe.db.get_value("Employee", employee, "reports_to")
	return get_employee_user(reports_to)


def get_secondary_manager_user(employee: str | None) -> str | None:
	if not employee or not frappe.db.exists("DocType", "Employee Reporting Assignment"):
		return None
	secondary = frappe.db.get_value(
		"Employee Reporting Assignment",
		{"employee": employee, "status": "Current", "docstatus": 1},
		"secondary_manager",
	)
	return get_employee_user(secondary)


def set_appraisal_reviewers(doc, method=None):
	if not doc.employee:
		return
	manager = get_primary_manager_user(doc.employee)
	second = get_secondary_manager_user(doc.employee)
	if doc.meta.has_field("custom_qd_manager_reviewer"):
		doc.custom_qd_manager_reviewer = manager
	if doc.meta.has_field("custom_qd_second_level_reviewer"):
		doc.custom_qd_second_level_reviewer = second


def validate_appraisal(doc, method=None):
	set_appraisal_reviewers(doc)
	if doc.meta.has_field("custom_qd_pip_required") and doc.custom_qd_pip_required:
		if doc.meta.has_field("custom_qd_rating_band") and not doc.custom_qd_rating_band:
			doc.custom_qd_rating_band = "Needs Improvement"


def before_submit_appraisal(doc, method=None):
	status = getattr(doc, "custom_qd_review_status", None) or "Draft"
	if status in ("Completed", "Calibrated"):
		return
	roles = set(frappe.get_roles())
	if roles.intersection({"System Manager", "HR Manager", "HR User"}):
		return
	frappe.throw(
		_("Complete Self, Manager, and Second-Level review before finalizing this appraisal."),
		frappe.ValidationError,
	)


@frappe.whitelist()
def load_calibration_rows(appraisal_cycle: str, department: str | None = None):
	filters = {"appraisal_cycle": appraisal_cycle, "docstatus": ["<", 2]}
	if department:
		filters["department"] = department
	rows = frappe.get_all(
		"Appraisal",
		filters=filters,
		fields=["name as appraisal", "employee", "employee_name", "final_score as original_score"],
		order_by="employee_name asc",
	)
	for row in rows:
		row["calibrated_score"] = row.get("original_score") or 0
	return rows


@frappe.whitelist()
def start_pip_from_appraisal(appraisal: str):
	appraisal_doc = frappe.get_doc("Appraisal", appraisal)
	if not appraisal_doc.custom_qd_pip_required:
		frappe.throw(_("Mark the appraisal as PIP Required first."))
	existing = frappe.db.exists(
		"QD Performance Improvement Plan",
		{"appraisal": appraisal, "docstatus": ["<", 2]},
	)
	if existing:
		return existing
	pip = frappe.get_doc(
		{
			"doctype": "QD Performance Improvement Plan",
			"employee": appraisal_doc.employee,
			"appraisal": appraisal_doc.name,
			"appraisal_cycle": appraisal_doc.appraisal_cycle,
			"manager": frappe.db.get_value("Employee", appraisal_doc.employee, "reports_to"),
			"start_date": today(),
			"end_date": getdate(frappe.utils.add_days(today(), 90)),
			"reason": _("Opened from appraisal {0}").format(appraisal_doc.name),
			"performance_gap": appraisal_doc.remarks or _("Performance below expected standard."),
			"expected_standard": _("Meet role expectations within the PIP period."),
			"objectives": [
				{
					"objective": _("Improve overall performance score"),
					"target": "Meets Expectations",
					"status": "Open",
				}
			],
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Appraisal", appraisal, "custom_qd_pip", pip.name)
	return pip.name
