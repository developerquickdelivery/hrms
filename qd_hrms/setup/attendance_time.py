"""Attendance Period, overtime approval, biometric layers, and dashboard setup."""

from __future__ import annotations

import json

import frappe

OVERTIME_WORKFLOW = "QD Overtime Approval"
ATTENDANCE_WORKSPACE = "Attendance Dashboard"


def run():
	migrate_legacy_period_locks()
	ensure_overtime_workflow()
	ensure_default_connectors()
	ensure_attendance_workspace()
	frappe.clear_cache()
	return {
		"attendance_period": "Attendance Period",
		"overtime_workflow": OVERTIME_WORKFLOW,
		"workspace": ATTENDANCE_WORKSPACE,
		"biometric_layers": [
			"QD Biometric Device",
			"QD Biometric Connector",
			"QD Raw Checkin",
			"QD Biometric Employee Mapping",
			"Employee Checkin",
			"Attendance",
		],
	}


def migrate_legacy_period_locks():
	old_dt = "QD Attendance Period Lock"
	if not frappe.db.exists("DocType", old_dt):
		return

	rows = frappe.get_all(
		old_dt,
		fields=[
			"name",
			"company",
			"from_date",
			"to_date",
			"remarks",
			"locked_by",
			"locked_on",
			"docstatus",
		],
	)
	for row in rows:
		if frappe.db.exists("Attendance Period", row.name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Attendance Period",
				"period": row.name,
				"company": row.company,
				"start_date": row.from_date,
				"end_date": row.to_date,
				"remarks": row.remarks,
			}
		).insert(ignore_permissions=True)
		if row.docstatus in (1, 2):
			doc.submit()
			frappe.db.set_value(
				"Attendance Period",
				doc.name,
				{
					"locked_by": row.locked_by,
					"locked_date": row.locked_on,
				},
				update_modified=False,
			)
		if row.docstatus == 2:
			doc.db_set("reopening_reason", "Migrated from cancelled legacy period lock.")
			doc.cancel()

	# The replacement source no longer ships this DocType. Remove the legacy
	# schema only after all rows have been copied.
	frappe.delete_doc("DocType", old_dt, force=1, ignore_permissions=True)


def ensure_overtime_workflow():
	for state, style in (
		("Draft", "Inverse"),
		("Pending Approval", "Warning"),
		("Approved", "Success"),
		("Rejected", "Danger"),
		("Withdrawn", "Inverse"),
		("Cancelled", "Inverse"),
	):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)

	for action in ("Submit for Approval", "Approve", "Reject", "Reopen", "Withdraw", "Cancel"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)

	if frappe.db.exists("Workflow", OVERTIME_WORKFLOW):
		doc = frappe.get_doc("Workflow", OVERTIME_WORKFLOW)
		doc.set("states", [])
		doc.set("transitions", [])
	else:
		doc = frappe.new_doc("Workflow")
		doc.workflow_name = OVERTIME_WORKFLOW

	doc.document_type = "Overtime Request"
	doc.is_active = 1
	doc.send_email_alert = 0
	doc.workflow_state_field = "approval_status"
	if doc.meta.has_field("override_status"):
		doc.override_status = 0

	for state, docstatus, style, allow_edit, value in (
		("Draft", "0", "Inverse", "Employee", "Draft"),
		("Pending Approval", "0", "Warning", "Leave Approver", "Pending Approval"),
		("Approved", "1", "Success", "HR User", "Approved"),
		("Rejected", "0", "Danger", "Employee", "Rejected"),
		("Withdrawn", "0", "Inverse", "Employee", "Withdrawn"),
		("Cancelled", "2", "Inverse", "HR User", "Cancelled"),
	):
		doc.append(
			"states",
			{
				"state": state,
				"doc_status": docstatus,
				"style": style,
				"allow_edit": allow_edit,
				"update_field": "approval_status",
				"update_value": value,
			},
		)

	def transition(state, action, next_state, role, allow_self=0):
		if frappe.db.exists("Role", role):
			doc.append(
				"transitions",
				{
					"state": state,
					"action": action,
					"next_state": next_state,
					"allowed": role,
					"allow_self_approval": allow_self,
				},
			)

	for role in ("Employee", "Employee Self Service", "HR User", "HR Manager", "System Manager"):
		transition("Draft", "Submit for Approval", "Pending Approval", role, 1)
	for role in ("Leave Approver", "HR User", "HR Manager", "System Manager"):
		transition("Pending Approval", "Approve", "Approved", role)
		transition("Pending Approval", "Reject", "Rejected", role)
		transition("Rejected", "Reopen", "Pending Approval", role)
		transition("Approved", "Cancel", "Cancelled", role)
	for role in ("Employee", "Employee Self Service", "HR User", "HR Manager", "System Manager"):
		transition("Draft", "Withdraw", "Withdrawn", role, 1)
		transition("Pending Approval", "Withdraw", "Withdrawn", role, 1)

	doc.save(ignore_permissions=True)


def ensure_default_connectors():
	connectors = (
		("QD Bench Scheduler", "Bench Scheduler"),
		("QD On-Prem Listener", "On-Prem Listener"),
	)
	for name, connector_type in connectors:
		if not frappe.db.exists("QD Biometric Connector", name):
			frappe.get_doc(
				{
					"doctype": "QD Biometric Connector",
					"connector_name": name,
					"connector_type": connector_type,
					"status": "Active",
				}
			).insert(ignore_permissions=True)

	for device in frappe.get_all(
		"QD Biometric Device",
		filters={"connector": ["is", "not set"]},
		fields=["name", "poll_via_scheduler"],
	):
		frappe.db.set_value(
			"QD Biometric Device",
			device.name,
			"connector",
			"QD Bench Scheduler" if device.poll_via_scheduler else "QD On-Prem Listener",
		)


def ensure_attendance_workspace():
	shortcuts = (
		("Attendance", "Attendance", "Blue"),
		("Employee Check-ins", "Employee Checkin", "Blue"),
		("Shifts", "Shift Type", "Grey"),
		("Shift Assignments", "Shift Assignment", "Grey"),
		("Timesheets", "Timesheet", "Grey"),
		("Attendance Corrections", "Attendance Request", "Orange"),
		("Overtime Requests", "Overtime Request", "Orange"),
		("Attendance Periods", "Attendance Period", "Orange"),
	)
	biometric = (
		"QD Biometric Device",
		"QD Biometric Connector",
		"QD Biometric Employee Mapping",
		"QD Raw Checkin",
		"QD Biometric Sync Log",
	)
	shortcuts = tuple(row for row in shortcuts if frappe.db.exists("DocType", row[1]))
	biometric = tuple(dt for dt in biometric if frappe.db.exists("DocType", dt))

	if frappe.db.exists("Workspace", ATTENDANCE_WORKSPACE):
		doc = frappe.get_doc("Workspace", ATTENDANCE_WORKSPACE)
		doc.shortcuts = []
		doc.links = []
		doc.roles = []
	else:
		doc = frappe.new_doc("Workspace")
		doc.label = ATTENDANCE_WORKSPACE

	doc.title = ATTENDANCE_WORKSPACE
	doc.module = "QD HRMS"
	doc.icon = "calendar"
	doc.public = 1
	doc.is_hidden = 0
	doc.hide_custom = 0
	for role in ("HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	content = [
		_block("header", {"text": '<span class="h4"><b>Attendance and Time</b></span>', "col": 12})
	]
	for label, dt, color in shortcuts:
		doc.append(
			"shortcuts",
			{
				"type": "DocType",
				"link_to": dt,
				"doc_view": "List",
				"label": label,
				"color": color,
			},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))

	if biometric:
		doc.append(
			"links",
			{
				"type": "Card Break",
				"label": "Biometric Integration",
				"hidden": 0,
				"link_count": len(biometric),
			},
		)
		for dt in biometric:
			doc.append(
				"links",
				{
					"type": "Link",
					"link_type": "DocType",
					"link_to": dt,
					"label": dt,
					"hidden": 0,
					"is_query_report": 0,
					"onboard": 0,
				},
			)
		content.extend(
			[
				_block("spacer", {"col": 12}),
				_block(
					"header",
					{"text": '<span class="h4"><b>Biometric Integration</b></span>', "col": 12},
				),
				_block("card", {"card_name": "Biometric Integration", "col": 6}),
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


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {
		"Attendance Period",
		"Overtime Request",
		"QD Biometric Connector",
		"QD Biometric Employee Mapping",
		"QD Raw Checkin",
	}
	missing = [doctype for doctype in required if not frappe.db.exists("DocType", doctype)]
	if missing:
		raise frappe.ValidationError(f"Missing DocTypes: {', '.join(missing)}")
	if frappe.db.exists("DocType", "QD Attendance Period Lock"):
		raise frappe.ValidationError("Legacy QD Attendance Period Lock was not removed")
	if frappe.db.get_value("Workflow", OVERTIME_WORKFLOW, "is_active") != 1:
		raise frappe.ValidationError("Overtime workflow is not active")
	if not frappe.db.exists("Workspace", ATTENDANCE_WORKSPACE):
		raise frappe.ValidationError("Attendance Dashboard workspace is missing")
	if not frappe.db.exists("Custom Field", "Attendance Request-custom_qd_requested_status"):
		raise frappe.ValidationError("Attendance Correction requested status is missing")

	lock_enforced = "skipped-no-company"
	company = frappe.db.get_value("Company", {}, "name")
	if company:
		from frappe.utils import add_days, nowdate, now_datetime

		from qd_hrms.attendance.period_lock import assert_period_open

		start = add_days(nowdate(), 3650)
		end = add_days(start, 6)
		period = frappe.get_doc(
			{
				"doctype": "Attendance Period",
				"period": f"VERIFY-{now_datetime()}",
				"company": company,
				"start_date": start,
				"end_date": end,
			}
		).insert(ignore_permissions=True)
		period.submit()
		try:
			assert_period_open(company, start, "verification")
			raise frappe.ValidationError("Period lock did not block")
		except frappe.ValidationError as exc:
			if "Period lock did not block" in str(exc):
				raise
			lock_enforced = True
		finally:
			frappe.db.rollback()

	return {
		"doctypes": sorted(required),
		"legacy_removed": True,
		"overtime_workflow": "active",
		"workspace": ATTENDANCE_WORKSPACE,
		"period_lock_enforced": lock_enforced,
	}
