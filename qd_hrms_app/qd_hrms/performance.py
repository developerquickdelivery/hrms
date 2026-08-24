"""Performance helpers: reviewers, calibration loaders, and appraisal guards."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

PIP_RATING_BANDS = {"unsatisfactory", "needs improvement"}
PEER_FEEDBACK_SCOPES = {"Peer", "360"}
FEEDBACK_SCOPES = {"Peer", "360", "Manager", "Skip-Level", "Customer"}


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


def rating_band_for_score(score, levels):
	"""Map a numeric score to the nearest rating-scale level label."""
	score = flt(score)
	rows = []
	for row in levels or []:
		label = row.get("label") if isinstance(row, dict) else getattr(row, "label", None)
		if not label:
			continue
		level_score = row.get("score") if isinstance(row, dict) else getattr(row, "score", 0)
		rows.append({"score": flt(level_score), "label": label})
	if not rows:
		return None
	return min(rows, key=lambda row: abs(row["score"] - score))["label"]


def _appraisal_rating_scale(doc):
	cycle_meta = frappe.get_meta("Appraisal Cycle") if doc.get("appraisal_cycle") else None
	if cycle_meta and cycle_meta.has_field("custom_qd_rating_scale"):
		scale = frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "custom_qd_rating_scale")
		if scale:
			return scale
	template = doc.get("appraisal_template")
	if template:
		template_meta = frappe.get_meta("Appraisal Template")
		if template_meta.has_field("custom_qd_rating_scale"):
			scale = frappe.db.get_value("Appraisal Template", template, "custom_qd_rating_scale")
			if scale:
				return scale
	return frappe.db.get_value("QD Rating Scale", {"is_default": 1}, "name")


def _scale_levels(scale_name):
	if not scale_name or not frappe.db.exists("QD Rating Scale", scale_name):
		return []
	return frappe.get_all(
		"QD Rating Scale Level",
		filters={"parent": scale_name, "parenttype": "QD Rating Scale"},
		fields=["score", "label"],
		order_by="score asc",
	)


def apply_rating_band(doc):
	if not doc.meta.has_field("custom_qd_rating_band"):
		return
	score = doc.get("custom_qd_calibrated_score")
	if score in (None, ""):
		score = doc.get("final_score")
	if score in (None, ""):
		return
	band = rating_band_for_score(score, _scale_levels(_appraisal_rating_scale(doc)))
	if not band:
		return
	doc.custom_qd_rating_band = band
	if doc.meta.has_field("custom_qd_pip_required") and band.strip().lower() in PIP_RATING_BANDS:
		doc.custom_qd_pip_required = 1


def _seed_formula_scores(doc):
	"""Keep cycle formulas numeric when manager / skip-level scores are still blank."""
	fallback = flt(doc.get("self_appraisal_score") or doc.get("goal_score") or 0)
	if doc.meta.has_field("custom_qd_manager_score") and doc.custom_qd_manager_score in (None, ""):
		doc.custom_qd_manager_score = fallback
	if doc.meta.has_field("custom_qd_second_level_score") and doc.custom_qd_second_level_score in (None, ""):
		doc.custom_qd_second_level_score = flt(doc.get("custom_qd_manager_score") or fallback)


def before_validate_appraisal(doc, method=None):
	set_appraisal_reviewers(doc)
	_seed_formula_scores(doc)


def _cycle_due_fields(doc):
	if not doc.get("appraisal_cycle"):
		return None
	fields = [
		"custom_qd_self_review_due",
		"custom_qd_manager_review_due",
		"custom_qd_calibration_due",
		"custom_qd_min_peer_feedback",
	]
	available = [
		field
		for field in fields
		if frappe.get_meta("Appraisal Cycle").has_field(field)
	]
	if not available:
		return None
	return frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, available, as_dict=True)


def warn_review_due_dates(doc):
	if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_migrate:
		return
	cycle = _cycle_due_fields(doc)
	if not cycle:
		return
	status = (doc.get("custom_qd_review_status") or "Draft").strip()
	today_date = getdate(today())
	self_due = cycle.get("custom_qd_self_review_due")
	manager_due = cycle.get("custom_qd_manager_review_due")
	if self_due and today_date > getdate(self_due) and status == "Draft":
		frappe.msgprint(_("Self review was due on {0}.").format(frappe.format(self_due)), alert=True)
	if manager_due and today_date > getdate(manager_due) and status not in ("Completed", "Calibrated"):
		frappe.msgprint(_("Manager review was due on {0}.").format(frappe.format(manager_due)), alert=True)


def validate_appraisal(doc, method=None):
	set_appraisal_reviewers(doc)
	apply_rating_band(doc)
	warn_review_due_dates(doc)
	if doc.meta.has_field("custom_qd_pip_required") and doc.custom_qd_pip_required:
		if doc.meta.has_field("custom_qd_rating_band") and not doc.custom_qd_rating_band:
			doc.custom_qd_rating_band = "Needs Improvement"


def _count_submitted_peer_feedback(appraisal):
	filters = {"appraisal": appraisal, "docstatus": 1}
	if frappe.get_meta("Employee Performance Feedback").has_field("custom_qd_feedback_scope"):
		filters["custom_qd_feedback_scope"] = ["in", list(PEER_FEEDBACK_SCOPES)]
	return frappe.db.count("Employee Performance Feedback", filters)


def enforce_min_peer_feedback(doc):
	cycle = _cycle_due_fields(doc)
	minimum = int(cycle.get("custom_qd_min_peer_feedback") or 0) if cycle else 0
	if minimum <= 0:
		return
	count = _count_submitted_peer_feedback(doc.name)
	if count < minimum:
		frappe.throw(
			_("This cycle requires at least {0} submitted Peer or 360 feedback(s). {1} received.").format(
				minimum, count
			),
			frappe.ValidationError,
		)


def enforce_calibration_due(doc):
	cycle = _cycle_due_fields(doc)
	due = cycle.get("custom_qd_calibration_due") if cycle else None
	if not due:
		return
	if getdate(today()) <= getdate(due):
		return
	if set(frappe.get_roles()) & {"System Manager", "HR Manager"}:
		return
	frappe.throw(
		_("Calibration was due on {0}. Ask HR to finalize this appraisal.").format(frappe.format(due)),
		frappe.ValidationError,
	)


def before_submit_appraisal(doc, method=None):
	enforce_min_peer_feedback(doc)
	enforce_calibration_due(doc)
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


def validate_performance_feedback(doc, method=None):
	if doc.employee and doc.reviewer and doc.employee == doc.reviewer:
		frappe.throw(_("An employee cannot provide feedback on their own appraisal."), frappe.ValidationError)
	if doc.meta.has_field("custom_qd_feedback_scope") and doc.custom_qd_feedback_scope not in FEEDBACK_SCOPES:
		doc.custom_qd_feedback_scope = "Peer"


def sync_recognition_badge(doc=None, method=None, user=None):
	user = user or getattr(doc, "user", None)
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		return
	points = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(points), 0)
		FROM `tabEnergy Point Log`
		WHERE user = %s
		""",
		(user,),
	)[0][0]
	points = int(points or 0)
	badge = ""
	for threshold, label in ((1000, "Platinum"), (600, "Gold"), (300, "Silver"), (100, "Bronze")):
		if points >= threshold:
			badge = label
			break
	frappe.db.set_value(
		"User",
		user,
		{
			"custom_qd_recognition_points": points,
			"custom_qd_recognition_badge": badge,
		},
		update_modified=False,
	)


def reconcile_recognition_badges():
	for user in frappe.get_all(
		"Energy Point Log",
		filters={"user": ["not in", ["Administrator", "Guest"]]},
		distinct=True,
		pluck="user",
	):
		try:
			sync_recognition_badge(user=user)
		except Exception:
			frappe.log_error(
				title=f"Recognition badge sync failed: {user}",
				message=frappe.get_traceback(),
			)


@frappe.whitelist()
def load_calibration_rows(appraisal_cycle: str, department: str | None = None):
	if not set(frappe.get_roles()) & {"System Manager", "HR Manager", "HR User"}:
		frappe.throw(_("Not permitted to load calibration rows."), frappe.PermissionError)
	filters = {"appraisal_cycle": appraisal_cycle, "docstatus": ["<", 2]}
	if department:
		filters["department"] = department
	rows = frappe.get_all(
		"Appraisal",
		filters=filters,
		fields=[
			"name as appraisal",
			"employee",
			"employee_name",
			"final_score as original_score",
			"custom_qd_potential_score as potential_score",
		],
		order_by="employee_name asc",
	)
	for row in rows:
		row["calibrated_score"] = row.get("original_score") or 0
		row["potential_score"] = row.get("potential_score") or 3
		row["retention_risk"] = "Low"
	return rows


def _assert_executive_calibration_access(write=False):
	allowed = {"System Manager", "HR Manager"}
	if not set(frappe.get_roles()) & allowed and frappe.session.user != "Administrator":
		frappe.throw(_("Executive calibration access is required."), frappe.PermissionError)
	if write and frappe.session.user == "Guest":
		frappe.throw(_("Not permitted."), frappe.PermissionError)


@frappe.whitelist()
def get_nine_box_data(calibration: str):
	_assert_executive_calibration_access()
	doc = frappe.get_doc("QD Performance Calibration", calibration)
	doc.check_permission("read")
	doc.run_method("validate")
	rows = []
	for row in doc.appraisals:
		rows.append(
			{
				"name": row.name,
				"appraisal": row.appraisal,
				"employee": row.employee,
				"employee_name": row.employee_name,
				"calibrated_score": row.calibrated_score,
				"potential_score": row.potential_score,
				"performance_level": row.performance_level,
				"potential_level": row.potential_level,
				"nine_box": row.nine_box,
				"rating_band": row.rating_band,
				"critical_role": row.critical_role,
				"retention_risk": row.retention_risk,
				"successor_ready": row.successor_ready,
				"development_action": row.development_action,
				"rationale": row.rationale,
			}
		)
	return {
		"name": doc.name,
		"appraisal_cycle": doc.appraisal_cycle,
		"department": doc.department,
		"approval_status": doc.approval_status,
		"docstatus": doc.docstatus,
		"low_score_max": doc.low_score_max,
		"high_score_min": doc.high_score_min,
		"rows": rows,
	}


@frappe.whitelist()
def update_nine_box_placement(
	calibration: str,
	appraisal: str,
	performance_level: str,
	potential_level: str,
	rationale: str | None = None,
	development_action: str | None = None,
	retention_risk: str = "Low",
	critical_role: int = 0,
	successor_ready: int = 0,
):
	_assert_executive_calibration_access(write=True)
	doc = frappe.get_doc("QD Performance Calibration", calibration)
	doc.check_permission("write")
	if doc.docstatus != 0 or doc.approval_status == "Completed":
		frappe.throw(_("Completed or submitted calibrations cannot be changed."))
	levels = {"Low": 2, "Moderate": 3, "High": 5}
	if performance_level not in levels or potential_level not in levels:
		frappe.throw(_("Performance and Potential must be Low, Moderate, or High."))
	row = next((item for item in doc.appraisals if item.appraisal == appraisal), None)
	if not row:
		frappe.throw(_("Appraisal {0} is not in this calibration.").format(appraisal))
	row.calibrated_score = levels[performance_level]
	row.potential_score = levels[potential_level]
	row.rationale = rationale
	row.development_action = development_action
	row.retention_risk = retention_risk
	row.critical_role = int(critical_role or 0)
	row.successor_ready = int(successor_ready or 0)
	doc.save()
	return get_nine_box_data(doc.name)


@frappe.whitelist()
def start_pip_from_appraisal(appraisal: str):
	appraisal_doc = frappe.get_doc("Appraisal", appraisal)
	appraisal_doc.check_permission("read")
	if not set(frappe.get_roles()) & {"System Manager", "HR Manager", "HR User", "Leave Approver"}:
		frappe.throw(_("Not permitted to start a PIP."), frappe.PermissionError)
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
	).insert()
	frappe.db.set_value("Appraisal", appraisal, "custom_qd_pip", pip.name)
	return pip.name


def _assert_can_request_feedback(appraisal_doc):
	user = frappe.session.user
	if user == "Administrator" or set(frappe.get_roles()) & {"System Manager", "HR Manager", "HR User"}:
		return
	if user == get_employee_user(appraisal_doc.employee):
		return
	if user in (
		appraisal_doc.get("custom_qd_manager_reviewer"),
		appraisal_doc.get("custom_qd_second_level_reviewer"),
	):
		return
	appraisal_doc.check_permission("write")


def _parse_reviewers(reviewers):
	if isinstance(reviewers, str):
		reviewers = json.loads(reviewers)
	if isinstance(reviewers, dict):
		reviewers = reviewers.get("reviewers") or reviewers.get("employee") or []
	names = []
	for item in reviewers or []:
		if isinstance(item, dict):
			item = item.get("employee") or item.get("reviewer") or item.get("name")
		if item:
			names.append(item)
	return list(dict.fromkeys(names))


@frappe.whitelist()
def request_peer_feedback(appraisal, reviewers, scope="Peer"):
	appraisal_doc = frappe.get_doc("Appraisal", appraisal)
	appraisal_doc.check_permission("read")
	_assert_can_request_feedback(appraisal_doc)
	if appraisal_doc.docstatus != 0:
		frappe.throw(_("Feedback can only be requested on a draft appraisal."))
	scope = scope if scope in FEEDBACK_SCOPES else "Peer"
	reviewer_names = _parse_reviewers(reviewers)
	if not reviewer_names:
		frappe.throw(_("Select at least one reviewer."))

	created = []
	for reviewer in reviewer_names:
		if reviewer == appraisal_doc.employee:
			frappe.throw(_("An employee cannot provide feedback on their own appraisal."))
		if not frappe.db.exists("Employee", reviewer):
			frappe.throw(_("Employee {0} does not exist.").format(reviewer))
		existing = frappe.db.exists(
			"Employee Performance Feedback",
			{"appraisal": appraisal_doc.name, "reviewer": reviewer, "docstatus": ["<", 2]},
		)
		if existing:
			created.append(existing)
			continue
		feedback = frappe.get_doc(
			{
				"doctype": "Employee Performance Feedback",
				"employee": appraisal_doc.employee,
				"reviewer": reviewer,
				"appraisal": appraisal_doc.name,
				"appraisal_cycle": appraisal_doc.appraisal_cycle,
				"custom_qd_feedback_scope": scope,
			}
		)
		feedback.feedback = _("Please add your {0} feedback.").format(scope)
		feedback.insert(ignore_mandatory=True)
		reviewer_user = get_employee_user(reviewer)
		if reviewer_user:
			try:
				from frappe.desk.form.assign_to import add as assign_to

				assign_to(
					{
						"assign_to": [reviewer_user],
						"doctype": "Employee Performance Feedback",
						"name": feedback.name,
						"description": _("Please provide {0} feedback for {1}.").format(
							scope, appraisal_doc.employee_name or appraisal_doc.employee
						),
					}
				)
			except Exception:
				frappe.log_error(
					title=f"Peer feedback assignment failed: {feedback.name}",
					message=frappe.get_traceback(),
				)
		created.append(feedback.name)
	return created

