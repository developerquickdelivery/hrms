"""Configure QD performance customizations on top of HRMS Appraisal / Goal."""

from __future__ import annotations

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

APPRAISAL_WORKFLOW = "QD Appraisal Review"
PIP_WORKFLOW = "QD PIP Approval"
RECOGNITION_WORKFLOW = "QD Recognition Approval"
CALIBRATION_WORKFLOW = "QD Calibration Approval"
DEFAULT_SCALE = "QD 5-Point Scale"
WORKSPACE = "Performance Hub"


def run():
	ensure_custom_fields()
	ensure_default_rating_scale()
	ensure_seed_kras_and_criteria()
	ensure_energy_points_recognition()
	ensure_cycle_score_formula()
	ensure_workflows()
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


def ensure_custom_fields():
	create_custom_fields(_fields(), ignore_validate=True, update=True)


def _fields():
	return {
		"User": [
			{
				"fieldname": "custom_qd_recognition_section",
				"fieldtype": "Section Break",
				"label": "Recognition",
				"insert_after": "roles",
				"collapsible": 1,
			},
			{
				"fieldname": "custom_qd_recognition_points",
				"fieldtype": "Int",
				"label": "Recognition Points",
				"read_only": 1,
				"insert_after": "custom_qd_recognition_section",
			},
			{
				"fieldname": "custom_qd_recognition_badge",
				"fieldtype": "Select",
				"label": "Recognition Badge",
				"options": "\nBronze\nSilver\nGold\nPlatinum",
				"read_only": 1,
				"insert_after": "custom_qd_recognition_points",
			},
		],
		"Appraisal Cycle": [
			{
				"fieldname": "custom_qd_cycle_section",
				"fieldtype": "Section Break",
				"label": "QD Cycle Settings",
				"insert_after": "final_score_formula",
				"collapsible": 1,
			},
			{
				"fieldname": "custom_qd_rating_scale",
				"fieldtype": "Link",
				"label": "Rating Scale",
				"options": "QD Rating Scale",
				"insert_after": "custom_qd_cycle_section",
			},
			{
				"fieldname": "custom_qd_self_review_due",
				"fieldtype": "Date",
				"label": "Self Review Due",
				"insert_after": "custom_qd_rating_scale",
			},
			{
				"fieldname": "custom_qd_manager_review_due",
				"fieldtype": "Date",
				"label": "Manager Review Due",
				"insert_after": "custom_qd_self_review_due",
			},
			{
				"fieldname": "custom_qd_calibration_due",
				"fieldtype": "Date",
				"label": "Calibration Due",
				"insert_after": "custom_qd_manager_review_due",
			},
			{
				"default": "0",
				"fieldname": "custom_qd_min_peer_feedback",
				"fieldtype": "Int",
				"label": "Minimum Peer / 360 Feedback",
				"description": "Submitted Peer or 360 feedback required before appraisal submit. 0 disables the check.",
				"non_negative": 1,
				"insert_after": "custom_qd_calibration_due",
			},
		],
		"Appraisal Template": [
			{
				"fieldname": "custom_qd_rating_scale",
				"fieldtype": "Link",
				"label": "Rating Scale",
				"options": "QD Rating Scale",
				"insert_after": "description",
			},
			{
				"fieldname": "custom_qd_template_category",
				"fieldtype": "Select",
				"label": "Staff Category",
				"options": "\nRider\nHub Staff\nOffice\nManager\nLeadership",
				"insert_after": "custom_qd_rating_scale",
			},
		],
		"KRA": [
			{
				"fieldname": "custom_qd_objective_code",
				"fieldtype": "Data",
				"label": "Objective Code",
				"insert_after": "title",
			},
			{
				"fieldname": "custom_qd_kpi_unit",
				"fieldtype": "Data",
				"label": "Default KPI Unit",
				"insert_after": "custom_qd_objective_code",
			},
		],
		"Goal": [
			{
				"fieldname": "custom_qd_employee_user",
				"fieldtype": "Link",
				"label": "Employee User",
				"options": "User",
				"fetch_from": "employee.user_id",
				"read_only": 1,
				"hidden": 1,
				"insert_after": "employee",
			},
			{
				"fieldname": "custom_qd_kpi_section",
				"fieldtype": "Section Break",
				"label": "KPI and Delivery Metrics",
				"insert_after": "description",
				"collapsible": 1,
			},
			{
				"fieldname": "custom_qd_kpi_name",
				"fieldtype": "Data",
				"label": "KPI",
				"insert_after": "custom_qd_kpi_section",
			},
			{
				"fieldname": "custom_qd_kpi_target",
				"fieldtype": "Float",
				"label": "KPI Target",
				"insert_after": "custom_qd_kpi_name",
			},
			{
				"fieldname": "custom_qd_kpi_actual",
				"fieldtype": "Float",
				"label": "KPI Actual",
				"insert_after": "custom_qd_kpi_target",
			},
			{
				"fieldname": "custom_qd_kpi_unit",
				"fieldtype": "Data",
				"label": "KPI Unit",
				"insert_after": "custom_qd_kpi_actual",
			},
			{
				"fieldname": "custom_qd_metric_sources",
				"fieldtype": "Table",
				"label": "Project / Task Metrics",
				"options": "QD Goal Metric Source",
				"insert_after": "custom_qd_kpi_unit",
			},
		],
		"Appraisal": [
			{
				"fieldname": "custom_qd_employee_user",
				"fieldtype": "Link",
				"label": "Employee User",
				"options": "User",
				"fetch_from": "employee.user_id",
				"read_only": 1,
				"hidden": 1,
				"insert_after": "employee",
			},
			{
				"fieldname": "custom_qd_review_status",
				"fieldtype": "Select",
				"label": "Review Status",
				"options": "Draft\nSelf Review\nManager Review\nSecond-Level Review\nCalibrated\nCompleted\nCancelled",
				"default": "Draft",
				"read_only": 1,
				"insert_after": "final_score",
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "custom_qd_manager_reviewer",
				"fieldtype": "Link",
				"label": "Manager Reviewer",
				"options": "User",
				"read_only": 1,
				"insert_after": "custom_qd_review_status",
			},
			{
				"fieldname": "custom_qd_second_level_reviewer",
				"fieldtype": "Link",
				"label": "Second-Level Reviewer",
				"options": "User",
				"read_only": 1,
				"insert_after": "custom_qd_manager_reviewer",
			},
			{
				"fieldname": "custom_qd_manager_score",
				"fieldtype": "Float",
				"label": "Manager Score",
				"precision": "2",
				"insert_after": "custom_qd_second_level_reviewer",
			},
			{
				"fieldname": "custom_qd_second_level_score",
				"fieldtype": "Float",
				"label": "Second-Level Score",
				"precision": "2",
				"insert_after": "custom_qd_manager_score",
			},
			{
				"fieldname": "custom_qd_potential_score",
				"fieldtype": "Float",
				"label": "Potential Score",
				"description": "Leadership potential, learning agility, and readiness on the active rating scale.",
				"precision": "2",
				"insert_after": "custom_qd_second_level_score",
			},
			{
				"fieldname": "custom_qd_calibrated_score",
				"fieldtype": "Float",
				"label": "Calibrated Score",
				"precision": "2",
				"read_only": 1,
				"insert_after": "custom_qd_potential_score",
			},
			{
				"fieldname": "custom_qd_rating_band",
				"fieldtype": "Data",
				"label": "Rating Band",
				"insert_after": "custom_qd_calibrated_score",
			},
			{
				"fieldname": "custom_qd_nine_box_placement",
				"fieldtype": "Data",
				"label": "Nine-Box Placement",
				"read_only": 1,
				"insert_after": "custom_qd_rating_band",
			},
			{
				"fieldname": "custom_qd_calibration",
				"fieldtype": "Link",
				"label": "Calibration",
				"options": "QD Performance Calibration",
				"read_only": 1,
				"insert_after": "custom_qd_nine_box_placement",
			},
			{
				"default": "0",
				"fieldname": "custom_qd_pip_required",
				"fieldtype": "Check",
				"label": "PIP Required",
				"insert_after": "custom_qd_calibration",
			},
			{
				"fieldname": "custom_qd_pip",
				"fieldtype": "Link",
				"label": "PIP",
				"options": "QD Performance Improvement Plan",
				"read_only": 1,
				"insert_after": "custom_qd_pip_required",
			},
			{
				"fieldname": "custom_qd_delivery_kpi_notes",
				"fieldtype": "Small Text",
				"label": "Delivery KPI Notes",
				"insert_after": "remarks",
			},
		],
		"Employee Performance Feedback": [
			{
				"fieldname": "custom_qd_employee_user",
				"fieldtype": "Link",
				"label": "Employee User",
				"options": "User",
				"fetch_from": "employee.user_id",
				"read_only": 1,
				"hidden": 1,
				"insert_after": "employee",
			},
			{
				"default": "Peer",
				"fieldname": "custom_qd_feedback_scope",
				"fieldtype": "Select",
				"label": "Feedback Scope",
				"options": "Peer\n360\nManager\nSkip-Level\nCustomer",
				"insert_after": "reviewer",
				"in_standard_filter": 1,
			}
		],
		"Project": [
			{
				"fieldname": "custom_qd_performance_section",
				"fieldtype": "Section Break",
				"label": "Performance Link",
				"insert_after": "department",
				"collapsible": 1,
			},
			{
				"default": "0",
				"fieldname": "custom_qd_counts_for_performance",
				"fieldtype": "Check",
				"label": "Counts for Performance",
				"insert_after": "custom_qd_performance_section",
			},
		],
		"Task": [
			{
				"default": "0",
				"fieldname": "custom_qd_counts_for_performance",
				"fieldtype": "Check",
				"label": "Counts for Performance",
				"insert_after": "priority",
			}
		],
	}


def ensure_default_rating_scale():
	if frappe.db.exists("QD Rating Scale", DEFAULT_SCALE):
		return
	frappe.get_doc(
		{
			"doctype": "QD Rating Scale",
			"scale_name": DEFAULT_SCALE,
			"min_score": 1,
			"max_score": 5,
			"is_default": 1,
			"description": "Standard 5-point performance scale.",
			"levels": [
				{"score": 1, "label": "Unsatisfactory", "description": "Consistently below expectations"},
				{"score": 2, "label": "Needs Improvement", "description": "Partially meets expectations"},
				{"score": 3, "label": "Meets Expectations", "description": "Solid, reliable performance"},
				{"score": 4, "label": "Exceeds Expectations", "description": "Frequently above expectations"},
				{"score": 5, "label": "Outstanding", "description": "Exceptional contribution"},
			],
		}
	).insert(ignore_permissions=True)


def ensure_seed_kras_and_criteria():
	for title, code, unit in (
		("Delivery Reliability", "OBJ-DEL", "% on-time"),
		("Customer Experience", "OBJ-CX", "CSAT"),
		("Safety and Compliance", "OBJ-SAFE", "incidents"),
		("Team Collaboration", "OBJ-TEAM", "score"),
		("Operational Efficiency", "OBJ-OPS", "% complete"),
	):
		if not frappe.db.exists("KRA", title):
			doc = frappe.get_doc({"doctype": "KRA", "title": title, "description": title})
			if doc.meta.has_field("custom_qd_objective_code"):
				doc.custom_qd_objective_code = code
			if doc.meta.has_field("custom_qd_kpi_unit"):
				doc.custom_qd_kpi_unit = unit
			doc.insert(ignore_permissions=True)
		else:
			frappe.db.set_value(
				"KRA",
				title,
				{"custom_qd_objective_code": code, "custom_qd_kpi_unit": unit},
				update_modified=False,
			)

	for criteria in (
		"Quality of Work",
		"Ownership",
		"Communication",
		"Teamwork",
		"Customer Focus",
	):
		if not frappe.db.exists("Employee Feedback Criteria", criteria):
			frappe.get_doc({"doctype": "Employee Feedback Criteria", "criteria": criteria}).insert(
				ignore_permissions=True
			)


def ensure_energy_points_recognition():
	"""Configure native Energy Points and retire the custom award workflow."""
	if not frappe.db.exists("DocType", "Energy Point Rule"):
		return
	settings = frappe.get_single("Energy Point Settings")
	settings.enabled = 1
	settings.save(ignore_permissions=True)

	for values in (
		{
			"rule_name": "QD Completed Appraisal",
			"reference_doctype": "Appraisal",
			"for_doc_event": "Submit",
			"user_field": "custom_qd_employee_user",
			"points": 100,
			"apply_only_once": 1,
		},
		{
			"rule_name": "QD Completed Goal",
			"reference_doctype": "Goal",
			"for_doc_event": "Value Change",
			"field_to_check": "status",
			"condition": "doc.status == 'Completed'",
			"user_field": "custom_qd_employee_user",
			"points": 25,
			"apply_only_once": 1,
		},
		{
			"rule_name": "QD Peer Feedback Received",
			"reference_doctype": "Employee Performance Feedback",
			"for_doc_event": "Submit",
			"user_field": "custom_qd_employee_user",
			"points": 15,
			"apply_only_once": 0,
		},
	):
		doc = (
			frappe.get_doc("Energy Point Rule", values["rule_name"])
			if frappe.db.exists("Energy Point Rule", values["rule_name"])
			else frappe.new_doc("Energy Point Rule")
		)
		doc.update(values)
		doc.enabled = 1
		doc.save(ignore_permissions=True)

	if frappe.db.exists("Workflow", RECOGNITION_WORKFLOW):
		frappe.db.set_value("Workflow", RECOGNITION_WORKFLOW, "is_active", 0)


def ensure_cycle_score_formula():
	"""Include manager and second-level scores in native Appraisal Cycle formulas."""
	formula = (
		"(goal_score + average_feedback_score + self_appraisal_score + "
		"custom_qd_manager_score + custom_qd_second_level_score) / 5"
	)
	if not frappe.db.exists("DocType", "Appraisal Cycle"):
		return
	for name in frappe.get_all("Appraisal Cycle", pluck="name"):
		doc = frappe.get_doc("Appraisal Cycle", name)
		if not doc.calculate_final_score_based_on_formula or not doc.final_score_formula:
			doc.calculate_final_score_based_on_formula = 1
			doc.final_score_formula = formula
			if doc.meta.has_field("custom_qd_rating_scale") and not doc.custom_qd_rating_scale:
				doc.custom_qd_rating_scale = DEFAULT_SCALE if frappe.db.exists("QD Rating Scale", DEFAULT_SCALE) else None
			if doc.meta.has_field("custom_qd_min_peer_feedback") and doc.custom_qd_min_peer_feedback in (None, ""):
				doc.custom_qd_min_peer_feedback = 0
			doc.save(ignore_permissions=True)


def ensure_workflows():
	_ensure_appraisal_workflow()
	_ensure_simple_workflow(
		PIP_WORKFLOW,
		"QD Performance Improvement Plan",
		"approval_status",
		[
			("Draft", "0", "Inverse", "HR User"),
			("Pending Acknowledgement", "0", "Warning", "Employee"),
			("Active", "1", "Success", "HR User"),
			("Successful", "1", "Success", "HR Manager"),
			("Extended", "1", "Warning", "HR Manager"),
			("Unsuccessful", "1", "Danger", "HR Manager"),
			("Withdrawn", "0", "Inverse", "HR Manager"),
			("Cancelled", "2", "Inverse", "HR Manager"),
		],
		[
			(("Draft", "Submit for Acknowledgement", "Pending Acknowledgement"), ("HR User", "HR Manager", "System Manager")),
			(("Pending Acknowledgement", "Acknowledge", "Active"), ("Employee", "Employee Self Service")),
			(("Active", "Mark Successful", "Successful"), ("HR User", "HR Manager", "System Manager")),
			(("Active", "Extend", "Extended"), ("HR Manager", "System Manager")),
			(("Active", "Mark Unsuccessful", "Unsuccessful"), ("HR Manager", "System Manager")),
			(("Draft", "Withdraw", "Withdrawn"), ("HR User", "HR Manager", "System Manager")),
			(("Pending Acknowledgement", "Withdraw", "Withdrawn"), ("HR User", "HR Manager", "System Manager")),
			(("Active", "Cancel", "Cancelled"), ("HR Manager", "System Manager")),
		],
		extra_actions=("Submit for Acknowledgement", "Acknowledge", "Mark Successful", "Extend", "Mark Unsuccessful"),
	)
	_ensure_simple_workflow(
		CALIBRATION_WORKFLOW,
		"QD Performance Calibration",
		"approval_status",
		[
			("Draft", "0", "Inverse", "HR User"),
			("In Progress", "0", "Warning", "HR Manager"),
			("Completed", "1", "Success", "HR Manager"),
			("Cancelled", "0", "Inverse", "HR Manager"),
		],
		[
			(("Draft", "Start Calibration", "In Progress"), ("HR User", "HR Manager", "System Manager")),
			(("In Progress", "Complete", "Completed"), ("HR Manager", "System Manager")),
			(("Draft", "Cancel", "Cancelled"), ("HR Manager", "System Manager")),
			(("In Progress", "Cancel", "Cancelled"), ("HR Manager", "System Manager")),
		],
		extra_actions=("Start Calibration", "Complete"),
	)


def _ensure_appraisal_workflow():
	_ensure_states_actions(
		states=(
			("Draft", "Inverse"),
			("Self Review", "Warning"),
			("Manager Review", "Warning"),
			("Second-Level Review", "Warning"),
			("Calibrated", "Primary"),
			("Completed", "Success"),
			("Cancelled", "Inverse"),
		),
		actions=(
			"Start Self Review",
			"Submit Self Review",
			"Manager Approve Review",
			"Second-Level Approve",
			"Mark Calibrated",
			"Complete Review",
			"Cancel",
		),
	)
	doc = (
		frappe.get_doc("Workflow", APPRAISAL_WORKFLOW)
		if frappe.db.exists("Workflow", APPRAISAL_WORKFLOW)
		else frappe.new_doc("Workflow")
	)
	if doc.is_new():
		doc.workflow_name = APPRAISAL_WORKFLOW
	doc.document_type = "Appraisal"
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = "custom_qd_review_status"
	doc.set("states", [])
	doc.set("transitions", [])
	for state, docstatus, style, allow_edit in (
		("Draft", "0", "Inverse", "Employee"),
		("Self Review", "0", "Warning", "Employee"),
		("Manager Review", "0", "Warning", "Employee"),
		("Second-Level Review", "0", "Warning", "Employee"),
		("Calibrated", "0", "Primary", "HR Manager"),
		("Completed", "1", "Success", "HR Manager"),
		("Cancelled", "0", "Inverse", "HR Manager"),
	):
		doc.append(
			"states",
			{
				"state": state,
				"doc_status": docstatus,
				"style": style,
				"allow_edit": allow_edit,
				"update_field": "custom_qd_review_status",
				"update_value": state,
			},
		)

	def transition(state, action, next_state, role, condition=None, allow_self=0):
		if frappe.db.exists("Role", role):
			doc.append(
				"transitions",
				{
					"state": state,
					"action": action,
					"next_state": next_state,
					"allowed": role,
					"condition": condition or "",
					"allow_self_approval": allow_self,
				},
			)

	for role in ("Employee", "Employee Self Service", "HR User", "HR Manager", "System Manager"):
		transition("Draft", "Start Self Review", "Self Review", role, allow_self=1)
		transition("Self Review", "Submit Self Review", "Manager Review", role, allow_self=1)
	transition(
		"Manager Review",
		"Manager Approve Review",
		"Second-Level Review",
		"Employee",
		"doc.custom_qd_manager_reviewer == frappe.session.user",
	)
	for role in ("HR User", "HR Manager", "System Manager"):
		transition("Manager Review", "Manager Approve Review", "Second-Level Review", role)
		transition("Second-Level Review", "Second-Level Approve", "Calibrated", role)
		transition("Calibrated", "Complete Review", "Completed", role)
		transition("Draft", "Cancel", "Cancelled", role)
		transition("Self Review", "Cancel", "Cancelled", role)
	transition(
		"Second-Level Review",
		"Second-Level Approve",
		"Calibrated",
		"Employee",
		"doc.custom_qd_second_level_reviewer == frappe.session.user",
	)
	doc.save(ignore_permissions=True)


def _ensure_simple_workflow(name, doctype, state_field, states, transitions, extra_actions=()):
	base_actions = ("Submit for Approval", "Approve", "Reject", "Withdraw", "Cancel")
	_ensure_states_actions(
		states=[(s[0], s[2]) for s in states],
		actions=base_actions + tuple(extra_actions),
	)
	doc = frappe.get_doc("Workflow", name) if frappe.db.exists("Workflow", name) else frappe.new_doc("Workflow")
	if doc.is_new():
		doc.workflow_name = name
	doc.document_type = doctype
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = state_field
	doc.set("states", [])
	doc.set("transitions", [])
	for state, docstatus, style, allow_edit in states:
		doc.append(
			"states",
			{
				"state": state,
				"doc_status": docstatus,
				"style": style,
				"allow_edit": allow_edit,
				"update_field": state_field,
				"update_value": state,
			},
		)
	for (state, action, next_state), roles in transitions:
		for role in roles:
			if frappe.db.exists("Role", role):
				doc.append(
					"transitions",
					{
						"state": state,
						"action": action,
						"next_state": next_state,
						"allowed": role,
						"allow_self_approval": 1 if role in ("Employee", "Employee Self Service") else 0,
					},
				)
	doc.save(ignore_permissions=True)


def _ensure_states_actions(states, actions):
	for state, style in states:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)
	for action in actions:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)


def ensure_workspace():
	if frappe.db.exists("Workspace", WORKSPACE):
		doc = frappe.get_doc("Workspace", WORKSPACE)
		doc.shortcuts = []
		doc.links = []
		doc.roles = []
	else:
		doc = frappe.new_doc("Workspace")
		doc.label = WORKSPACE
	doc.title = WORKSPACE
	doc.module = "QD HRMS"
	doc.icon = "hr"
	doc.public = 1
	doc.is_hidden = 0
	for role in ("HR User", "HR Manager", "Employee", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	content = [_block("header", {"text": '<span class="h4"><b>Performance Management</b></span>', "col": 12})]
	shortcuts = (
		("Appraisal Cycles", "Appraisal Cycle", "List", "Blue"),
		("Templates", "Appraisal Template", "List", "Grey"),
		("Goals / KPIs", "Goal", "List", "Blue"),
		("Appraisals", "Appraisal", "List", "Blue"),
		("360 / Peer Feedback", "Employee Performance Feedback", "List", "Orange"),
		("Calibration", "QD Performance Calibration", "List", "Orange"),
		("PIP", "QD Performance Improvement Plan", "List", "Orange"),
		("Recognition Points", "Energy Point Log", "List", "Green"),
		("Recognition Rules", "Energy Point Rule", "List", "Green"),
		("Rating Scale", "QD Rating Scale", "List", "Grey"),
	)
	for label, target, view, color in shortcuts:
		if not frappe.db.exists("DocType", target):
			continue
		doc.append(
			"shortcuts",
			{"type": "DocType", "link_to": target, "doc_view": view, "label": label, "color": color},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))

	doc.append(
		"shortcuts",
		{
			"type": "Page",
			"link_to": "qd-nine-box-grid",
			"label": "Executive Nine-Box Grid",
			"color": "Purple",
		},
	)
	content.append(_block("shortcut", {"shortcut_name": "Executive Nine-Box Grid", "col": 3}))

	doc.append("links", {"type": "Card Break", "label": "Reports", "link_count": 1})
	if frappe.db.exists("Report", "Appraisal Overview"):
		doc.append(
			"links",
			{
				"type": "Link",
				"link_type": "Report",
				"link_to": "Appraisal Overview",
				"label": "Appraisal Overview",
				"is_query_report": 1,
			},
		)
		content.extend(
			[
				_block("spacer", {"col": 12}),
				_block("header", {"text": '<span class="h4"><b>Reports</b></span>', "col": 12}),
				_block("card", {"card_name": "Reports", "col": 4}),
			]
		)
	doc.content = json.dumps(content)
	doc.flags.ignore_links = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def extend_ess():
	"""Ensure ESS can participate in native reviews, goals, and feedback."""
	if not frappe.db.exists("User Type", "Employee Self Service"):
		return
	from hrms.setup import append_docperms_to_user_type

	doc = frappe.get_doc("User Type", "Employee Self Service")
	docperms = {
		dt: perms
		for dt, perms in {
			"Appraisal": ["read", "write"],
			"Goal": ["read", "write", "create"],
			"Employee Performance Feedback": ["read", "write", "create", "submit"],
			"Energy Point Log": ["read"],
			"QD Performance Improvement Plan": ["read"],
			"KRA": ["read"],
			"Appraisal Cycle": ["read"],
			"Appraisal Template": ["read"],
		}.items()
		if frappe.db.exists("DocType", dt)
	}
	append_docperms_to_user_type(docperms, doc)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {
		"QD Rating Scale",
		"QD Performance Improvement Plan",
		"QD Performance Calibration",
		"QD Goal Metric Source",
	}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing DocTypes: {', '.join(missing)}")
	for workflow in (APPRAISAL_WORKFLOW, PIP_WORKFLOW, CALIBRATION_WORKFLOW):
		if frappe.db.get_value("Workflow", workflow, "is_active") != 1:
			raise frappe.ValidationError(f"Inactive workflow: {workflow}")
	if not frappe.db.exists("QD Rating Scale", DEFAULT_SCALE):
		raise frappe.ValidationError("Default rating scale missing")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Performance Hub workspace missing")
	if not frappe.db.exists("Custom Field", "Goal-custom_qd_metric_sources"):
		raise frappe.ValidationError("Goal metric sources field missing")
	for rule in ("QD Completed Appraisal", "QD Completed Goal", "QD Peer Feedback Received"):
		if not frappe.db.exists("Energy Point Rule", rule):
			raise frappe.ValidationError(f"Missing recognition rule: {rule}")
	if not frappe.db.get_single_value("Energy Point Settings", "enabled"):
		raise frappe.ValidationError("Energy Points recognition is not enabled")
	for fieldname in ("custom_qd_recognition_points", "custom_qd_recognition_badge"):
		if not frappe.db.exists("Custom Field", f"User-{fieldname}"):
			raise frappe.ValidationError(f"Missing recognition badge field: {fieldname}")
	if not frappe.db.exists("Page", "qd-nine-box-grid"):
		raise frappe.ValidationError("Executive Nine-Box Grid page missing")
	return {
		"kept": [
			"Appraisal Cycle",
			"Appraisal Template",
			"KRA",
			"Goal",
			"Appraisal",
			"Employee Performance Feedback",
		],
		"created": sorted(required),
		"workflows": [
			APPRAISAL_WORKFLOW,
			PIP_WORKFLOW,
			CALIBRATION_WORKFLOW,
		],
		"workspace": WORKSPACE,
		"recognition": "Energy Points with Bronze / Silver / Gold / Platinum badges",
		"nine_box_page": "qd-nine-box-grid",
		"verified": True,
	}
