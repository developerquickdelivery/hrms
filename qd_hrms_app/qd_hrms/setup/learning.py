"""Dedicated Training Management on top of standard HRMS training records."""

from __future__ import annotations

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

WORKFLOW = "QD Training Request Approval"
WORKSPACE = "Learning and Development"


def run():
	ensure_custom_fields()
	ensure_courses_and_programs()
	ensure_workflow()
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


def ensure_custom_fields():
	create_custom_fields(
		{
			"Training Program": [
				{"fieldname":"custom_qd_category","fieldtype":"Select","label":"Category","options":"Induction\nSafety\nCompliance\nOperations\nCustomer Service\nLeadership\nTechnical\nOther","insert_after":"status"},
				{"fieldname":"custom_qd_primary_course","fieldtype":"Link","label":"Primary Course","options":"QD Training Course","insert_after":"custom_qd_category"},
				{"fieldname":"custom_qd_target_staff","fieldtype":"Select","label":"Target Staff","options":"All Employees\nRiders\nHub Staff\nOffice\nManagers\nLeadership","insert_after":"custom_qd_primary_course"},
				{"default":"0","fieldname":"custom_qd_mandatory","fieldtype":"Check","label":"Mandatory","insert_after":"custom_qd_target_staff"},
			],
			"Training Event": [
				{"fieldname":"custom_qd_course","fieldtype":"Link","label":"Course","options":"QD Training Course","insert_after":"course","in_standard_filter":1},
				{"fieldname":"custom_qd_capacity","fieldtype":"Int","label":"Capacity","insert_after":"custom_qd_course"},
				{"default":"0","fieldname":"custom_qd_mandatory","fieldtype":"Check","label":"Mandatory Session","insert_after":"custom_qd_capacity"},
				{"fieldname":"custom_qd_hub","fieldtype":"Link","label":"Hub / Department","options":"Department","insert_after":"location"},
			],
			"Training Feedback": [
				{"fieldname":"custom_qd_enrollment","fieldtype":"Link","label":"Enrollment","options":"QD Training Enrollment","insert_after":"training_event"},
				{"fieldname":"custom_qd_course","fieldtype":"Link","label":"Course","options":"QD Training Course","fetch_from":"training_event.custom_qd_course","read_only":1,"insert_after":"custom_qd_enrollment"},
				{"fieldname":"custom_qd_rating","fieldtype":"Rating","label":"Overall Rating","insert_after":"feedback"},
				{"fieldname":"custom_qd_relevance_rating","fieldtype":"Rating","label":"Relevance Rating","insert_after":"custom_qd_rating"},
				{"fieldname":"custom_qd_trainer_rating","fieldtype":"Rating","label":"Trainer Rating","insert_after":"custom_qd_relevance_rating"},
			],
			"Training Result": [
				{"fieldname":"custom_qd_assessment","fieldtype":"Link","label":"Assessment","options":"QD Training Assessment","insert_after":"training_event"}
			],
		},
		ignore_validate=True,
		update=True,
	)


def ensure_courses_and_programs():
	courses = (
		("Rider Safety Induction", "SAF-IND", "Safety", 8, 1, 365),
		("Customer Service Essentials", "CSE-101", "Customer Service", 6, 0, 0),
		("Hub Operations Basics", "HUB-101", "Operations", 8, 1, 730),
	)
	for name, code, category, hours, cert, validity in courses:
		if not frappe.db.exists("QD Training Course", name):
			frappe.get_doc(
				{
					"doctype": "QD Training Course",
					"course_name": name,
					"course_code": code,
					"category": category,
					"duration_hours": hours,
					"assessment_required": 1,
					"passing_score": 70,
					"certification_required": cert,
					"certificate_validity_days": validity or None,
					"description": f"Quick Delivery standard course: {name}.",
				}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Training Program", name):
			doc = frappe.get_doc(
				{
					"doctype": "Training Program",
					"training_program": name,
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
					"status": "Scheduled",
					"description": f"Quick Delivery standard program: {name}.",
				}
			)
			doc.custom_qd_category = category
			doc.custom_qd_primary_course = name
			doc.custom_qd_target_staff = "All Employees"
			doc.custom_qd_mandatory = 1 if category in ("Safety", "Operations") else 0
			doc.insert(ignore_permissions=True)


def ensure_workflow():
	from qd_hrms.setup.performance import _ensure_simple_workflow

	_ensure_simple_workflow(
		WORKFLOW,
		"QD Training Request",
		"approval_status",
		[
			("Draft", "0", "Inverse", "Employee"),
			("Pending Manager Approval", "0", "Warning", "Employee"),
			("Pending HR Approval", "0", "Warning", "HR User"),
			("Approved", "1", "Success", "HR User"),
			("Rejected", "0", "Danger", "Employee"),
			("Withdrawn", "0", "Inverse", "Employee"),
			("Cancelled", "2", "Inverse", "HR User"),
		],
		[
			(("Draft", "Submit for Approval", "Pending Manager Approval"), ("Employee", "Employee Self Service", "HR User", "HR Manager", "System Manager")),
			(("Pending Manager Approval", "Manager Approve", "Pending HR Approval"), ("Employee", "HR User", "HR Manager", "System Manager")),
			(("Pending Manager Approval", "Reject", "Rejected"), ("Employee", "HR User", "HR Manager", "System Manager")),
			(("Pending HR Approval", "Approve", "Approved"), ("HR User", "HR Manager", "System Manager")),
			(("Pending HR Approval", "Reject", "Rejected"), ("HR User", "HR Manager", "System Manager")),
			(("Draft", "Withdraw", "Withdrawn"), ("Employee", "Employee Self Service", "HR User")),
			(("Pending Manager Approval", "Withdraw", "Withdrawn"), ("Employee", "Employee Self Service", "HR User")),
			(("Approved", "Cancel", "Cancelled"), ("HR Manager", "System Manager")),
		],
		extra_actions=("Manager Approve",),
	)
	workflow = frappe.get_doc("Workflow", WORKFLOW)
	for row in workflow.transitions:
		if row.state == "Pending Manager Approval" and row.allowed == "Employee":
			row.condition = "doc.manager_approver == frappe.session.user"
	workflow.save(ignore_permissions=True)


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
	doc.icon = "education"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("Employee", "HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	content = [_block("header", {"text": '<span class="h4"><b>Learning & Development</b></span>', "col": 12})]
	for label, target, color in (
		("Courses", "QD Training Course", "Blue"),
		("Training Programs", "Training Program", "Blue"),
		("Training Requests", "QD Training Request", "Orange"),
		("Nominations", "QD Training Nomination", "Orange"),
		("Enrollments", "QD Training Enrollment", "Blue"),
		("Training Sessions", "Training Event", "Blue"),
		("Attendance", "QD Training Attendance", "Grey"),
		("Assessments", "QD Training Assessment", "Orange"),
		("Certifications", "QD Training Certification", "Green"),
		("Licenses", "QD Employee License", "Orange"),
		("Training Feedback", "Training Feedback", "Grey"),
	):
		if not frappe.db.exists("DocType", target):
			continue
		doc.append("shortcuts", {"type":"DocType","link_to":target,"doc_view":"List","label":label,"color":color})
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))
	doc.content = json.dumps(content)
	doc.flags.ignore_links = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def extend_ess():
	if not frappe.db.exists("User Type", "Employee Self Service"):
		return
	from hrms.setup import append_docperms_to_user_type

	doc = frappe.get_doc("User Type", "Employee Self Service")
	append_docperms_to_user_type(
		{
			"QD Training Course": ["read"],
			"Training Program": ["read"],
			"Training Event": ["read"],
			"QD Training Request": ["read", "write", "create"],
			"QD Training Nomination": ["read"],
			"QD Training Enrollment": ["read"],
			"QD Training Attendance": ["read"],
			"QD Training Assessment": ["read"],
			"QD Training Certification": ["read"],
			"Training Feedback": ["read", "write", "create", "submit"],
		},
		doc,
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {
		"QD Training Course",
		"QD Training Request",
		"QD Training Nomination",
		"QD Training Enrollment",
		"QD Training Attendance",
		"QD Training Assessment",
		"QD Training Certification",
	}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing Training DocTypes: {', '.join(missing)}")
	if frappe.db.get_value("Workflow", WORKFLOW, "is_active") != 1:
		raise frappe.ValidationError("Training Request workflow is inactive")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Learning workspace missing")
	return {
		"kept": ["Training Program", "Training Event", "Training Result", "Training Feedback"],
		"created": sorted(required),
		"notification_stages": [90, 30, 7, "Expired"],
		"workspace": WORKSPACE,
		"verified": True,
	}
