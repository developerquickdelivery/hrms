"""Sync ERPNext Project / Task progress into linked Goal metrics."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime


def validate_goal_metrics(doc, method=None):
	rows = doc.get("custom_qd_metric_sources") or []
	if not rows:
		return
	total_weight = sum(flt(row.weight) for row in rows if cint(row.active))
	if rows and abs(total_weight - 100) > 0.01 and any(cint(row.active) for row in rows):
		frappe.throw(_("Active Goal metric source weights must total 100%."))
	sync_goal_metrics(doc, save=False)


def sync_goal_metrics(doc, save=True):
	"""Recalculate Goal.progress from explicitly linked Project/Task sources."""
	rows = [row for row in (doc.get("custom_qd_metric_sources") or []) if cint(row.active)]
	if not rows:
		return
	weighted = 0.0
	for row in rows:
		progress, value, error = _calculate_source(row)
		row.calculated_progress = progress
		row.current_value = value
		row.last_synced_on = now_datetime()
		row.sync_error = error
		weighted += flt(progress) * flt(row.weight) / 100.0
	doc.progress = max(0, min(100, weighted))
	if save and not doc.is_new():
		doc.flags.ignore_validate_update_after_submit = True
		doc.save(ignore_permissions=True)


def _calculate_source(row):
	try:
		if row.source_doctype == "Task":
			return _task_metric(row)
		if row.source_doctype == "Project":
			return _project_metric(row)
		return 0, 0, _("Unsupported source type")
	except Exception as exc:
		return 0, 0, str(exc)


def _task_metric(row):
	task = frappe.db.get_value(
		"Task",
		row.source_name,
		["status", "progress", "exp_end_date", "completed_on"],
		as_dict=True,
	)
	if not task:
		frappe.throw(_("Task {0} not found").format(row.source_name))
	status = task.status
	progress = flt(task.progress)
	if row.metric_type == "Completion":
		done = status == "Completed" or (cint(row.include_cancelled) and status == "Cancelled")
		value = 100 if done else 0
		return value, value, None
	if row.metric_type == "On-time Completion":
		if status != "Completed":
			return 0, 0, None
		if task.exp_end_date and task.completed_on and getdate(task.completed_on) > getdate(task.exp_end_date):
			return 0, 0, None
		return 100, 100, None
	# Progress
	if status == "Completed":
		progress = 100
	elif status == "Cancelled" and not cint(row.include_cancelled):
		progress = 0
	return max(0, min(100, progress)), progress, None


def _project_metric(row):
	project = frappe.db.get_value(
		"Project",
		row.source_name,
		["status", "percent_complete", "percent_complete_method"],
		as_dict=True,
	)
	if not project:
		frappe.throw(_("Project {0} not found").format(row.source_name))
	pct = flt(project.percent_complete)
	if row.metric_type in ("Completion", "On-time Completion"):
		done = project.status == "Completed" or (
			cint(row.include_cancelled) and project.status == "Cancelled"
		)
		value = 100 if done else 0
		return value, value, None
	if project.status == "Completed":
		pct = 100
	elif project.status == "Cancelled" and not cint(row.include_cancelled):
		pct = 0
	return max(0, min(100, pct)), pct, None


def on_task_update(doc, method=None):
	_resync_linked_goals("Task", doc.name)


def on_project_update(doc, method=None):
	_resync_linked_goals("Project", doc.name)


def _resync_linked_goals(source_doctype: str, source_name: str):
	if not frappe.db.exists("DocType", "Goal"):
		return
	# Child table lives on Goal via custom field; query parent references.
	parents = frappe.db.sql(
		"""
		select distinct parent
		from `tabQD Goal Metric Source`
		where parenttype = 'Goal'
			and source_doctype = %s
			and source_name = %s
			and ifnull(active, 0) = 1
		""",
		(source_doctype, source_name),
		as_list=True,
	)
	for (goal_name,) in parents:
		goal = frappe.get_doc("Goal", goal_name)
		# Skip goals belonging to completed cycles.
		if goal.appraisal_cycle and frappe.db.get_value(
			"Appraisal Cycle", goal.appraisal_cycle, "status"
		) == "Completed":
			continue
		sync_goal_metrics(goal, save=True)


def reconcile_all_goal_metrics():
	"""Scheduled safety net for missed Project/Task events."""
	goals = frappe.db.sql_list(
		"""
		select distinct parent
		from `tabQD Goal Metric Source`
		where parenttype = 'Goal' and ifnull(active, 0) = 1
		"""
	)
	for goal_name in goals:
		goal = frappe.get_doc("Goal", goal_name)
		if goal.appraisal_cycle and frappe.db.get_value(
			"Appraisal Cycle", goal.appraisal_cycle, "status"
		) == "Completed":
			continue
		sync_goal_metrics(goal, save=True)
